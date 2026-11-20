"""Tạo lỗi giả kiểu STT cho câu train (G18). Cùng seed ➔ cùng kết quả.

Mỗi câu chịu 1–2 phép biến đổi: bỏ dấu một chữ, thay chữ gần âm, xóa hoặc nhân đôi một từ ngắn.
"""

from __future__ import annotations

import random
import unicodedata

# Cặp gần âm hay gặp khi STT nghe sai (tự định nghĩa; "khám ➔ khá" thấy thật ở G13).
HOMOPHONES: dict[str, str] = {
    "khoa": "hoa", "tầng": "tần", "khám": "khá", "phòng": "phong", "thuốc": "thuốt", "đâu": "đau",
    "chậm": "chặm", "dẫn": "dẩn", "nhiêu": "nhiu", "tiền": "tiềng", "giúp": "dúp", "gì": "dì",
    "rồi": "dồi", "lại": "lạy", "máu": "mấu", "số": "xố", "xe": "se", "nói": "lói",
    "bảo": "bão", "hỏi": "hõi", "mấy": "mầy", "nào": "nàu",
}
SHORT_MAX_LEN: int = 3
OPS: tuple[str, ...] = ("strip_accent", "homophone", "drop_short", "dup_short")


def strip_accents(word: str) -> str:
    """Bỏ hết dấu (thanh và mũ), đ ➔ d."""
    nfd = unicodedata.normalize("NFD", word.replace("đ", "d").replace("Đ", "D"))
    return unicodedata.normalize("NFC", "".join(c for c in nfd if not unicodedata.combining(c)))


def _apply(op: str, words: list[str], rng: random.Random) -> list[str] | None:
    """Trả câu mới hoặc None nếu phép này không áp được cho câu."""
    if op == "strip_accent":
        idx = [i for i, w in enumerate(words) if strip_accents(w) != w]
        if not idx:
            return None
        i = rng.choice(idx)
        return words[:i] + [strip_accents(words[i])] + words[i + 1:]
    if op == "homophone":
        idx = [i for i, w in enumerate(words) if w in HOMOPHONES]
        if not idx:
            return None
        i = rng.choice(idx)
        return words[:i] + [HOMOPHONES[words[i]]] + words[i + 1:]
    idx = [i for i, w in enumerate(words) if len(w) <= SHORT_MAX_LEN]
    if not idx or (op == "drop_short" and len(words) < 3):
        return None
    i = rng.choice(idx)
    if op == "drop_short":
        return words[:i] + words[i + 1:]
    return words[:i + 1] + [words[i]] + words[i + 1:]


def corrupt(text: str, rng: random.Random) -> str:
    """1–2 phép ngẫu nhiên; không phép nào áp được ➔ trả nguyên câu."""
    words = text.split()
    n_ops = rng.choice((1, 1, 2))
    ops = list(OPS)
    rng.shuffle(ops)
    done = 0
    for op in ops:
        new = _apply(op, words, rng)
        if new is not None:
            words = new
            done += 1
            if done == n_ops:
                break
    return " ".join(words)


def augment(texts: list[str], frac: float = 0.3, seed: int = 42) -> list[tuple[int, str]]:
    """Chọn ngẫu nhiên `frac` số câu, trả [(chỉ số câu gốc, câu lỗi)] (bỏ câu không đổi)."""
    rng = random.Random(seed)
    k = round(len(texts) * frac)
    picks = sorted(rng.sample(range(len(texts)), k))
    out: list[tuple[int, str]] = []
    for i in picks:
        noisy = corrupt(texts[i], rng)
        if noisy != texts[i]:
            out.append((i, noisy))
    return out
