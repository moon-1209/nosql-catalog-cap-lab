from __future__ import annotations

import csv
import json
import shutil
import unicodedata
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from voice import config
from voice.prepare_data import ClipName, SkipError, decode_audio, parse_name, prepare, process_audio, trim_silence
from voice.sync_voices import build_clips, sync
from voice.transcripts import load_script_table, parse_script_table
from voice_testutil import data_dir, script_md, tone, write_tone  # noqa: F401  (fixture)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# --- Kịch bản ---

def test_prepare_real_script_has_all_rows() -> None:
    rows = load_script_table(config.SCRIPT_MD)
    assert len([k for k in rows if k[2] != "C" and k.startswith("A_")]) == 30
    assert len([k for k in rows if k[2] != "C" and k.startswith("B_")]) == 30
    assert len([k for k in rows if "_C" in k]) == 20
    assert rows["A_07"].text == "Phòng khám số 205 đi đường nào?"
    assert rows["A_07"].intent == "hoi_phong"
    assert rows["B_C03"].text == rows["A_C03"].text == "Phòng xét nghiệm máu đi đường nào?"
    assert all(unicodedata.is_normalized("NFC", r.text) for r in rows.values())


def test_prepare_script_ignores_other_tables_and_rejects_duplicates() -> None:
    md = "| Intent | Ý nghĩa |\n| :-- | :-- |\n| hoi_khoa | Hỏi khoa |\n"
    assert parse_script_table(md) == {}
    dup = "| Mã | Câu | Intent |\n|--|--|--|\n| A_01 | x | a |\n| A_01 | y | b |\n"
    with pytest.raises(ValueError):
        parse_script_table(dup)


# --- Tên file ---

@pytest.mark.parametrize("name,expected", [
    ("A_07_r.m4a", ClipName("A", "07", "r")),
    ("B_C03_n.wav", ClipName("B", "C03", "n")),
    ("Nam_C01.m4a", ClipName("A", "C01", "r")),
    ("Nu_C10.wav", ClipName("B", "C10", "r")),
    ("ghi_am_moi.wav", None),
    ("A_7_r.wav", None),
    ("C_01_r.wav", None),
    ("A_07_x.wav", None),
    ("A_07_r.mp3", None),
    ("A_C1_r.wav", None),
])
def test_prepare_parse_name(name: str, expected: ClipName | None) -> None:
    assert parse_name(name) == expected


def test_prepare_clip_id() -> None:
    assert ClipName("B", "C03", "n").clip_id == "B_C03_n"
    assert ClipName("A", "07", "r").key == "A_07"


# --- Xử lý audio ---

def test_prepare_decode_resamples(tmp_path: Path) -> None:
    p = write_tone(tmp_path / "x.wav", seconds=1.0, lead_s=0.0, sr=44100, channels=2)
    audio = decode_audio(p)
    assert audio.dtype == np.float32 and audio.ndim == 1
    assert abs(audio.size - config.SAMPLE_RATE) <= 2


def test_prepare_trim_keeps_200ms() -> None:
    sr = config.SAMPLE_RATE
    x = tone(1.0, sr=sr, lead_s=1.0, channels=1)
    out = trim_silence(x, sr)
    assert out.size / sr == pytest.approx(1.4, abs=0.06)


def test_prepare_trim_all_silence_is_empty() -> None:
    assert trim_silence(np.zeros(16000, dtype=np.float32), 16000).size == 0


def test_prepare_too_short_and_empty_are_skipped() -> None:
    with pytest.raises(SkipError, match="too short"):
        process_audio(np.zeros(16000, dtype=np.float32), 16000)
    with pytest.raises(SkipError, match="empty"):
        process_audio(np.zeros(0, dtype=np.float32), 16000)
    with pytest.raises(SkipError, match="too long"):
        process_audio(np.full(16000 * 16, 0.1, dtype=np.float32), 16000)


def test_prepare_clipping_flag() -> None:
    x = np.full(16000, 0.5, dtype=np.float32)
    x[:400] = 1.0                                     # 2.5% mẫu chạm 1.0
    assert process_audio(x, 16000)[1].clipping
    x[:400] = 0.9
    assert not process_audio(x, 16000)[1].clipping


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="cần ffmpeg")
def test_prepare_decode_m4a(tmp_path: Path) -> None:
    import subprocess
    wav = write_tone(tmp_path / "x.wav", seconds=1.0, lead_s=0.0)
    m4a = tmp_path / "x.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-c:a", "aac", str(m4a)], check=True)
    assert abs(decode_audio(m4a).size - config.SAMPLE_RATE) < 2000
    bad = tmp_path / "bad.m4a"
    bad.write_bytes(b"not audio")
    with pytest.raises(SkipError, match="decode error"):
        decode_audio(bad)


# --- prepare() trên thư mục tạm ---

