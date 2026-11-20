"""Đọc số nguyên thành chữ tiếng Việt (dùng cho sinh câu G18 và chuẩn hóa văn bản TTS G21).

Ngược lại với `voice.intent.parse_vi_number` (G14).
"""

from __future__ import annotations

DIGIT_WORDS: tuple[str, ...] = ("không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín")


def spell_digits(digits: str) -> str:
    """Đọc từng chữ số: "205" ➔ "hai không năm"."""
    if not digits.isdigit():
        raise ValueError(f"not a digit string: {digits!r}")
    return " ".join(DIGIT_WORDS[int(c)] for c in digits)


def _two(n: int, after_hundred: bool) -> list[str]:
    tens, units = divmod(n, 10)
    if tens == 0:
        if units == 0:
            return []
        return (["linh"] if after_hundred else []) + [DIGIT_WORDS[units]]
    out = ["mười"] if tens == 1 else [DIGIT_WORDS[tens], "mươi"]
    if units == 5:
        out.append("lăm")
    elif units == 1 and tens >= 2:
        out.append("mốt")
    elif units:
        out.append(DIGIT_WORDS[units])
    return out


def read_number(n: int) -> str:
    """0–999 đọc theo hàng: 205 ➔ "hai trăm linh năm", 115 ➔ "một trăm mười lăm", 21 ➔ "hai mươi mốt"."""
    if not 0 <= n <= 999:
        raise ValueError(f"out of range 0..999: {n}")
    if n == 0:
        return "không"
    hundreds, rest = divmod(n, 100)
    words = [DIGIT_WORDS[hundreds], "trăm"] if hundreds else []
    return " ".join(words + _two(rest, after_hundred=bool(hundreds)))
