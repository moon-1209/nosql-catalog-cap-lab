"""Standalone downloader for Qualcomm-AI-Research/PhoASR-whisper-small.

Downloads all model weights, configs, and tokenizers directly to models/PhoASR-whisper-small
WITHOUT using or creating any Hugging Face cache.
"""

from __future__ import annotations

import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models" / "PhoASR-whisper-small"
REPO_ID = "Qualcomm-AI-Research/PhoASR-whisper-small"
BASE_URL = f"https://huggingface.co/{REPO_ID}/resolve/main"

FILES = [
    ".gitattributes",
    "README.md",
    "added_tokens.json",
    "config.json",
    "generation_config.json",
    "inference.py",
    "merges.txt",
    "model.safetensors",
    "normalizer.json",
    "preprocessor_config.json",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
]


def download_file(filename: str) -> None:
    dest = MODEL_DIR / filename
    temp_dest = MODEL_DIR / f"{filename}.tmp"
    url = f"{BASE_URL}/{filename}"

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        total_size = int(resp.headers.get("Content-Length", 0))

        # Check existing
        if dest.exists() and total_size > 0 and dest.stat().st_size == total_size:
            print(f"[{filename}] already downloaded ({total_size / (1024*1024):.2f} MB). Skipping.")
            return

        print(f"[{filename}] Downloading {total_size / (1024*1024):.2f} MB from {url}...")
        downloaded = 0
        chunk_size = 1024 * 1024  # 1 MB
        t0 = time.time()
        last_log = t0

        with open(temp_dest, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                now = time.time()
                if now - last_log >= 2.0 or downloaded == total_size:
                    last_log = now
                    speed = (downloaded / (now - t0)) / (1024 * 1024) if (now - t0) > 0 else 0
                    pct = (downloaded / total_size) * 100 if total_size > 0 else 0
                    print(f"  -> {pct:5.1f}% ({downloaded/(1024*1024):.1f}/{total_size/(1024*1024):.1f} MB) at {speed:.1f} MB/s", end="\r")

    if temp_dest.exists():
        if dest.exists():
            dest.unlink()
        temp_dest.rename(dest)
    print(f"\n[{filename}] Finished successfully.")


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Starting download of {REPO_ID} to {MODEL_DIR}")
    for idx, fname in enumerate(FILES, 1):
        print(f"\n({idx}/{len(FILES)}) {fname}")
        download_file(fname)

    print(f"\nAll files successfully downloaded directly into {MODEL_DIR}")


if __name__ == "__main__":
    main()