def test_prepare_end_to_end(data_dir: Path, script_md: Path) -> None:
    raw_before = {p.name: p.read_bytes() for p in (data_dir / config.RAW_SUBDIR).iterdir()}
    s = prepare(data_dir, script_md)
    proc = config.processed_dir(data_dir)
    manifest = {r["clip_id"]: r for r in _read(proc / "manifest.csv")}
    skipped = {Path(r["file"]).name: r["reason"] for r in _read(proc / "skipped.csv")}

    assert s["manifest"] + s["skipped"] == s["files"] == 7
    assert set(manifest) == {"A_07_r", "A_07_n", "A_25_r", "A_C03_r"}
    assert skipped["ghi_am_moi.wav"] == "bad name"
    assert skipped["A_99_r.wav"] == "not in script"
    assert skipped["A_25_n.wav"].startswith("too short")

    r = manifest["A_07_r"]
    assert (r["speaker"], r["gender"], r["sentence_id"], r["take"]) == ("A", "male", "07", "r")
    assert r["text_ref"] == "Phòng khám số 205 đi đường nào?" and r["intent"] == "hoi_phong"
    assert r["ref_verified"] == "True" and r["clipping"] == "False"
    assert manifest["A_07_n"]["ref_verified"] == "False"
    assert manifest["A_C03_r"]["ref_verified"] == "True"
    assert manifest["A_C03_r"]["src_path"] == f"{config.RAW_SUBDIR}/Nam_C03.wav"

    info = sf.info(str(proc / "wav" / "A_07_r.wav"))
    assert (info.samplerate, info.channels, info.subtype) == (16000, 1, "PCM_16")
    assert info.duration == pytest.approx(1.4, abs=0.06)

    missing = {r["clip_id"] for r in _read(proc / "missing.csv")}
    assert missing == {"A_25_n", "A_C03_n", "B_C03_r", "B_C03_n"}
    assert [r["clip_id"] for r in _read(proc / "transcripts_n_todo.csv")] == ["A_07_n"]
    # Không ghi gì vào thư mục nguồn.
    assert {p.name: p.read_bytes() for p in (data_dir / config.RAW_SUBDIR).iterdir()} == raw_before


def test_prepare_idempotent(data_dir: Path, script_md: Path) -> None:
    prepare(data_dir, script_md)
    proc = config.processed_dir(data_dir)
    snap = {p.name: p.read_bytes() for p in proc.rglob("*") if p.is_file()}
    mtimes = {p.name: p.stat().st_mtime_ns for p in (proc / "wav").iterdir()}
    s = prepare(data_dir, script_md)
    assert s["converted"] == 0 and s["reused"] == 4
    assert {p.name: p.read_bytes() for p in proc.rglob("*") if p.is_file()} == snap
    assert {p.name: p.stat().st_mtime_ns for p in (proc / "wav").iterdir()} == mtimes


def test_prepare_reconverts_changed_source(data_dir: Path, script_md: Path) -> None:
    prepare(data_dir, script_md)
    write_tone(data_dir / config.RAW_SUBDIR / "A_07_r.wav", seconds=2.0)
    s = prepare(data_dir, script_md)
    assert s["converted"] == 1
    dur = {r["clip_id"]: float(r["duration_s"]) for r in _read(config.manifest_path(data_dir))}
    assert dur["A_07_r"] == pytest.approx(2.4, abs=0.06)


def test_prepare_text_fixed_takes_priority(data_dir: Path, script_md: Path) -> None:
    prepare(data_dir, script_md)
    todo = config.processed_dir(data_dir) / "transcripts_n_todo.csv"
    rows = _read(todo)
    rows[0]["text_fixed"] = "ờ phòng khám số 205 thì đi đường nào ạ"
    with todo.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    prepare(data_dir, script_md)
    r = {r["clip_id"]: r for r in _read(config.manifest_path(data_dir))}["A_07_n"]
    assert r["text_ref"] == "ờ phòng khám số 205 thì đi đường nào ạ"
    assert r["ref_verified"] == "True"
    assert _read(todo)[0]["text_fixed"] == "ờ phòng khám số 205 thì đi đường nào ạ", "giữ text_fixed cũ"


def test_prepare_duplicate_clip_id_skipped(data_dir: Path, script_md: Path) -> None:
    write_tone(data_dir / config.RAW_SUBDIR / "A_C03_r.wav")   # trùng với Nam_C03
    prepare(data_dir, script_md)
    skipped = _read(config.processed_dir(data_dir) / "skipped.csv")
    assert any(r["reason"].startswith("duplicate clip_id A_C03_r") for r in skipped)


# --- sync_voices ---

def test_prepare_sync_voices(data_dir: Path, script_md: Path, tmp_path: Path) -> None:
    prepare(data_dir, script_md)
    dest = tmp_path / "voices"
    (dest).mkdir()
    (dest / "OLD_01_r.wav").write_bytes(b"x")
    c = sync(data_dir, dest)
    assert c == {"copied": 4, "kept": 0, "removed": 1}
    clips = json.loads((dest / "clips.json").read_text(encoding="utf-8"))
    assert set(clips) == {"A_07_r", "A_07_n", "A_25_r", "A_C03_r"}
    assert set(clips["A_07_r"]) == {"speaker", "gender", "sentence_id", "take", "intent", "duration_s"}
    assert "text_ref" not in json.dumps(clips) and "Phòng" not in json.dumps(clips, ensure_ascii=False)
    assert sync(data_dir, dest) == {"copied": 0, "kept": 4, "removed": 0}


def test_prepare_build_clips_types() -> None:
    rows = [{"clip_id": "A_01_r", "speaker": "A", "gender": "male", "sentence_id": "01", "take": "r",
             "intent": "x", "duration_s": "1.25", "text_ref": "bí mật"}]
    assert build_clips(rows) == {"A_01_r": {"speaker": "A", "gender": "male", "sentence_id": "01", "take": "r",
                                             "intent": "x", "duration_s": 1.25}}
