"""Mô phỏng âm thanh tới micro robot (G12): giảm âm theo khoảng cách, trộn ồn.

Hàm thuần: cùng input và cùng trạng thái `rng` ➔ cùng kết quả.
"""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np

from voice import config

MIN_DIST_M: float = 0.3
MAX_GAIN: float = 1.5
BABBLE_MIN: int = 4
BABBLE_MAX: int = 6
BABBLE_ATTEN_DB: float = 20.0
BUILTIN_NOISES: tuple[str, ...] = ("none", "white", "babble")

# noise_fn(noise, n_samples, rng) ➔ tín hiệu ồn dài n_samples (chưa chỉnh mức), cho "babble" và tên file.
NoiseFn = Callable[[str, int, np.random.Generator], np.ndarray]


def distance_gain(distance_m: float) -> float:
    """`gain = REF_DIST_M / max(d, 0.3)`, kẹp ≤ 1.5."""
    return min(config.REF_DIST_M / max(distance_m, MIN_DIST_M), MAX_GAIN)


def power(x: np.ndarray) -> float:
    return float(np.mean(np.square(x, dtype=np.float64))) if x.size else 0.0


def fit_length(x: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """Lặp `x` cho đủ dài rồi cắt `n` mẫu bắt đầu từ vị trí ngẫu nhiên."""
    if x.size == 0:
        return np.zeros(n, dtype=np.float32)
    reps = -(-(n + x.size) // x.size)
    tiled = np.tile(x, reps)
    start = int(rng.integers(0, x.size))
    return tiled[start:start + n].astype(np.float32)


def make_babble(sources: list[np.ndarray], n: int, rng: np.random.Generator) -> np.ndarray:
    """Cộng các clip (mỗi clip dịch thời gian ngẫu nhiên, giảm BABBLE_ATTEN_DB)."""
    if not sources:
        raise ValueError("babble needs at least one source clip")
    atten = 10.0 ** (-BABBLE_ATTEN_DB / 20.0)
    return sum((atten * fit_length(s, n, rng) for s in sources), np.zeros(n, dtype=np.float32))


def render(speech: np.ndarray, distance_m: float, snr_db: float, noise: str, rng: np.random.Generator,
           noise_fn: NoiseFn | None = None) -> tuple[np.ndarray, float]:
    """Trả `(audio, effective_snr_db)`.

    Mức ồn cố định sao cho SNR tại REF_DIST_M bằng `snr_db`; tiếng nói nhân `gain` nên
    `effective_snr_db = snr_db + 20·log10(gain)`. `noise == "none"` ➔ không trộn, SNR = inf.
    """
    speech = np.asarray(speech, dtype=np.float32)
    gain = distance_gain(distance_m)
    voice = speech * np.float32(gain)
    if noise == "none":
        return np.clip(voice, -1.0, 1.0), math.inf
    p_speech = power(speech)
    if p_speech == 0.0:
        raise ValueError("silent speech")
    n = speech.size
    if noise == "white":
        raw = rng.standard_normal(n).astype(np.float32)
    elif noise_fn is None:
        raise ValueError(f"no noise source for {noise!r}")
    else:
        raw = np.asarray(noise_fn(noise, n, rng), dtype=np.float32)
    p_raw = power(raw)
    if p_raw == 0.0:
        raise ValueError(f"silent noise: {noise}")
    target = p_speech / (10.0 ** (snr_db / 10.0))
    mixed = voice + raw * np.float32(math.sqrt(target / p_raw))
    return np.clip(mixed, -1.0, 1.0), snr_db + 20.0 * math.log10(gain)


def measured_snr_db(clean: np.ndarray, mixed: np.ndarray) -> float:
    """SNR đo lại: công suất `clean` so với phần dư `mixed − clean` (dùng trong test và dò lỗi)."""
    return 10.0 * math.log10(power(clean) / power(mixed - clean))
