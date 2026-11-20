"""Chuẩn bị dữ liệu (G11): file thu âm ➔ wav 16 kHz mono đã cắt im lặng + manifest.csv.

Chạy: python -m voice.prepare_data [--data-dir DIR] [--script docs/kich_ban_thu_am.md]
Không ghi gì vào thư mục nguồn; mọi thứ ghi vào <data>/processed/.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

from voice import config
from voice.transcripts import ScriptRow, load_script_table

NAME_RE = re.compile(r"^(A|B)_(\d{2}|C\d{2})_(r|n)\.(wav|m4a)$")
# Câu chung thu một lần, đặt tên Nam_Cxx / Nu_Cxx ➔ coi là bản đọc rõ (người dùng chọn 2026-10-21).
ALIAS_RE = re.compile(r"^(Nam|Nu)_(C\d{2})\.(wav|m4a)$")
ALIAS_SPEAKER: dict[str, str] = {"Nam": "A", "Nu": "B"}
GENDER: dict[str, str] = {"A": "male", "B": "female"}
TAKES: tuple[str, ...] = ("r", "n")

MIN_S: float = 0.3
MAX_S: float = 15.0
KEEP_SILENCE_S: float = 0.2
TRIM_TOP_DB: float = 40.0
TRIM_FRAME: int = 512                 # 32 ms ở 16 kHz (mặc định 2048 dư ~70 ms mỗi bên)
TRIM_HOP: int = 128
CLIP_LEVEL: float = 0.999
CLIP_RATIO: float = 0.01

MANIFEST_COLS: list[str] = ["clip_id", "speaker", "gender", "sentence_id", "take", "text_ref", "intent",
                            "ref_verified", "duration_s", "rms_dbfs", "clipping", "src_path"]
CACHE_NAME: str = ".prepare_cache.json"


class SkipError(Exception):
    """File không dùng được; message là lý do ghi vào skipped.csv."""


@dataclass(frozen=True)
class ClipName:
    speaker: str
    sentence_id: str
    take: str

    @property
    def clip_id(self) -> str:
        return f"{self.speaker}_{self.sentence_id}_{self.take}"

    @property
    def key(self) -> str:
        return f"{self.speaker}_{self.sentence_id}"


@dataclass(frozen=True)
class ClipInfo:
    duration_s: float
    rms_dbfs: float
    clipping: bool


def parse_name(name: str) -> ClipName | None:
    """Tên file ➔ ClipName, không khớp ➔ None."""
    m = NAME_RE.match(name)
    if m:
        return ClipName(m.group(1), m.group(2), m.group(3))
    m = ALIAS_RE.match(name)
    if m:
        return ClipName(ALIAS_SPEAKER[m.group(1)], m.group(2), "r")
    return None


def decode_audio(path: Path, sr: int = config.SAMPLE_RATE) -> np.ndarray:
    """Đọc file ➔ float32 mono ở `sr`. .m4a qua ffmpeg hoặc PyAV; .wav qua soundfile + librosa."""
    if path.suffix.lower() == ".m4a":
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is not None:
            proc = subprocess.run([ffmpeg, "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                                  capture_output=True, check=False)
            if proc.returncode == 0:
                return np.frombuffer(proc.stdout, dtype=np.float32).copy()
        try:
            import av
            container = av.open(str(path))
            if container.streams.audio:
                stream = container.streams.audio[0]
                resampler = av.AudioResampler(format="flt", layout="mono", rate=sr)
                chunks = []
                for packet in container.demux(stream):
                    try:
                        for frame in packet.decode():
                            for rf in resampler.resample(frame):
                                chunks.append(rf.to_ndarray().flatten())
                    except Exception:
                        continue
                if chunks:
                    return np.concatenate(chunks, axis=0).astype(np.float32)
        except Exception as exc:
            raise SkipError("decode error") from exc
        raise SkipError("decode error")
    try:
        audio, file_sr = sf.read(str(path), dtype="float32", always_2d=True)
    except (sf.LibsndfileError, RuntimeError) as exc:
        raise SkipError("decode error") from exc
    mono = audio.mean(axis=1)
    if file_sr != sr:
        import librosa
        mono = librosa.resample(mono, orig_sr=file_sr, target_sr=sr)
    return mono.astype(np.float32)


def trim_silence(audio: np.ndarray, sr: int, keep_s: float = KEEP_SILENCE_S,
                 top_db: float = TRIM_TOP_DB) -> np.ndarray:
    """Cắt im lặng đầu cuối, giữ lại tối đa `keep_s` giây mỗi bên. Toàn im lặng ➔ mảng rỗng."""
    if audio.size == 0 or not np.any(audio):
        return audio[:0]
    import librosa
    _, (start, end) = librosa.effects.trim(audio, top_db=top_db, frame_length=TRIM_FRAME, hop_length=TRIM_HOP)
    keep = int(round(keep_s * sr))
    return audio[max(start - keep, 0):min(end + keep, audio.size)]


def clipping_ratio(audio: np.ndarray) -> float:
    return float(np.mean(np.abs(audio) >= CLIP_LEVEL)) if audio.size else 0.0


def rms_dbfs(audio: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(np.square(audio, dtype=np.float64)))) if audio.size else 0.0
    return 20.0 * np.log10(rms) if rms > 0 else float("-inf")


def process_audio(audio: np.ndarray, sr: int) -> tuple[np.ndarray, ClipInfo]:
    """Hàm thuần: cắt im lặng, kiểm tra độ dài, đo mức. Lỗi ➔ SkipError."""
    if audio.size == 0:
        raise SkipError("empty")
    clip = clipping_ratio(audio) > CLIP_RATIO
    out = trim_silence(audio, sr)
    dur = out.size / sr
    if dur < MIN_S:
        raise SkipError(f"too short ({dur:.2f} s)")
    if dur > MAX_S:
        raise SkipError(f"too long ({dur:.2f} s)")
    return out, ClipInfo(round(dur, 3), round(rms_dbfs(out), 2), clip)


def read_todo_fixes(path: Path) -> dict[str, str]:
    """clip_id ➔ text_fixed (chỉ dòng có giá trị) từ transcripts_n_todo.csv cũ."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {r["clip_id"]: r["text_fixed"].strip() for r in csv.DictReader(f) if (r.get("text_fixed") or "").strip()}


