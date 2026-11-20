from __future__ import annotations

from collections import Counter

import pytest

from voice import config, responses
from voice.intent import INTENTS, classify, contains, load_map, numbers_in, parse_vi_number, tokenize
from voice.transcripts import load_script_table

SCRIPT = load_script_table(config.SCRIPT_MD)
# B_Cxx trùng câu với A_Cxx ➔ chỉ lấy 70 câu khác nhau.
UNIQUE = {k: v for k, v in SCRIPT.items() if not k.startswith("B_C")}


def test_intent_accuracy_on_script(capsys: pytest.CaptureFixture[str]) -> None:
    pairs = [(r.intent, classify(r.text).intent) for r in UNIQUE.values()]
    acc = sum(t == p for t, p in pairs) / len(pairs)
    confusion = Counter((t, p) for t, p in pairs if t != p)
    with capsys.disabled():
        print(f"\nintent accuracy trên text_ref: {acc:.1%} ({len(pairs)} câu); nhầm: {dict(confusion) or 'không'}")
    assert acc >= 0.95


def test_intent_labels_in_script_are_known() -> None:
    assert {r.intent for r in SCRIPT.values()} <= set(INTENTS)


@pytest.mark.parametrize("text,intent,slots", [
    ("bố mình đang khó thở quá gọi bác sĩ giúp mình với", "cap_cuu", {}),
    ("khoa tiêu hóa ở tầng mấy", "hoi_khoa", {"department": "tiêu hóa"}),
    ("phòng 112 ở tầng một hay tầng hai ạ", "hoi_phong", {"room": "112", "floor": "1"}),
    ("em có cần đeo khẩu trang không ạ", "khong_ho_tro", {}),
    ("xin chào", "unknown", {}),
])
def test_intent_examples(text: str, intent: str, slots: dict[str, str]) -> None:
    r = classify(text)
    assert r.intent == intent and r.slots == slots
    assert r.conf == (0.0 if intent == "unknown" else 1.0)


def test_intent_unknown_response() -> None:
    assert responses.build("unknown", {}) == "Dạ, anh chị cần tôi giúp gì ạ?"


def test_intent_whole_word_only() -> None:
    toks = tokenize("Khoa cấp cứu ở đâu?")
    assert contains(toks, "đâu") and not contains(toks, "đau")
    assert not contains(tokenize("nhiều người"), "nhi")
    assert classify("nhân viên hướng dẫn ở đâu").intent == "gap_nhan_vien"
    assert classify("quầy hướng dẫn ở đâu").intent != "dan_duong", "'dẫn' trong 'hướng dẫn' không tính"
    assert classify("bệnh viện nghỉ trưa lúc nào").intent != "dung_lai"


@pytest.mark.parametrize("text,intent", [
    ("bà em chóng mặt, gọi nhân viên giúp em", "cap_cuu"),          # cap_cuu trước gap_nhan_vien
    ("khoan dừng lại, đi chậm thôi", "dung_lai"),                   # dung_lai trước dieu_chinh_toc_do
    ("bà em nghe không rõ, nói to hơn", "dieu_chinh_am_luong"),     # trước nhac_lai
    ("dẫn tôi đến khoa sản", "dan_duong"),                          # trước hoi_khoa
    ("dẫn bố mình đến phòng 302", "dan_duong"),                     # trước hoi_phong
    ("khoa cấp cứu ở đâu", "cap_cuu"),                              # không phải hoi_khoa
    ("bao lâu thì có kết quả xét nghiệm", "thoi_gian_cho"),         # dịch vụ không kèm vị trí ➔ không hoi_phong
    ("xét nghiệm máu thì lấy máu ở đâu", "hoi_phong"),
    ("lấy thuốc bảo hiểm ở đâu", "nha_thuoc"),                      # nha_thuoc trước bao_hiem
    ("bố mình bị đau ngực, khám tim mạch ở đâu", "hoi_khoa"),       # đau ngực không phải cap_cuu
])
def test_intent_priority(text: str, intent: str) -> None:
    assert classify(text).intent == intent


def test_intent_weak_match_conf() -> None:
    assert classify("chậm").conf == 0.6
    assert classify("đi chậm").conf == 1.0


@pytest.mark.parametrize("words,n", [
    ("hai trăm linh năm", 205), ("hai trăm lẻ năm", 205), ("hai trăm linh lăm", 205),
    ("một trăm mười hai", 112), ("ba trăm linh tư", 304), ("ba không bốn", 304),
    ("hai mươi lăm", 25), ("mười", 10), ("ba trăm", 300), ("hai trăm năm mươi lăm", 255),
    ("chín mươi mốt", 91),
])
def test_parse_vi_number(words: str, n: int) -> None:
    assert parse_vi_number(words.split()) == n


