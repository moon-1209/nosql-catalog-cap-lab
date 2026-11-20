"""Fixture chung cho test voice: thư mục dữ liệu giả với file sóng sin."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from voice import config

MINI_SCRIPT = """
| Mã | Câu | Intent |
| :-- | :-- | :-- |
| A_07 | Phòng khám số 205 đi đường nào? | hoi_phong |
| A_25 | Bố mình đang khó thở quá, gọi bác sĩ giúp mình với! | cap_cuu |

| Mã | Câu | Intent |
| :-- | :-- | :-- |
| C03 | Phòng xét nghiệm máu đi đường nào? | hoi_phong |
"""


def tone(seconds: float, sr: int = 44100, lead_s: float = 0.5, channels: int = 2, amp: float = 0.3) -> np.ndarray:
    """Im lặng `lead_s` + sin 440 Hz `seconds` + im lặng `lead_s`."""
    t = np.arange(int(seconds * sr)) / sr
    sig = (amp * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    pad = np.zeros(int(lead_s * sr), dtype=np.float32)
    mono = np.concatenate([pad, sig, pad])
    return np.stack([mono] * channels, axis=1) if channels > 1 else mono


def write_tone(path: Path, seconds: float = 1.0, **kw) -> Path:
    sr = kw.pop("sr", 44100)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), tone(seconds, sr=sr, **kw), sr)
    return path


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """data/raw/real_voice với vài file hợp lệ, một file sai tên, một file quá ngắn."""
    d = tmp_path / "data"
    raw = d / config.RAW_SUBDIR
    write_tone(raw / "A_07_r.wav")
    write_tone(raw / "A_07_n.wav", seconds=1.5)
    write_tone(raw / "A_25_r.wav")
    write_tone(raw / "Nam_C03.wav")
    write_tone(raw / "ghi_am_moi.wav")
    write_tone(raw / "A_25_n.wav", seconds=0.05, lead_s=0.0)
    write_tone(raw / "A_99_r.wav")
    return d


@pytest.fixture
def script_md(tmp_path: Path) -> Path:
    p = tmp_path / "kich_ban.md"
    p.write_text(MINI_SCRIPT, encoding="utf-8")
    return p
