"""Hằng số Mục 2.1 (G21) phần TTS. Không import torch/transformers: chạy được trong venv riêng `.venv-tts`."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT: Path = Path(os.environ.get("PROJECT_ROOT", str(Path(__file__).resolve().parents[3])))
VIENEU_DIR: Path = PROJECT_ROOT / "models" / "Vie-neu-v3-turbo"
VIENEU_ONNX_SUBDIR: str = "onnx_update"            # fp32 (int8 cần CPU có VNNI, Apple Silicon không có)
MOSS_CODEC_DIR: Path = PROJECT_ROOT / "models" / "MOSS-Audio-Tokenizer-Nano"
MOSS_CODEC_ONNX_DIR: Path = PROJECT_ROOT / "models" / "MOSS-Audio-Tokenizer-Nano-ONNX"
MOSS_CODEC_ONNX_REPO: str = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX"   # tên repo SDK tìm trong cache HF
TTS_CACHE_DIR: Path = Path(os.environ.get("TTS_CACHE_DIR", str(PROJECT_ROOT / "data" / "tts_cache")))
REPORTS_DIR: Path = PROJECT_ROOT / "sim_vision" / "reports"

TTS_WS_HOST: str = "127.0.0.1"
TTS_WS_PORT: int = 8767
TTS_WS_URL: str = f"ws://{TTS_WS_HOST}:{TTS_WS_PORT}"
TTS_TIMEOUT_S: float = 8.0
OUT_SAMPLE_RATE: int = 24000
MAX_TEXT_CHARS: int = 300
TARGET_RMS_DBFS: float = -20.0
PAD_S: float = 0.1
QUEUE_MAX: int = 4

# Giọng robot: TẠM chọn "Ngọc Huyền" (nữ, Bắc, giọng đọc tự nhiên) chờ người dùng nghe reports/voices/ (U4).
ROBOT_VOICE: str = os.environ.get("ROBOT_VOICE", "Ngọc Huyền")
# Đổi model / cách hậu xử lý ➔ đổi chuỗi này để cache cũ không bị dùng lại.
MODEL_VERSION: str = "vieneu-3.8.3/v3turbo/onnx_update-fp32/pp1"