def test_numbers_in_ignores_negation() -> None:
    assert numbers_in(tokenize("có được không")) == []
    assert numbers_in(tokenize("phòng 205 hay phòng hai trăm linh sáu")) == [205, 206]


def test_slots_from_stt_style_text() -> None:
    assert classify("Phòng khám số hai trăm linh lăm đi đường nào?").slots == {"room": "205"}
    assert classify("Phòng siêu âm số ba không bốn ở đâu?").slots["room"] == "304"
    assert classify("phòng nội soi ở đâu").slots == {"room": "208"}
    assert classify("dẫn bố con mình đến phòng siêu âm tim").slots["room"] == "302", "bí danh dài nhất thắng"
    assert classify("nhà vệ sinh nữ ở đâu ạ").slots == {"facility": "nha_ve_sinh"}


# --- hospital_map ---

def test_map_is_mock_and_sizes() -> None:
    m = load_map()
    assert m["is_mock"] is True
    assert len(m["departments"]) >= 12 and len(m["rooms"]) >= 15
    keys = {f["key"] for f in m["facilities"]}
    assert {"nha_thuoc", "thu_ngan", "cap_cuu", "thang_may", "nha_ve_sinh"} <= keys


@pytest.mark.parametrize("text,slot,value", [
    ("khoa tiêu hóa", "department", "tiêu hóa"), ("khoa tim mạch", "department", "tim mạch"),
    ("khoa tai mũi họng", "department", "tai mũi họng"), ("khoa cơ xương khớp", "department", "cơ xương khớp"),
    ("khám xương khớp", "department", "cơ xương khớp"), ("khoa nhi", "department", "nhi"),
    ("khoa sản", "department", "sản"), ("khoa cấp cứu", "department", "cấp cứu"),
    ("phòng 205", "room", "205"), ("phòng 112", "room", "112"), ("phòng 304", "room", "304"),
    ("phòng nội soi ở đâu", "room", "208"), ("lấy máu ở đâu", "room", "110"), ("lấy kết quả ở đâu", "room", "115"),
    ("phòng siêu âm tim", "room", "302"), ("phòng điện tim", "room", "303"), ("chụp x quang phổi", "room", "130"),
    ("phiếu chỉ định", "room", "105"), ("phòng vật lý trị liệu", "room", "140"), ("đọc kết quả", "room", "211"),
])
def test_map_covers_every_place_in_script(text: str, slot: str, value: str) -> None:
    assert classify(text).slots.get(slot) == value


# --- responses ---

def test_response_example_room() -> None:
    assert responses.build("hoi_phong", {"room": "205"}) == "Dạ, phòng 205 ở tầng 2. Mời anh chị đi theo tôi."


def test_response_fixed_cap_cuu_and_khong_ho_tro() -> None:
    assert responses.build("cap_cuu", {"department": "tim mạch"}) == \
        "Tôi đang gọi nhân viên y tế ngay. Anh chị giữ bình tĩnh nhé."
    assert "bác sĩ" in responses.build("khong_ho_tro", {})


def test_response_missing_slot_asks_back() -> None:
    assert responses.build("hoi_khoa", {}).startswith("Dạ, anh chị muốn đến khoa nào ạ?")
    assert responses.build("hoi_phong", {}) == "Dạ, anh chị muốn đến phòng nào ạ?"
    assert responses.build("dan_duong", {}) == "Dạ, anh chị muốn tôi dẫn đến đâu ạ?"
    assert responses.build("tien_ich", None) == responses.ASK_FACILITY


def test_response_unknown_room_uses_first_digit_floor() -> None:
    assert responses.build("hoi_phong", {"room": "507"}) == "Dạ, phòng 507 ở tầng 5. Mời anh chị đi theo tôi."


def test_response_every_script_sentence() -> None:
    for r in UNIQUE.values():
        res = classify(r.text)
        out = responses.build(res.intent, res.slots)
        assert out.startswith(("Dạ", "Tôi đang gọi")) and len(out) < 160


def test_response_no_medical_advice() -> None:
    texts = [responses.build(i, s) for i in INTENTS for s in ({}, {"department": "nhi", "room": "205",
                                                                   "facility": "nha_thuoc"})]
    banned = ("nên uống", "uống thuốc", "liều", "nhịn ăn", "bệnh của", "chẩn đoán", "không sao đâu", "nên khám khoa")
    assert not [t for t in texts if any(b in t.lower() for b in banned)]
