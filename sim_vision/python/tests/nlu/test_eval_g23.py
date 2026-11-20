from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nlu import eval_nlu as ev
from nlu.nlu import IntentResult
from tts import config as tts_config
from tts.eval_tts_roundtrip import evaluate as rt_evaluate, render as rt_render
from tts.tts_engine import FakeTTS, Synthesizer, TtsCache
from voice import analyze_e2e


def _engine(mapping: dict[str, str], conf: float = 0.9):
    return lambda t: IntentResult(mapping.get(t, "unknown"), conf if t in mapping else 0.2, {}, "fake", [])


def _sets() -> dict[str, pd.DataFrame]:
    ref = pd.DataFrame({"id": ["r0", "r1", "r2"], "clip_id": ["A_25_r", "A_06_r", "A_15_r"],
                        "text": ["cứu", "khoa", "thuốc"], "intent": ["cap_cuu", "hoi_khoa", "nha_thuoc"]})
    stt = pd.DataFrame({"id": [f"s{i}" for i in range(6)], "clip_id": ["A_25_r", "A_06_r", "A_15_r"] * 2,
                        "text": ["cứu", "khoa", "thuốc", "cấp cũ", "khoa", "thuốt"],
                        "intent": ["cap_cuu", "hoi_khoa", "nha_thuoc"] * 2,
                        "snr_db": [30.0, 30.0, 30.0, 5.0, 5.0, 5.0], "distance_m": [1.0, 1.0, 1.0, 3.0, 3.0, 3.0],
                        "noise": ["none"] * 3 + ["babble"] * 3})
    return {"test_ref": ref, "test_stt": stt}


ENGINES = {
    "rule": (_engine({"cứu": "cap_cuu", "khoa": "hoi_khoa", "thuốc": "nha_thuoc"}), 0.6),
    "phobert": (_engine({"cứu": "cap_cuu", "khoa": "hoi_khoa", "thuốc": "nha_thuoc", "cấp cũ": "cap_cuu",
                         "thuốt": "nha_thuoc"}), 0.6),
}


def test_evaluate_same_rows_and_metrics() -> None:
    res = ev.evaluate(_sets(), ENGINES)
    assert len(res["test_ref"]) == 3 and len(res["test_stt"]) == 6
    m_rule, m_pho = ev.metrics(res["test_stt"], "rule"), ev.metrics(res["test_stt"], "phobert")
    assert m_rule["accuracy"] == pytest.approx(4 / 6) and m_pho["accuracy"] == 1.0
    assert m_rule["recall_cap_cuu"] == 0.5 and m_pho["recall_cap_cuu"] == 1.0
    assert m_rule["clarify_rate"] == pytest.approx(2 / 6)
    assert m_rule["f1_lo"] <= m_rule["macro_f1"] <= m_rule["f1_hi"]


def test_mcnemar_counts() -> None:
    a = np.array([True, True, False, False, True])
    b = np.array([True, False, True, True, True])
    r = ev.mcnemar_test(a, b)
    assert (r["b"], r["c"]) == (1, 2) and 0 < r["p"] <= 1
    assert ev.mcnemar_test(a, a) == {"b": 0, "c": 0, "p": 1.0}


def test_condition_groups_clean_separately() -> None:
    stt = _sets()["test_stt"]
    assert list(ev.condition(stt)) == ["sạch"] * 3 + ["5 dB"] * 3


def test_render_report_and_plot(tmp_path: Path) -> None:
    res = ev.evaluate(_sets(), ENGINES)
    md = ev.render(res, {"rule": 0.6, "phobert": 0.55}, "x.png")
    assert "| test_ref | Luật (G14) | 3 |" in md and "McNemar" in md
    assert "`A_25_r` (babble, 5 dB, 3 m): \"cấp cũ\" ➔ unknown" in md
    assert "Hạn chế" in md
    ev.plot(res["test_stt"], tmp_path / "p.png")
    assert (tmp_path / "p.png").stat().st_size > 1000


def test_tts_roundtrip_with_fake(tmp_path: Path) -> None:
    cache = TtsCache(tmp_path)
    synth = Synthesizer(FakeTTS(), cache, "v")
    synth.speak("Dạ, phòng 205 ở tầng 2.", "G")
    df = rt_evaluate(["Dạ, phòng 205 ở tầng 2.", "Chưa sinh."], "G", cache,
                     lambda audio: "dạ phòng hai không năm ở tầng hai", "v")
    assert df.loc[0, "wer"] == 0.0 and df.loc[0, "spoken"] == "Dạ, phòng hai không năm ở tầng hai."
    assert df.loc[1, "error"] == "not cached"
    md = rt_render(df, "G")
    assert "thiếu cache: 1" in md and "so nguyên văn | 0.0%" in md
    assert tts_config.OUT_SAMPLE_RATE == 24000


def test_analyze_e2e_latency_and_actions() -> None:
    manifest = pd.DataFrame([{"clip_id": "A_25_r", "text_ref": "Cứu với!", "intent": "cap_cuu", "ref_verified": "True"},
                             {"clip_id": "A_15_r", "text_ref": "Nhà thuốc ở đâu?", "intent": "nha_thuoc",
                              "ref_verified": "True"}])
    base = {"speaker": "A", "snr_db": 20.0, "noise": "babble", "error": "", "effective_snr_db": 20.0, "intent_conf": 1.0,
            "sim_time_s": 20.0, "h_target": 0.8, "seed": 0, "distance_m": 1.6, "target": None, "response_len": 30}
    batch = pd.DataFrame([
        {**base, "episode": 0, "clip_id": "A_25_r", "completed": "true", "hyp_text": "cứu với", "intent_pred": "cap_cuu",
         "stt_ms": 800.0, "tts_ms": 20.0, "latency_ms": 1000.0, "action": "emergency", "tts_cache_hit": "true",
         "tts_error": None, "speak_duration_s": 3.0},
        {**base, "episode": 1, "clip_id": "A_15_r", "completed": "true", "hyp_text": "nhà thuốc ở đâu",
         "intent_pred": "nha_thuoc", "stt_ms": 600.0, "tts_ms": 40.0, "latency_ms": 800.0, "action": "answer",
         "tts_cache_hit": "false", "tts_error": None, "speak_duration_s": 2.5},
    ])
    df = analyze_e2e.merge(batch, manifest)
    split = analyze_e2e.latency_split(df).set_index("phần")["TB"]
    assert split["STT"] == 700.0 and split["TTS"] == 30.0 and split["NLU + mạng + khung hình"] == 170.0
    md = analyze_e2e.render(df, "b.csv")
    assert "| emergency | 1 |" in md and "Hoàn thành lượt | 2/2" in md and "TTS cache hit | 50.0%" in md
