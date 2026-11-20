"""Test script to verify offline PhoASR-whisper-small model without Hugging Face cache.

Loads model and processor directly from models/PhoASR-whisper-small using local_files_only=True.
Tests transcription on real voice samples (e.g. data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_01_n.m4a
or the converted WAV under src/data/stt/processed/real_voice/wav/).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from stt_paths import ANNOTATIONS_FILE, PROCESSED_WAV_DIR, RAW_DIR, ROOT

MODEL_DIR = ROOT / "models" / "PhoASR-whisper-small"
SPEAKER_A_DIR = Path("Hoàng Tuấn") / "Nam 20 tuổi"  # canonical speaker-A source folder
DEFAULT_WAV = PROCESSED_WAV_DIR / SPEAKER_A_DIR / "A_01_n.wav"
DEFAULT_RAW = RAW_DIR / SPEAKER_A_DIR / "A_01_n.m4a"


def load_audio(path: str | Path, target_sr: int = 16000) -> np.ndarray:
    path = str(path)

    # 1. Try PyAV (handles both raw AAC/m4a with header anomalies and standard formats)
    try:
        import av
        container = av.open(path)
        if container.streams.audio:
            stream = container.streams.audio[0]
            resampler = av.AudioResampler(format="flt", layout="mono", rate=target_sr)
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
                return np.concatenate(pcm_chunks, axis=1)[0].astype(np.float32)
    except ImportError:
        pass
    except Exception:
        pass

    # 2. Try soundfile
    try:
        import soundfile as sf
        audio, sr = sf.read(path, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sr != target_sr:
            import scipy.signal
            num_samples = int(len(audio) * float(target_sr) / sr)
            audio = scipy.signal.resample(audio, num_samples).astype(np.float32)
        return audio
    except Exception as e:
        raise RuntimeError(f"Unable to load audio file {path}: {e}")


def get_ground_truth(audio_path: Path) -> dict | None:
    stem = audio_path.stem
    if not ANNOTATIONS_FILE.exists():
        return None
    try:
        with open(ANNOTATIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("annotations", []):
                if item.get("file_id") == stem:
                    return item
    except Exception:
        pass
    return None


def main() -> None:
    default_target = DEFAULT_WAV if DEFAULT_WAV.exists() else DEFAULT_RAW
    parser = argparse.ArgumentParser(description="Test PhoASR-whisper-small locally on audio sample")
    parser.add_argument("--model-dir", default=str(MODEL_DIR), help="Path to local PhoASR model directory")
    parser.add_argument("--audio", default=str(default_target), help="Path to audio file (.m4a or .wav)")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu", help="Device (cpu or cuda)")
    args = parser.parse_args()

    audio_path = Path(args.audio)
    model_path = Path(args.model_dir)

    print(f"==================================================")
    print(f"PhoASR-whisper-small Local Offline Verification")
    print(f"==================================================")
    print(f"Model path (offline): {model_path}")
    print(f"Audio file:           {audio_path}")
    print(f"Device:               {args.device}")

    if not model_path.exists():
        print(f"ERROR: Model directory does not exist: {model_path}")
        return

    if not audio_path.exists():
        print(f"ERROR: Audio file does not exist: {audio_path}")
        return

    gt_info = get_ground_truth(audio_path)
    if gt_info:
        print(f"\n[Ground Truth Annotation]")
        print(f"  File ID:  {gt_info.get('file_id')}")
        print(f"  Speaker:  {gt_info.get('speaker')}")
        print(f"  Mode:     {gt_info.get('mode_label')}")
        print(f"  Intent:   {gt_info.get('intent')}")
        print(f"  Expected: \"{gt_info.get('text')}\"")

    # Load offline model
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

    print(f"\nLoading processor & model from local directory (local_files_only=True)...")
    t0 = time.time()
    processor = AutoProcessor.from_pretrained(str(model_path), local_files_only=True)
    model = AutoModelForSpeechSeq2Seq.from_pretrained(str(model_path), local_files_only=True).to(args.device)
    load_time = time.time() - t0
    print(f"Loaded successfully in {load_time:.2f}s (NO HuggingFace cache used).")

    # Load audio
    sr = processor.feature_extractor.sampling_rate
    print(f"\nLoading and preprocessing audio (target sample rate: {sr} Hz)...")
    audio = load_audio(audio_path, target_sr=sr)
    print(f"Audio duration: {len(audio) / sr:.2f} seconds")

    # Inference
    t1 = time.time()
    inputs = processor(audio, sampling_rate=sr, return_tensors="pt", return_attention_mask=True)
    input_features = inputs.input_features.to(args.device)
    attention_mask = inputs.attention_mask.to(args.device)

    num_frames = int(attention_mask.sum().item())
    with torch.no_grad():
        outputs = model.generate(
            input_features=input_features,
            attention_mask=attention_mask,
            language="vi",
            task="transcribe",
            return_dict_in_generate=True,
        )

    transcribed_text = processor.batch_decode(outputs["sequences"], skip_special_tokens=True)[0].strip()
    infer_time = time.time() - t1

    print(f"\n[Transcription Result]")
    print(f"  Output text:  \"{transcribed_text}\"")
    print(f"  Inference:    {infer_time:.2f}s")

    if gt_info:
        expected = gt_info.get("text", "")
        # Compare normalized
        def norm(s: str) -> str:
            import re
            return re.sub(r'[^\w\s]', '', s.lower()).strip()

        print(f"  Match exact:      {transcribed_text.lower() == expected.lower()}")
        print(f"  Match normalized: {norm(transcribed_text) == norm(expected)}")


if __name__ == "__main__":
    main()
