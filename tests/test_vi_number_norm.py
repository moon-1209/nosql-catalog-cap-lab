"""Tests for Vietnamese number-word normalization (metric variant only).

Covers representative number expressions from the hospital voice dataset and
locks the baseline metric behavior (predictions CSV <-> metrics summary).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from vi_number_norm import normalize_numbers  # noqa: E402


@pytest.mark.parametrize(
    "spoken,digits",
    [
        # room number 205 — both common spellings
        ("phòng khám số hai trăm linh lăm đi đường nào", "phòng khám số 205 đi đường nào"),
        ("phòng khám số hai trăm lẻ năm thì đi đường nào", "phòng khám số 205 thì đi đường nào"),
        # room number 304 — full form + "số"-context shorthands
        ("phòng siêu âm số ba trăm lẻ bốn ở đâu", "phòng siêu âm số 304 ở đâu"),
        ("phòng siêu âm số ba lẻ bốn ở đâu", "phòng siêu âm số 304 ở đâu"),
        ("phòng siêu âm số ba không bốn ở đâu", "phòng siêu âm số 304 ở đâu"),
        # 112 via full trăm+mười form
        ("phòng một trăm mười hai ở tầng một hay tầng hai", "phòng 112 ở tầng 1 hay tầng 2"),
        # tens forms
        ("hai mươi mốt", "21"),
        ("hai mươi", "20"),
        ("mười hai", "12"),
        ("mười", "10"),
        # thousands
        ("hai nghìn lẻ năm", "2005"),
        ("hai nghìn", "2000"),
        # lone units
        ("tầng ba", "tầng 3"),
        ("lần đầu", "lần đầu"),  # 'lần' is not a number word
    ],
)
def test_number_phrases(spoken, digits):
    assert normalize_numbers(spoken) == digits


@pytest.mark.parametrize(
    "text,expected",
    [
        # negation "không" is NOT the digit zero and must be preserved
        ("ở đây có thanh toán bằng chuyển khoản không",
         "ở đây có thanh toán bằng chuyển khoản không"),
        # "năm" is dual-use (five OR year): standalone "năm" never converts;
        # "hai trăm" alone is unambiguous and converts to 200
        ("hai trăm năm ngoái", "200 năm ngoái"),
        ("năm ngoái", "năm ngoái"),
        # misheard marker "lấy" is not a number form — no merge happens;
        # units still normalize to digits (symmetric on both sides)
        ("phòng siêu âm số ba lấy bốn là nằm ở đâu",
         "phòng siêu âm số 3 lấy 4 là nằm ở đâu"),
        # no number words at all
        ("chào bạn cho mình hỏi chỗ đăng ký khám ở đâu vậy",
         "chào bạn cho mình hỏi chỗ đăng ký khám ở đâu vậy"),
        # "U lẻ U" NOT in số/phòng context: no N0U merge, units still normalize
        ("em thích ba lẻ bốn", "em thích 3 lẻ 4"),
    ],
)
def test_non_numeric_or_ambiguous_preserved(text, expected):
    assert normalize_numbers(text) == expected


def test_idempotent():
    s = "phòng một trăm mười hai ở tầng hai"
    assert normalize_numbers(normalize_numbers(s)) == normalize_numbers(s)


def test_does_not_touch_digits():
    assert normalize_numbers("phòng 304 ở tầng 3") == "phòng 304 ở tầng 3"


# --- baseline preservation: stored predictions reproduce stored summary ---
import csv  # noqa: E402
import json  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "src/data/stt/evaluation/predictions/asr_predictions_180_samples.csv"
SUMMARY = ROOT / "src/data/stt/evaluation/metrics/asr_summary.json"


@pytest.mark.skipif(not PRED.exists(), reason="benchmark predictions not present")
def test_baseline_metrics_reproduce_from_predictions():
    jiwer = pytest.importorskip("jiwer")
    rows = list(csv.DictReader(open(PRED, encoding="utf-8")))
    summary = json.load(open(SUMMARY, encoding="utf-8"))
    assert len(rows) == 180
    assert abs(jiwer.wer([r["ground_truth"] for r in rows],
                         [r["prediction"] for r in rows]) - summary["overall"]["raw_wer"]) < 1e-4
    assert abs(jiwer.wer([r["norm_ground_truth"] for r in rows],
                         [r["norm_prediction"] for r in rows]) - summary["overall"]["norm_wer"]) < 1e-4
    assert abs(jiwer.cer([r["norm_ground_truth"] for r in rows],
                         [r["norm_prediction"] for r in rows]) - summary["overall"]["norm_cer"]) < 1e-4
