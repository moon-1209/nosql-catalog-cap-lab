from __future__ import annotations

import random
from collections import Counter
from pathlib import Path

import pandas as pd
import pytest

from nlu import asr_noise, build_dataset as bd, config
from nlu.segment import Segmenter
from nlu.vi_numbers import read_number, spell_digits
from voice.intent import load_map, numbers_in, tokenize


class CountingBackend:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, text: str) -> list[str]:
        self.calls += 1
        return [text.replace("tim mạch", "tim_mạch")]


def test_segment_uses_cache() -> None:
    backend = CountingBackend()
    seg = Segmenter(backend)
    assert seg("khoa tim mạch ở đâu") == "khoa tim_mạch ở đâu"
    assert seg("khoa  tim mạch ở đâu ") == "khoa tim_mạch ở đâu"
    assert backend.calls == 1
    assert seg("") == "" and backend.calls == 1


def test_segment_missing_files_reports_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="VnCoreNLP-1.2.jar"):
        Segmenter(vncorenlp_dir=tmp_path)("khoa nhi")


@pytest.mark.parametrize("n,text", [(205, "hai trăm linh năm"), (112, "một trăm mười hai"), (115, "một trăm mười lăm"),
                                    (125, "một trăm hai mươi lăm"), (321, "ba trăm hai mươi mốt"), (210, "hai trăm mười"),
                                    (300, "ba trăm"), (0, "không"), (21, "hai mươi mốt"), (7, "bảy")])
def test_read_number(n: int, text: str) -> None:
    assert read_number(n) == text
    if n:                                             # G14 coi "không" đứng một mình là phủ định
        assert numbers_in(tokenize(text)) == [n]      # khớp với bộ đọc số của G14


def test_spell_digits() -> None:
    assert spell_digits("205") == "hai không năm"
    with pytest.raises(ValueError):
        spell_digits("2a5")


def test_templates_fill_every_slot_value() -> None:
    values = bd.slot_values(load_map())
    seed = [{"id": "s1", "intent": "hoi_khoa", "kind": "q", "text": "cho tôi hỏi khoa {department} ở đâu"},
            {"id": "s2", "intent": "hoi_phong", "kind": "q", "text": "phòng {room_name} ở đâu"},
            {"id": "s3", "intent": "cam_on", "kind": "c", "text": "cảm ơn bạn"}]
    out = bd.expand_templates(seed, values)
    khoa = [s.text for s in out if s.base == "s1"]
    assert len(khoa) == len(values["department"])
    assert "cho tôi hỏi khoa tiêu hóa ở đâu" in khoa
    assert not any("{" in s.text for s in out)
    assert "phòng tiêm ở đâu" in [s.text for s in out if s.base == "s2"]      # không thành "phòng phòng tiêm"
    assert [s.source for s in out if s.base == "s3"] == ["seed"]


def test_slot_values_only_from_map() -> None:
    hmap = load_map()
    values = bd.slot_values(hmap)
    assert "cấp cứu" not in values["department"]
    numbers = {r["number"] for r in hmap["rooms"]}
    assert {v for v in values["room"] if v.isdigit()} == numbers
    assert "hai trăm linh năm" in values["room"] and "hai không năm" in values["room"]


def test_unknown_placeholder_raises() -> None:
    with pytest.raises(ValueError, match="unknown placeholder"):
        bd.expand_templates([{"id": "x", "intent": "hoi_khoa", "kind": "q", "text": "khoa {abc}"}], {})


def test_rule_variants() -> None:
    v = bd.rule_variants("tôi muốn tìm thang máy", "c")
    assert "em muốn tìm thang máy" in v and "muốn tìm thang máy" in v
    assert "dạ tôi muốn tìm thang máy nhé" in v
    assert "tôi muốn tìm thang máy" not in v
    assert not any(t.endswith("với nhé") for t in bd.rule_variants("đợi tôi với", "c"))
    assert all(not t.endswith("không nhỉ") for t in bd.rule_variants("có xe lăn không", "q"))


def test_dedupe_conflicting_labels_raise() -> None:
    a = bd.Sample("Cảm ơn!", "cam_on", "seed", "s1")
    assert [s.text for s in bd.dedupe([a, bd.Sample("cảm ơn", "cam_on", "variant", "s1")])] == ["cảm ơn"]
    with pytest.raises(ValueError, match="different intents"):
        bd.dedupe([a, bd.Sample("cảm ơn", "unknown", "seed", "s2")])


def test_remove_similar_drops_near_test_sentence() -> None:
    pool = [bd.Sample("phòng khám số 205 đi đường nào", "hoi_phong", "template", "s1"),
            bd.Sample("phòng khám số 205 đi đường nào ạ", "hoi_phong", "variant", "s1"),
            bd.Sample("nhà thuốc ở chỗ nào", "nha_thuoc", "seed", "s2")]
    kept, leaked = bd.remove_similar(pool, ["Phòng khám số 205 đi đường nào?"])
    assert [s.text for s in kept] == ["nhà thuốc ở chỗ nào"]
    assert len(leaked) == 2 and leaked[0]["similarity"] == 1.0
    assert leaked[0]["similar_to"] == "phòng khám số 205 đi đường nào"


