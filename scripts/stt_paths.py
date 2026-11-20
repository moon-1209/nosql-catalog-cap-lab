"""Centralized, repository-root-relative paths for the STT data pipeline.

Used by scripts/convert_audio.py, scripts/evaluate_asr.py and scripts/test_asr.py.
Importable because scripts/ is on sys.path when those scripts run directly.

Layout:
  raw originals : data/raw/real_voice/<Drive hierarchy>
  annotations   : data/annotations.json (canonical ground truth, unchanged)
  processed wavs: src/data/stt/processed/real_voice/wav/<mirrored hierarchy>
  manifests     : src/data/stt/manifests/
  eval outputs  : src/data/stt/evaluation/{predictions,metrics,error_analysis}/
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw" / "real_voice"
ANNOTATIONS_FILE = ROOT / "data" / "annotations.json"
ANNOTATIONS_CSV = ROOT / "data" / "annotations.csv"

STT_ROOT = ROOT / "src" / "data" / "stt"
PROCESSED_WAV_DIR = STT_ROOT / "processed" / "real_voice" / "wav"
MANIFESTS_DIR = STT_ROOT / "manifests"
EVAL_DIR = STT_ROOT / "evaluation"
PREDICTIONS_DIR = EVAL_DIR / "predictions"
METRICS_DIR = EVAL_DIR / "metrics"
ERROR_ANALYSIS_DIR = EVAL_DIR / "error_analysis"

AUDIO_SUFFIXES = (".m4a", ".wav", ".mp3", ".flac", ".ogg")

# Canonical source folders for benchmark file_ids when the same filename
# exists in multiple Drive folders (e.g. child re-recordings in "Trẻ con").
BENCHMARK_SOURCE_DIRS = (
    "Hoàng Tuấn/Nam 20 tuổi",
    "Phương Uyên/Nữ 20 tuổi",
)
