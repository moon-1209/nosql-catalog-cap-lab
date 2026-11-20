"""Hằng số Mục 2.1 (G18–G23) phần NLU. Đường dẫn đọc từ biến môi trường nếu có."""

from __future__ import annotations

import os
from pathlib import Path

from voice import config as voice_config
from voice.intent import INTENTS as RULE_INTENTS

PROJECT_ROOT: Path = Path(os.environ.get("PROJECT_ROOT", str(Path(__file__).resolve().parents[3])))
PHOBERT_DIR: Path = PROJECT_ROOT / "models" / "PhoBert-base-v2"
PHOBERT_FT_DIR: Path = PROJECT_ROOT / "models_finetuned" / "phobert-intent"
# RDRSegmenter (VnCoreNLP-1.2.jar + models/wordsegmenter), tải 2026-10-22 theo lựa chọn của người dùng.
VNCORENLP_DIR: Path = Path(os.environ.get("VNCORENLP_DIR", str(PROJECT_ROOT / "models" / "VnCoreNLP")))
# openjdk@17 qua Homebrew (keg-only, không có trong PATH); pyjnius cần JAVA_HOME trỏ tới thư mục Home.
DEFAULT_JAVA_HOME: str = "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"

NLU_DATA_DIR: Path = voice_config.DATA_DIR / "nlu"
REPORTS_DIR: Path = PROJECT_ROOT / "sim_vision" / "reports"

MAX_SEQ_LEN: int = 64
CONF_THRESHOLD_DEFAULT: float = 0.6
MAX_CLARIFY: int = 2
SEED: int = 42

# Mục 2.2: 19 intent của kịch bản (Mục 6 thiếu ho_tro_di_chuyen; người dùng chọn giữ, 2026-10-22) + unknown.
# Thứ tự nhãn cố định theo chữ cái (G19).
INTENTS: tuple[str, ...] = tuple(sorted(RULE_INTENTS))
assert len(INTENTS) == 20
