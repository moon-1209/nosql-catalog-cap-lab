"""Convert raw audio recordings (e.g. .m4a, .mp3, arbitrary .wav)
into standardized 16kHz mono WAV for Whisper / PhoASR speech recognition.

Standard ASR Audio Specs:
  - Format: WAV (RIFF header, PCM 16-bit)
  - Sample Rate: 16,000 Hz (16 kHz)
  - Channels: 1 (Mono)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from stt_paths import AUDIO_SUFFIXES, PROCESSED_WAV_DIR, RAW_DIR

PROCESSED_DIR = PROCESSED_WAV_DIR


def convert_file(src_path: Path, dest_path: Path, target_sr: int = 16000) -> bool:
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. PyAV (av) - packet-level demuxer with bad-packet tolerance
    try:
        import av
        import numpy as np
        import soundfile as sf

        container = av.open(str(src_path))
        if not container.streams.audio:
            print(f"No audio stream in {src_path.name}")
            return False

        stream = container.streams.audio[0]
        resampler = av.AudioResampler(format="s16", layout="mono", rate=target_sr)

        pcm_chunks = []
        for packet in container.demux(stream):
            try:
                frames = packet.decode()
                for frame in frames:
                    for rf in resampler.resample(frame):
                        pcm_chunks.append(rf.to_ndarray())
            except Exception:
                continue

        if pcm_chunks:
            audio_data = np.concatenate(pcm_chunks, axis=1)[0]
            sf.write(str(dest_path), audio_data, target_sr, subtype="PCM_16")
            duration = len(audio_data) / target_sr
            print(f"Converted [av]: {src_path.name} -> {dest_path.name} ({duration:.2f}s)")
            return True
    except ImportError:
        pass
    except Exception as e:
        print(f"PyAV conversion failed for {src_path.name}: {e}")

    # 2. Try soundfile
    try:
        import numpy as np
        import soundfile as sf

        audio, sr = sf.read(str(src_path))
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sr != target_sr:
            import scipy.signal
            num_samples = int(len(audio) * float(target_sr) / sr)
            audio = scipy.signal.resample(audio, num_samples)
        sf.write(str(dest_path), audio.astype(np.int16), target_sr, subtype="PCM_16")
        print(f"Converted [soundfile]: {src_path.name} -> {dest_path.name}")
        return True
    except Exception:
        pass

    print(f"ERROR: No suitable audio backend found to convert {src_path}.")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert raw audio to standard 16kHz mono WAV")
    parser.add_argument("--src", default=str(RAW_DIR), help="Source directory containing raw audio")
    parser.add_argument("--dest", default=str(PROCESSED_DIR), help="Destination directory for processed wavs")
    args = parser.parse_args()

    src_dir = Path(args.src)
    dest_dir = Path(args.dest)

    if not src_dir.exists():
        print(f"Source directory does not exist: {src_dir}")
        return

    raw_files = sorted(f for f in src_dir.rglob("*")
                       if f.is_file() and f.suffix.lower() in AUDIO_SUFFIXES)
    print(f"Found {len(raw_files)} audio file(s) in {src_dir}")

    # Two sources sharing a stem in the same folder (e.g. X.m4a + X.wav)
    # would map to the same output name; keep the source extension for the
    # non-.wav variant so nothing is silently overwritten.
    rels = {f: f.relative_to(src_dir) for f in raw_files}
    import unicodedata
    out_count: dict[str, int] = {}
    for rel in rels.values():
        key = unicodedata.normalize("NFC", rel.with_suffix(".wav").as_posix())
        out_count[key] = out_count.get(key, 0) + 1

    for f in raw_files:
        rel = rels[f]
        out_rel = rel.with_suffix(".wav")
        if out_count[unicodedata.normalize("NFC", out_rel.as_posix())] > 1 and f.suffix.lower() != ".wav":
            out_rel = rel.with_name(f"{rel.name}.wav")
        convert_file(f, dest_dir / out_rel)


if __name__ == "__main__":
    main()