def _write_csv(path: Path, cols: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def _src_sig(path: Path) -> dict:
    st = path.stat()
    return {"size": st.st_size, "mtime_ns": st.st_mtime_ns}


def prepare(data_dir: Path, script_md: Path, src_dirs: list[Path] | None = None) -> dict[str, int]:
    """Theo pseudocode G11.2. Trả số lượng {manifest, skipped, missing, converted, reused}."""
    script: dict[str, ScriptRow] = load_script_table(script_md)
    out_dir = config.processed_dir(data_dir)
    wav_dir = config.wav_dir(data_dir)
    wav_dir.mkdir(parents=True, exist_ok=True)
    cache_path = out_dir / CACHE_NAME
    cache: dict = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    todo_path = out_dir / "transcripts_n_todo.csv"
    fixes = read_todo_fixes(todo_path)

    manifest: list[dict] = []
    skipped: list[dict] = []
    seen: set[str] = set()
    new_cache: dict = {}
    counts = {"converted": 0, "reused": 0}
    files = sorted(p for d in (src_dirs or [data_dir / config.RAW_SUBDIR]) for p in d.rglob("*")
                   if p.is_file() and not p.name.startswith("."))
    for f in files:
        rel = f.relative_to(data_dir).as_posix() if f.is_relative_to(data_dir) else Path(f).as_posix()
        name = parse_name(f.name)
        if name is None:
            skipped.append({"file": rel, "reason": "bad name"})
            continue
        if name.key not in script:
            skipped.append({"file": rel, "reason": "not in script"})
            continue
        if name.clip_id in seen:
            skipped.append({"file": rel, "reason": f"duplicate clip_id {name.clip_id}"})
            continue
        out_wav = wav_dir / f"{name.clip_id}.wav"
        sig = {"src": rel, **_src_sig(f)}
        old = cache.get(name.clip_id)
        if old and {k: old.get(k) for k in sig} == sig and out_wav.exists():
            info = ClipInfo(old["duration_s"], old["rms_dbfs"], old["clipping"])
            counts["reused"] += 1
        else:
            try:
                audio, info = process_audio(decode_audio(f), config.SAMPLE_RATE)
            except SkipError as exc:
                skipped.append({"file": rel, "reason": str(exc)})
                continue
            sf.write(str(out_wav), audio, config.SAMPLE_RATE, subtype="PCM_16")
            counts["converted"] += 1
        seen.add(name.clip_id)
        new_cache[name.clip_id] = {**sig, **asdict(info)}
        row = script[name.key]
        fixed = fixes.get(name.clip_id) if name.take == "n" else None
        manifest.append({
            "clip_id": name.clip_id, "speaker": name.speaker, "gender": GENDER[name.speaker],
            "sentence_id": name.sentence_id, "take": name.take, "text_ref": fixed or row.text,
            "intent": row.intent, "ref_verified": name.take == "r" or fixed is not None,
            "duration_s": info.duration_s, "rms_dbfs": info.rms_dbfs, "clipping": info.clipping, "src_path": rel,
        })

    missing = [{"clip_id": f"{key}_{take}", "text": script[key].text}
               for key in script for take in TAKES if f"{key}_{take}" not in seen]
    todo = [{"clip_id": r["clip_id"], "text_script": script[f"{r['speaker']}_{r['sentence_id']}"].text,
             "text_fixed": fixes.get(r["clip_id"], "")} for r in manifest if r["take"] == "n"]
    # Giữ text_fixed của clip đã từng có trong todo nhưng lần này không có file.
    todo += [{"clip_id": cid, "text_script": "", "text_fixed": txt} for cid, txt in fixes.items()
             if cid not in {t["clip_id"] for t in todo}]

    _write_csv(config.manifest_path(data_dir), MANIFEST_COLS, manifest)
    _write_csv(out_dir / "skipped.csv", ["file", "reason"], skipped)
    _write_csv(out_dir / "missing.csv", ["clip_id", "text"], missing)
    _write_csv(todo_path, ["clip_id", "text_script", "text_fixed"], todo)
    cache_path.write_text(json.dumps(new_cache, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return {"files": len(files), "manifest": len(manifest), "skipped": len(skipped), "missing": len(missing), **counts}


def describe_tree(data_dir: Path, depth: int = 2) -> str:
    lines = [str(data_dir)]
    for p in sorted(data_dir.rglob("*")):
        rel = p.relative_to(data_dir)
        if p.is_dir() and len(rel.parts) <= depth:
            lines.append(f"  {rel}/ ({sum(1 for q in p.iterdir() if q.is_file())} file)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=config.DATA_DIR)
    p.add_argument("--script", type=Path, default=config.SCRIPT_MD)
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    src = args.data_dir / config.RAW_SUBDIR
    if not src.is_dir():
        print(f"không thấy thư mục dữ liệu {src}. Cấu trúc thực tế:\n{describe_tree(args.data_dir)}", file=sys.stderr)
        return 2
    s = prepare(args.data_dir, args.script)
    print(f"{s['files']} file: manifest {s['manifest']} (mới {s['converted']}, giữ {s['reused']}), "
          f"skipped {s['skipped']}, missing {s['missing']} ➔ {config.processed_dir(args.data_dir)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
