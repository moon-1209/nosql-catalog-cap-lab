from __future__ import annotations

import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from voice import config
from voice.eval_stt import (Condition, SttCache, bootstrap_ci, build_grid, corpus_wer, evaluate, main, score,
                            summarize)
from voice.prepare_data import prepare
from voice.stt_server import ClipStore, read_manifest
from voice.text_norm import has_number_mismatch, normalize
from voice.transcriber import FakeTranscriber
from voice_testutil import data_dir, script_md  # noqa: F401  (fixture)


# --- text_norm ---

def test_normalize_example() -> None:
    assert normalize("Phòng khám số 205 đi đường nào?") == "phòng khám số 205 đi đường nào"


def test_normalize_punctuation_case_spaces() -> None:
    assert normalize('  Khoan,   DỪNG lại chút; "bố" (mình) mệt…!  ') == "khoan dừng lại chút bố mình mệt"
    assert normalize("X-quang") == "x quang"
    assert normalize("Ok, cảm ơn bạn nhiều nha.") == "ok cảm ơn bạn nhiều nha"


def test_normalize_nfc_nfd_same() -> None:
    s = "Khoa tiêu hóa ở tầng mấy?"
    nfd = unicodedata.normalize("NFD", s)
    assert nfd != s
    assert normalize(nfd) == normalize(s)
    assert unicodedata.is_normalized("NFC", normalize(nfd))


def test_normalize_keeps_tone_marks_and_numbers() -> None:
    assert normalize("Phòng 304 Ở ĐÂU") == "phòng 304 ở đâu"


@pytest.mark.parametrize("ref,hyp,expected", [
    ("phòng 205", "phòng hai trăm linh năm", True),
    ("phòng 205", "Phòng 205?", False),
    ("phòng 112 ở tầng một", "phòng 112 ở tầng 1", False),
    ("phòng 304", "phòng 340", True),
    ("không có số", "hai trăm", False),
])
def test_number_mismatch(ref: str, hyp: str, expected: bool) -> None:
    assert has_number_mismatch(ref, hyp) is expected


# --- score / WER ---

def test_score_identical_is_zero() -> None:
    s = score("Phòng khám số 205 đi đường nào?", "phòng khám số 205, đi đường nào")
    assert s["wer"] == 0 and s["cer"] == 0 and s["ref_words"] == 7


def test_score_counts_errors() -> None:
    s = score("a b c d", "a x c")
    assert (s["word_errors"], s["ref_words"]) == (2, 4) and s["wer"] == 0.5


def test_corpus_wer_and_bootstrap_contains_mean() -> None:
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"clip_id": [f"c{i}" for i in range(40)], "ref_words": rng.integers(4, 12, 40)})
    df["word_errors"] = rng.binomial(df["ref_words"], 0.2)
    w = corpus_wer(df)
    lo, hi = bootstrap_ci(df, 1000, 0)
    assert lo <= w <= hi and hi - lo > 0


def test_bootstrap_degenerate() -> None:
    df = pd.DataFrame({"clip_id": ["a", "b"], "word_errors": [0, 0], "ref_words": [5, 5]})
    assert bootstrap_ci(df) == (0.0, 0.0)


# --- lưới ---

def test_default_grid() -> None:
    g = build_grid("default")
    assert len([c for c in g if c.noise == "none"]) == 4
    assert {c.snr_db for c in g if c.noise == "none"} == {30.0}
    assert len([c for c in g if c.noise != "none"]) == 4 * 4 * 2
    assert {c.distance_m for c in g} == {0.5, 1.0, 2.0, 3.0}


# --- evaluate ---

@pytest.fixture
def store(data_dir: Path, script_md: Path) -> ClipStore:  # noqa: F811
    prepare(data_dir, script_md)
    return ClipStore(read_manifest(config.manifest_path(data_dir)), config.wav_dir(data_dir), data_dir / "noise")


def _fake(store: ClipStore) -> FakeTranscriber:
    return FakeTranscriber({c: r["text_ref"] for c, r in store.manifest.items()})


GRID = [Condition(1.0, 30.0, "none"), Condition(2.0, 10.0, "white"), Condition(1.0, 5.0, "babble")]


def test_evaluate_fake_wer_zero_everywhere(store: ClipStore) -> None:
    df = evaluate(store, _fake(store), GRID, "fake", 1, SttCache(None))
    assert len(df) == 3 * 4 and (df["error"] == "").all()
    tables = summarize(df, n_boot=50)
    for t in tables.values():
        assert (t["wer"] == 0).all() and (t["cer"] == 0).all()
    assert tables["all"]["n_clips"].iloc[0] == 3               # A_07_n chưa xác minh


def test_evaluate_skips_unverified_wer(store: ClipStore) -> None:
    df = evaluate(store, FakeTranscriber({}, default="sai hoàn toàn"), GRID, "fake", 1, SttCache(None),
                  classify=lambda t: "unknown")
    n = df[df["clip_id"] == "A_07_n"]
    assert n["wer"].isna().all() and n["number_mismatch"].isna().all()
    assert n["intent_ok"].notna().all(), "clip _n vẫn tính intent"
    r = df[df["clip_id"] == "A_07_r"]
    assert (r["wer"] > 0).all() and r["number_mismatch"].all()


def test_evaluate_cache_hit_skips_transcriber(store: ClipStore, tmp_path: Path) -> None:
    path = tmp_path / "cache.jsonl"
    fake = _fake(store)
    evaluate(store, fake, GRID, "m", 1, SttCache(path))
    assert fake.calls == 12
    fake2 = _fake(store)
    df = evaluate(store, fake2, GRID, "m", 1, SttCache(path))
    assert fake2.calls == 0 and df["cached"].all()
    fake3 = _fake(store)
    evaluate(store, fake3, GRID, "m", 2, SttCache(path))       # beams khác ➔ không trúng cache
    assert fake3.calls == 12


def test_evaluate_error_does_not_stop(store: ClipStore) -> None:
    class Flaky(FakeTranscriber):
        def transcribe(self, audio, sr, clip_id=None):  # type: ignore[override]
            if clip_id == "A_25_r":
                raise RuntimeError("boom")
            return super().transcribe(audio, sr, clip_id)
    df = evaluate(store, Flaky({c: r["text_ref"] for c, r in store.manifest.items()}), GRID, "f", 1, SttCache(None))
    bad = df[df["clip_id"] == "A_25_r"]
    assert (bad["error"] == "RuntimeError: boom").all()
    assert (df[df["clip_id"] != "A_25_r"]["error"] == "").all()


def test_summary_snr_table_excludes_none(store: ClipStore) -> None:
    df = evaluate(store, _fake(store), GRID, "fake", 1, SttCache(None))
    assert list(summarize(df, n_boot=10)["snr_db"]["snr_db"]) == [5.0, 10.0]


def test_main_fake_pipeline(data_dir: Path, script_md: Path, tmp_path: Path) -> None:  # noqa: F811
    prepare(data_dir, script_md)
    out = tmp_path / "reports"
    assert main(["--fake", "--grid", "quick", "--data-dir", str(data_dir), "--out", str(out)]) == 0
    assert (out / "stt_summary.md").exists() and (out / "wer_vs_snr.png").exists()
    assert (out / "wer_vs_distance.png").exists()
    csvs = list(out.glob("stt_eval_*.csv"))
    assert len(csvs) == 1 and pd.read_csv(csvs[0])["wer"].fillna(0).eq(0).all()
