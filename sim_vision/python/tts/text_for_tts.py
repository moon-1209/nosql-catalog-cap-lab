"""Chuẩn hóa văn bản trước khi đọc (G21): số phòng đọc từng chữ số, số khác đọc theo hàng, viết tắt ➔ đầy đủ.

text_for_tts("Phòng 205") ➔ "Phòng hai không năm"; "tầng 2" ➔ "tầng hai"; "BHYT" ➔ "bảo hiểm y tế".
"""

from __future__ import annotations

import re
import unicodedata

from nlu.vi_numbers import read_number, spell_digits

ABBREVIATIONS: dict[str, str] = {
    "BHYT": "bảo hiểm y tế", "CCCD": "căn cước công dân", "WC": "nhà vệ sinh", "X-quang": "x quang", "CT": "xi ti",
}
# Số phòng: "phòng 205", "phòng số 205" ➔ đọc từng chữ số (quy ước gọi phòng trong bệnh viện).
_ROOM_RE = re.compile(r"(?i)\b(phòng(?:\s+số)?)\s+(\d{2,4})\b")
_NUM_RE = re.compile(r"\d+")


def _abbrev(text: str) -> str:
    for short, full in ABBREVIATIONS.items():
        text = re.sub(rf"(?<!\w){re.escape(short)}(?!\w)", full, text)
    return text


def _number(m: re.Match[str]) -> str:
    digits = m.group(0)
    n = int(digits)
    return read_number(n) if n <= 999 and not (len(digits) > 1 and digits[0] == "0") else spell_digits(digits)


def text_for_tts(text: str) -> str:
    t = unicodedata.normalize("NFC", text)
    t = _abbrev(t)
    t = _ROOM_RE.sub(lambda m: f"{m.group(1)} {spell_digits(m.group(2))}", t)
    t = _NUM_RE.sub(_number, t)
    return " ".join(t.split())
