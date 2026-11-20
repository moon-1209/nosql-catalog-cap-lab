"""Chuẩn hóa văn bản để tính WER (Mục 2.6, G13)."""

from __future__ import annotations

import re
import unicodedata

# Mục 2.6 bước 3, thêm ngoặc kép/đơn kiểu chữ in (“ ” ‘ ’) và gạch dài (– —) cho cùng nghĩa.
PUNCT: str = ".,!?;:\"'()…-“”‘’–—"
_PUNCT_RE = re.compile("[" + re.escape(PUNCT) + "]")
_SPACE_RE = re.compile(r"\s+")
_NUM_RE = re.compile(r"\d+")


def normalize(text: str) -> str:
    """NFC ➔ chữ thường ➔ bỏ dấu câu (giữ dấu thanh) ➔ gộp khoảng trắng. Không đổi số sang chữ."""
    t = unicodedata.normalize("NFC", text).lower()
    t = _PUNCT_RE.sub(" ", t)
    return _SPACE_RE.sub(" ", t).strip()


def numbers(text: str) -> list[str]:
    return _NUM_RE.findall(normalize(text))


def has_number_mismatch(ref: str, hyp: str) -> bool:
    """`ref` có số viết bằng chữ số mà `hyp` không có đúng số đó (vd viết bằng chữ)."""
    hyp_nums = set(numbers(hyp))
    return any(n not in hyp_nums for n in numbers(ref))
