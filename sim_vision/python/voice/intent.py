"""Nhận intent và slot bằng luật từ khóa (G14). Không gọi LLM.

Khớp nguyên từ / cụm từ trên văn bản đã chuẩn hóa (text_norm.normalize), theo thứ tự ưu tiên:
cap_cuu ➔ dung_lai ➔ dieu_chinh_toc_do ➔ dieu_chinh_am_luong ➔ nhac_lai ➔ gap_nhan_vien ➔ dan_duong
➔ hoi_khoa ➔ hoi_phong ➔ các intent còn lại ➔ unknown.
intent_conf: 1.0 khớp cụm từ đặc trưng, 0.6 chỉ khớp từ đơn, 0 khi unknown.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from voice.text_norm import normalize

MAP_PATH: Path = Path(__file__).with_name("hospital_map.json")
STRONG: float = 1.0
WEAK: float = 0.6

# Cụm từ ghép thành một token trước khi khớp, để từ đơn bên trong không bị khớp nhầm
# (vd "dẫn" trong "hướng dẫn", "nghỉ" trong "nghỉ trưa", "nội" trong "nội soi").
COMPOUNDS: tuple[str, ...] = ("hướng dẫn", "tiếp đón", "nghỉ trưa", "nội soi")

# (intent, cụm từ đặc trưng ➔ 1.0, từ đơn ➔ 0.6). Thứ tự = thứ tự ưu tiên của các intent dùng luật thường.
Rule = tuple[str, tuple[str, ...], tuple[str, ...]]
RULES_HIGH: tuple[Rule, ...] = (
    ("cap_cuu", ("cấp cứu", "khó thở", "chóng mặt", "sắp ngã", "bị ngã", "ngất xỉu", "bất tỉnh", "co giật",
                 "gọi bác sĩ", "cứu với", "cứu tôi", "khẩn cấp"), ("ngất", "xỉu", "ngã")),
    ("dung_lai", ("dừng lại", "đứng lại", "ngồi nghỉ", "nghỉ một chút", "nghỉ chút", "đợi một chút", "chờ một chút",
                  "đợi chút", "chờ chút"), ("dừng", "khoan")),
    ("dieu_chinh_toc_do", ("đi chậm", "chậm lại", "chậm thôi", "đi nhanh", "nhanh lên", "nhanh hơn"), ("chậm",)),
    ("dieu_chinh_am_luong", ("nói to", "to hơn", "nói lớn", "lớn hơn", "âm lượng", "nói to lên"), ()),
    ("nhac_lai", ("nói lại", "nhắc lại", "lặp lại", "chỉ lại", "không hiểu", "chưa hiểu", "chưa nghe kịp",
                  "chưa nghe rõ", "nghe không kịp"), ()),
    ("gap_nhan_vien", ("gặp nhân viên", "gọi nhân viên", "hỏi ai", "người thật", "gặp người"), ("nhân viên",)),
    ("dan_duong", ("dẫn tôi", "dẫn em", "dẫn mình", "dẫn bố", "dẫn bà", "dẫn đường", "dẫn giúp", "bạn dẫn",
                   "đưa tôi đến", "đưa tôi tới", "đưa em đến", "đưa em tới", "dẫn đi"), ("dẫn",)),
)
RULES_LOW: tuple[Rule, ...] = (
    ("khong_ho_tro", ("nhịn ăn", "khẩu trang", "uống thuốc", "thuốc gì", "bệnh gì", "có sao không", "có nguy hiểm",
                      "kiêng", "liều"), ("có cần",)),
    ("nha_thuoc", ("nhà thuốc", "lấy thuốc", "mua thuốc", "quầy thuốc"), ("thuốc",)),
    ("bao_hiem", ("bảo hiểm", "căn cước", "bhyt"), ()),
    ("thanh_toan", ("đóng tiền", "trả tiền", "viện phí", "thanh toán", "chuyển khoản", "thu ngân", "nộp tiền"),
     ("tiền",)),
    ("dang_ky_kham", ("đăng ký", "lấy số", "thủ tục", "đặt lịch", "khám lần đầu", "quầy ưu tiên", "tiếp đón"),
     ("ưu tiên",)),
    ("ho_tro_di_chuyen", ("xe lăn", "xe đẩy", "mượn xe", "đi lại hơi khó", "đi lại khó"), ()),
    ("thoi_gian_cho", ("bao lâu", "mấy giờ", "bao nhiêu người", "tới lượt", "tới số", "đến lượt", "nghỉ trưa",
                       "chờ lâu"), ()),
    ("tien_ich", ("thang máy", "nhà vệ sinh", "gửi xe", "ngồi chờ", "ghế chờ", "đồ ăn", "căng tin", "nhà ăn",
                  "toilet", "để xe"), ()),
    ("tiep_tuc", ("đi tiếp", "tiếp tục"), ()),
    ("cam_on", ("cảm ơn", "cám ơn"), ()),
)
INTENTS: tuple[str, ...] = tuple(r[0] for r in RULES_HIGH) + ("hoi_khoa", "hoi_phong") + \
    tuple(r[0] for r in RULES_LOW) + ("unknown",)

# hoi_phong: dịch vụ chỉ tính khi đi kèm từ hỏi vị trí (để "bao lâu có kết quả xét nghiệm" ➔ thoi_gian_cho).
LOCATION_CUES: tuple[str, ...] = ("ở đâu", "đâu", "đường nào", "lối nào", "chỗ nào", "chỗ", "quầy nào", "phòng nào",
                                  "tầng mấy", "tầng nào")
DIGITS: dict[str, int] = {"không": 0, "linh": 0, "lẻ": 0, "một": 1, "mốt": 1, "hai": 2, "ba": 3, "bốn": 4, "tư": 4,
                          "năm": 5, "lăm": 5, "sáu": 6, "bảy": 7, "bẩy": 7, "tám": 8, "chín": 9}
NUM_WORDS: frozenset[str] = frozenset(DIGITS) | {"mười", "mươi", "trăm"}


@dataclass(frozen=True)
class IntentResult:
    intent: str
    conf: float
    slots: dict[str, str] = field(default_factory=dict)


def _compound(tokens: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(tokens):
        for c in COMPOUNDS:
            parts = c.split()
            if tokens[i:i + len(parts)] == parts:
                out.append("_".join(parts))
                i += len(parts)
                break
        else:
            out.append(tokens[i])
            i += 1
    return out


def tokenize(text: str) -> list[str]:
    return _compound(normalize(text).split())


def _phrase_tokens(phrase: str) -> list[str]:
    return _compound(normalize(phrase).split())


def contains(tokens: list[str], phrase: str) -> bool:
    """Khớp nguyên từ / cụm từ liên tiếp (không khớp chuỗi con)."""
    p = _phrase_tokens(phrase)
    return any(tokens[i:i + len(p)] == p for i in range(len(tokens) - len(p) + 1)) if p else False


def match_rule(tokens: list[str], strong: tuple[str, ...], weak: tuple[str, ...]) -> float:
    if any(contains(tokens, s) for s in strong):
        return STRONG
    if any(contains(tokens, w) for w in weak):
        return WEAK
    return 0.0


def parse_vi_number(words: list[str]) -> int | None:
    """Số đọc bằng chữ ➔ int: "hai trăm linh năm" 205, "một trăm mười hai" 112, "ba không bốn" 304."""
    if not words or any(w not in NUM_WORDS for w in words):
        return None
    if "trăm" not in words and "mươi" not in words and "mười" not in words:
        return int("".join(str(DIGITS[w]) for w in words))         # đọc từng chữ số
    total, cur = 0, 0
    for w in words:
        if w == "trăm":
            total += (cur or 1) * 100
            cur = 0
        elif w == "mươi":
            cur = (cur or 1) * 10
        elif w == "mười":
            cur += 10
        else:
            cur += DIGITS[w]
    return total + cur


def numbers_in(tokens: list[str]) -> list[int]:
    """Số viết bằng chữ số và số đọc bằng chữ (chuỗi từ số liên tiếp) theo thứ tự xuất hiện."""
    out: list[int] = []
    i = 0
    while i < len(tokens):
        if tokens[i].isdigit():
            out.append(int(tokens[i]))
            i += 1
            continue
        j = i
        while j < len(tokens) and tokens[j] in NUM_WORDS:
            j += 1
        # "không" đứng một mình thường là phủ định, không phải số.
        if j > i and tokens[i:j] != ["không"]:
            n = parse_vi_number(tokens[i:j])
            if n is not None:
                out.append(n)
            i = j
        else:
            i += 1
    return out


@lru_cache(maxsize=1)
def load_map(path: Path = MAP_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_alias(tokens: list[str], items: list[dict]) -> dict | None:
    """Mục có bí danh dài nhất khớp trong câu (ưu tiên "siêu âm tim" hơn "siêu âm")."""
    best, best_len = None, 0
    for it in items:
        for a in it["aliases"]:
            n = len(_phrase_tokens(a))
            if n > best_len and contains(tokens, a):
                best, best_len = it, n
    return best


def extract_slots(tokens: list[str]) -> dict[str, str]:
    m = load_map()
    slots: dict[str, str] = {}
    dept = _find_alias(tokens, m["departments"])
    if dept is not None:
        slots["department"] = dept["name"].lower()
    room = next((str(n) for n in numbers_in(tokens) if 100 <= n <= 999), None)
    if room is None:
        named = _find_alias(tokens, m["rooms"])
        room = named["number"] if named is not None else None
    if room is not None:
        slots["room"] = room
    for i, t in enumerate(tokens[:-1]):
        if t == "tầng":
            n = numbers_in(tokens[i + 1:i + 2])
            if n and 0 <= n[0] <= 20:
                slots["floor"] = str(n[0])
                break
    fac = _find_alias(tokens, m["facilities"])
    if fac is not None:
        slots["facility"] = fac["key"]
    return slots


def _has_department(tokens: list[str]) -> bool:
    return _find_alias(tokens, load_map()["departments"]) is not None


def _hoi_khoa(tokens: list[str]) -> float:
    if contains(tokens, "khoa nào") or contains(tokens, "khám khoa") or _has_department(tokens):
        return STRONG
    return WEAK if contains(tokens, "khoa") else 0.0


def _hoi_phong(tokens: list[str]) -> float:
    if contains(tokens, "phòng"):
        return STRONG
    named = _find_alias(tokens, load_map()["rooms"])
    if named is not None and any(contains(tokens, c) for c in LOCATION_CUES):
        return STRONG
    return 0.0


def classify(text: str) -> IntentResult:
    tokens = tokenize(text)
    slots = extract_slots(tokens)
    for name, strong, weak in RULES_HIGH:
        conf = match_rule(tokens, strong, weak)
        if conf:
            return IntentResult(name, conf, slots)
    for name, fn in (("hoi_khoa", _hoi_khoa), ("hoi_phong", _hoi_phong)):
        conf = fn(tokens)
        if conf:
            return IntentResult(name, conf, slots)
    for name, strong, weak in RULES_LOW:
        conf = match_rule(tokens, strong, weak)
        if conf:
            return IntentResult(name, conf, slots)
    return IntentResult("unknown", 0.0, slots)


__all__ = ["INTENTS", "IntentResult", "classify", "extract_slots", "load_map", "numbers_in", "parse_vi_number",
           "tokenize"]
