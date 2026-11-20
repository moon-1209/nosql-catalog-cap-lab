"""Interface STT (G12) và hai cài đặt: PhoWhisper (model thật) và Fake (cho test)."""

from __future__ import annotations

import logging
from typing import Protocol

import numpy as np

from voice import config

log = logging.getLogger("transcriber")

MAX_AUDIO_S: float = 30.0


class Transcriber(Protocol):
    def transcribe(self, audio: np.ndarray, sr: int, clip_id: str | None = None) -> str:
        """Audio float32 mono ở `sr` ➔ văn bản. `clip_id` chỉ là gợi ý (Fake dùng, model thật bỏ qua)."""
        ...


def check_audio(audio: np.ndarray, sr: int) -> np.ndarray:
    """Kiểm tra 16 kHz, mono, float32; dài hơn 30 s ➔ cắt và cảnh báo."""
    if sr != config.SAMPLE_RATE:
        raise ValueError(f"sample rate must be {config.SAMPLE_RATE}, got {sr}")
    if audio.ndim != 1:
        raise ValueError(f"audio must be mono (1-D), got shape {audio.shape}")
    if audio.dtype != np.float32:
        raise ValueError(f"audio must be float32, got {audio.dtype}")
    limit = int(MAX_AUDIO_S * sr)
    if audio.size > limit:
        log.warning("audio %.1f s > %.0f s, truncated", audio.size / sr, MAX_AUDIO_S)
        audio = audio[:limit]
    return audio


def pick_device(requested: str = "auto") -> str:
    """`auto` ➔ mps nếu có, rồi cuda, rồi cpu."""
    if requested != "auto":
        return requested
    import torch
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class PhoWhisperTranscriber:
    """Whisper (PhoASR-whisper-small) qua transformers, `language="vi"`, `task="transcribe"`."""

    def __init__(self, model_id: str = config.STT_MODEL_ID, device: str = "auto", beams: int = 1) -> None:
        import torch
        from transformers.models.whisper.modeling_whisper import WhisperForConditionalGeneration
        from transformers.models.whisper.processing_whisper import WhisperProcessor

        if not 1 <= beams <= 5:
            raise ValueError("beams must be in 1..5")
        self._torch = torch
        self.device: str = pick_device(device)
        self.beams: int = beams
        self.model_id: str = model_id
        self.processor = WhisperProcessor.from_pretrained(model_id)
        self.model = WhisperForConditionalGeneration.from_pretrained(model_id).to(self.device).eval()
        # Lần chạy đầu trên MPS chậm vài giây (biên dịch kernel) ➔ chạy nháp 1 s im lặng.
        self.transcribe(np.zeros(config.SAMPLE_RATE, dtype=np.float32), config.SAMPLE_RATE)

    def transcribe(self, audio: np.ndarray, sr: int, clip_id: str | None = None) -> str:
        audio = check_audio(audio, sr)
        feats = self.processor(audio, sampling_rate=sr, return_tensors="pt").input_features.to(self.device)
        with self._torch.no_grad():
            ids = self.model.generate(feats, language="vi", task="transcribe", num_beams=self.beams)
        return self.processor.batch_decode(ids, skip_special_tokens=True)[0].strip()


class FakeTranscriber:
    """Trả `text_ref` của clip theo `clip_id` (không gọi model). Đếm số lần gọi."""

    def __init__(self, texts: dict[str, str], default: str = "") -> None:
        self.texts: dict[str, str] = texts
        self.default: str = default
        self.calls: int = 0

    def transcribe(self, audio: np.ndarray, sr: int, clip_id: str | None = None) -> str:
        check_audio(audio, sr)
        self.calls += 1
        return self.texts.get(clip_id or "", self.default)
