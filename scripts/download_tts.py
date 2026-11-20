"""Download TTS models: VieNeu-TTS v3 Turbo ONNX and MOSS-Audio-Tokenizer-Nano-ONNX.

Downloads directly to models/ directory for offline use.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"


def download_moss_tokenizer() -> None:
    dest = MODELS_DIR / "MOSS-Audio-Tokenizer-Nano-ONNX"
    dest.mkdir(parents=True, exist_ok=True)
    print(f"\n[1/2] Downloading MOSS-Audio-Tokenizer-Nano-ONNX to {dest}...")
    t0 = time.time()
    snapshot_download(
        repo_id="OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX",
        local_dir=str(dest),
        max_workers=4,
    )
    print(f" -> MOSS tokenizer downloaded in {time.time() - t0:.1f}s")


def download_vieneu_tts() -> None:
    dest = MODELS_DIR / "Vie-neu-v3-turbo"
    dest.mkdir(parents=True, exist_ok=True)
    print(f"\n[2/2] Downloading VieNeu-TTS-v3-Turbo (ONNX & Configs) to {dest}...")
    t0 = time.time()
    # Exclude *.gguf model files (only need ONNX + voices + configs)
    patterns = [
        "config.json",
        "special_tokens_map.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "onnx_update/*",
        "gguf/voices/**",
    ]
    snapshot_download(
        repo_id="pnnbao-ump/VieNeu-TTS-v3-Turbo",
        local_dir=str(dest),
        allow_patterns=patterns,
        max_workers=4,
    )
    print(f" -> VieNeu TTS downloaded in {time.time() - t0:.1f}s")


def main() -> None:
    print("=" * 60)
    print("Starting TTS Model Download (~2.1 GB total)")
    print("=" * 60)
    download_moss_tokenizer()
    download_vieneu_tts()
    print("\n" + "=" * 60)
    print("All TTS models successfully downloaded into models/!")
    print("=" * 60)


if __name__ == "__main__":
    main()