def test_stratified_split_keeps_ratio() -> None:
    samples = [bd.Sample(f"{it} câu {i}", it, "seed", "b") for it in ("a", "b", "c") for i in range(100)]
    train, val = bd.stratified_split(samples, 0.15, 42)
    assert len(val) == 45 and len(train) == 255
    assert Counter(s.intent for s in val) == {"a": 15, "b": 15, "c": 15}
    again = bd.stratified_split(samples, 0.15, 42)
    assert [s.text for s in again[1]] == [s.text for s in val]


def test_balanced_sample_covers_every_base() -> None:
    samples = [bd.Sample(f"x{i}", "a", "variant", "big") for i in range(100)] + \
              [bd.Sample(f"y{i}", "a", "variant", "small") for i in range(3)]
    out = bd.balanced_sample(samples, 10, random.Random(0))
    assert len(out) == 10 and sum(s.base == "small" for s in out) == 3


def test_asr_noise_same_seed_same_result() -> None:
    texts = [f"cho tôi hỏi khoa tim mạch ở tầng mấy {i}" for i in range(50)]
    a = asr_noise.augment(texts, 0.3, 42)
    assert a == asr_noise.augment(texts, 0.3, 42)
    assert a != asr_noise.augment(texts, 0.3, 7)
    assert 10 <= len(a) <= 15 and all(t != texts[i] for i, t in a)


def test_asr_noise_ops() -> None:
    assert asr_noise.strip_accents("đường") == "duong"
    rng = random.Random(0)
    assert asr_noise._apply("homophone", ["khoa", "nhi"], rng) == ["hoa", "nhi"]
    assert asr_noise._apply("homophone", ["xin", "chào"], rng) is None
    assert asr_noise._apply("drop_short", ["đi", "tiếp"], rng) is None


def _write_inputs(tmp: Path) -> tuple[Path, Path, Path, Path]:
    out = tmp / "nlu"
    out.mkdir()
    rows = ["id,intent,kind,text"]
    for k, it in enumerate(config.INTENTS):
        rows += [f"s{k}a,{it},c,câu mẫu {it.replace('_', ' ')} số một", f"s{k}b,{it},c,tôi nói {it.replace('_', ' ')}"]
    (out / "seed.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    manifest = tmp / "manifest.csv"
    pd.DataFrame([{"clip_id": "A_07_r", "text_ref": "Phòng khám số 205 đi đường nào?", "intent": "hoi_phong",
                   "ref_verified": "True"},
                  {"clip_id": "A_07_n", "text_ref": "Phòng khám số 205 đi đường nào?", "intent": "hoi_phong",
                   "ref_verified": "False"}]).to_csv(manifest, index=False)
    stt = tmp / "stt.csv"
    pd.DataFrame([{"clip_id": "A_07_r", "hyp": "phòng khám số hai trăm linh năm đi đường nào", "error": None,
                   "intent_true": "hoi_phong", "snr_db": 20.0, "distance_m": 1.0, "noise": "babble"},
                  {"clip_id": "A_07_n", "hyp": "x", "error": None, "intent_true": "hoi_phong", "snr_db": 20.0,
                   "distance_m": 1.0, "noise": "babble"}]).to_csv(stt, index=False)
    script = tmp / "script.md"
    script.write_text("| Mã | Câu | Intent |\n| :-- | :-- | :-- |\n| A_07 | Phòng khám số 205 đi đường nào? | hoi_phong |\n",
                      encoding="utf-8")
    return out, manifest, stt, script


def test_build_end_to_end(tmp_path: Path) -> None:
    out, manifest, stt, script = _write_inputs(tmp_path)
    rc = bd.build(out, manifest, stt, script, segment=lambda t: t.replace(" ", "_", 1), per_intent=100)
    assert rc == 0
    train = pd.read_csv(out / "train.csv")
    assert list(train.columns) == bd.COLUMNS
    assert (train.groupby("intent").size() >= bd.MIN_TRAIN).all()
    test_ref = pd.read_csv(out / "test_ref.csv")
    assert list(test_ref["clip_id"]) == ["A_07_r"]                       # chỉ clip ref_verified
    test_stt = pd.read_csv(out / "test_stt.csv")
    assert list(test_stt["clip_id"]) == ["A_07_r"] and test_stt["snr_db"].tolist() == [20.0]
    test_texts = {bd.normalize(t) for t in pd.concat([test_ref["text"], test_stt["text"]])}
    assert not test_texts & set(train["text"]) and not test_texts & set(pd.read_csv(out / "val.csv")["text"])
    assert train["text_seg"].iloc[0] == train["text"].iloc[0].replace(" ", "_", 1)


def test_build_stops_when_intent_too_small(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out, manifest, stt, script = _write_inputs(tmp_path)
    assert bd.build(out, manifest, stt, script, segment=str, per_intent=40) == 2
    assert "CẢNH BÁO" in capsys.readouterr().err
    assert not (out / "train.csv").exists()
