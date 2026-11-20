from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from voice import analyze_dialogue as ad

MANIFEST = pd.DataFrame([
    {"clip_id": "A_25_r", "text_ref": "Bố mình đang khó thở quá, gọi bác sĩ giúp mình với!", "intent": "cap_cuu",
     "ref_verified": "True"},
    {"clip_id": "A_26_n", "text_ref": "Khoa cấp cứu ở đâu?", "intent": "cap_cuu", "ref_verified": "False"},
    {"clip_id": "A_06_r", "text_ref": "Khoa tiêu hóa ở tầng mấy?", "intent": "hoi_khoa", "ref_verified": "True"},
])


def batch() -> pd.DataFrame:
    base = {"speaker": "A", "snr_db": 20.0, "noise": "babble", "error": "", "effective_snr_db": 20.0,
            "intent_conf": 1.0, "stt_ms": 800.0, "sim_time_s": 20.0}
    return pd.DataFrame([
        {**base, "episode": 0, "seed": 0, "h_target": 0.75, "clip_id": "A_25_r", "completed": "true",
         "distance_m": 1.9, "hyp_text": "bố mình đang khó thở quá gọi bác sĩ giúp mình với", "intent_pred": "cap_cuu",
         "latency_ms": 900.0},
        {**base, "episode": 1, "seed": 1, "h_target": 0.80, "clip_id": "A_26_n", "completed": "true",
         "distance_m": 1.6, "hyp_text": "khoa cấp cũ ở đâu", "intent_pred": "hoi_khoa", "latency_ms": 1100.0},
        {**base, "episode": 2, "seed": 2, "h_target": 0.85, "clip_id": "A_06_r", "completed": "true",
         "distance_m": 1.5, "hyp_text": "khoa tiêu hóa ở từng máy", "intent_pred": "hoi_khoa", "latency_ms": 1000.0},
        {**base, "episode": 3, "seed": 3, "h_target": 0.75, "clip_id": "A_06_r", "completed": "false",
         "error": "timeout", "distance_m": None, "hyp_text": None, "intent_pred": None, "latency_ms": None},
    ])


def test_merge_scores_only_verified_completed() -> None:
    df = ad.merge(batch(), MANIFEST)
    assert df["wer"].notna().tolist() == [True, False, True, False]
    assert df.loc[2, "word_errors"] == 2 and df.loc[2, "ref_words"] == 6
    assert df["intent_ok"].tolist() == [True, False, True, False]


def test_cap_cuu_recall_and_misses() -> None:
    recall, missed = ad.cap_cuu(ad.merge(batch(), MANIFEST))
    assert recall == 0.5 and missed["clip_id"].tolist() == ["A_26_n"]


def test_by_group_distance() -> None:
    g = ad.by_group(ad.merge(batch(), MANIFEST), "h_target")
    row = g[g["h_target"] == 0.75].iloc[0]
    assert row["n"] == 2 and row["completed"] == 1 and row["wer"] == 0.0 and row["intent_acc"] == 1.0


def test_g13_reference_same_condition() -> None:
    df = ad.merge(batch(), MANIFEST)
    stt = pd.DataFrame([
        {"clip_id": "A_06_r", "noise": "babble", "snr_db": 20.0, "distance_m": 1.0, "wer": 0.1, "word_errors": 1,
         "ref_words": 6},
        {"clip_id": "A_06_r", "noise": "babble", "snr_db": 20.0, "distance_m": 2.0, "wer": 0.3, "word_errors": 2,
         "ref_words": 6},
        {"clip_id": "A_06_r", "noise": "babble", "snr_db": 10.0, "distance_m": 1.0, "wer": 0.9, "word_errors": 5,
         "ref_words": 6},
    ])
    ref = ad.g13_reference(stt, df).iloc[0]
    assert ref["g13_wer_1m"] == pytest.approx(1 / 6) and ref["g13_wer_2m"] == pytest.approx(2 / 6)


def test_render_report(tmp_path: Path) -> None:
    md = ad.render(ad.merge(batch(), MANIFEST), None, "dialogue_batch_x.csv")
    assert "Hoàn thành một lượt | 3/4 (75.0%)" in md
    assert "**Recall cap_cuu** | 50.0%" in md
    assert "A_26_n" in md and "khoa cấp cũ ở đâu" in md
    assert "Hạn chế" in md and "người cao tuổi" in md
    assert "timeout: 1" in md


def test_main_without_batch_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert ad.main(["--batch", str(tmp_path / "none.csv"), "--out", str(tmp_path / "o.md")]) == 1
    assert "dialogue_batch" in capsys.readouterr().err
