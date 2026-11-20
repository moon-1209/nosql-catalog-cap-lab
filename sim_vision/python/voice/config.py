"""Hằng số Mục 2.1 (bản Python). Đường dẫn đọc từ biến môi trường nếu có."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[3]

DATA_DIR: Path = Path(os.environ.get("DATA_DIR", str(REPO_ROOT / "data")))
# Dữ liệu thật nằm ở data/raw/real_voice (người dùng chọn 2026-10-21, khác Mục 2.4).
RAW_SUBDIR: str = "raw/real_voice"
SCRIPT_MD: Path = REPO_ROOT / "docs" / "kich_ban_thu_am.md"

STT_WS_HOST: str = "127.0.0.1"
STT_WS_PORT: int = 8766
STT_WS_URL: str = f"ws://{STT_WS_HOST}:{STT_WS_PORT}"
# Model local Qualcomm PhoASR-whisper-small (người dùng chọn thay vinai/PhoWhisper-small).
STT_MODEL_ID: str = os.environ.get("STT_MODEL_ID", str(REPO_ROOT / "models" / "PhoASR-whisper-small"))
SAMPLE_RATE: int = 16000

TALK_TRIGGER_DIST: float = 2.0
TURN_DURATION_S: float = 0.6
STT_TIMEOUT_S: float = 10.0
NPC_COOLDOWN_S: float = 8.0
MAX_TURNS: int = 1
SUBTITLE_S: float = 4.0
REF_DIST_M: float = 1.0
DEFAULT_SNR_DB: float = 20.0


def processed_dir(data_dir: Path | None = None) -> Path:
    return (data_dir or DATA_DIR) / "processed"


def manifest_path(data_dir: Path | None = None) -> Path:
    return processed_dir(data_dir) / "manifest.csv"


def wav_dir(data_dir: Path | None = None) -> Path:
    return processed_dir(data_dir) / "wav"
