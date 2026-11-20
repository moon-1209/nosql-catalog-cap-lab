"""Engine TTS (G21): VieneuEngine (VieNeu-TTS v3 Turbo, ONNX/CPU, chỉ đọc model local), FakeTTS cho test,
hậu xử lý về PCM 16-bit 24 kHz và cache theo sha1(văn bản + giọng + phiên bản model).

Nạp local (đọc mã nguồn vieneu 3.8.3, xem ASSUMPTIONS G21):
- Model: `Vieneu(mode="v3turbo", backend="onnx", backbone_repo=VIENEU_DIR, onnx_dir=VIENEU_DIR/onnx_update)`.
- Codec: engine ONNX có `codec_dir` nhưng `V3TurboVieNeuTTS` không chuyển tham số này xuống ➔ dựng thư mục cache
  Hugging Face (symlink tới MOSS_CODEC_ONNX_DIR) và đặt HF_HUB_CACHE + HF_HUB_OFFLINE=1 trước khi import vieneu.
"""

from __future__ import annotations

import hashlib
import os
import threading
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
import soundfile as sf

from tts import config
from tts.text_for_tts import text_for_tts


class TTSEngine(Protocol):
    def synth(self, text: str, voice: str) -> tuple[np.ndarray, int]:
        """Âm thanh mono float32 và tần số lấy mẫu gốc."""

    def voices(self) -> list[str]:
        """id các giọng có sẵn."""


class FakeTTS:
    """Sóng sin 220 Hz, dài tỉ lệ số ký tự (1/15 s mỗi ký tự). Đếm số lần gọi."""

    def __init__(self, sample_rate: int = 48000, voices: list[str] | None = None, delay_s: float = 0.0) -> None:
        self.sample_rate = sample_rate
        self._voices = voices or [config.ROBOT_VOICE]
        self.delay_s = delay_s
        self.calls = 0
        self.gate: threading.Event | None = None

    def synth(self, text: str, voice: str) -> tuple[np.ndarray, int]:
        self.calls += 1
        if self.gate is not None:
            self.gate.wait(5)
        if self.delay_s:
            time.sleep(self.delay_s)
        n = int(len(text) / 15 * self.sample_rate)
        t = np.arange(n) / self.sample_rate
        return (0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32), self.sample_rate

    def voices(self) -> list[str]:
        return list(self._voices)


def prepare_codec_cache(codec_dir: Path, cache_root: Path, repo: str = config.MOSS_CODEC_ONNX_REPO) -> Path:
    """Thư mục cache HF dạng models--org--name/{refs/main, snapshots/local/<symlink>} trỏ tới codec local."""
    missing = [f for f in ("moss_audio_tokenizer_decode_full.onnx", "moss_audio_tokenizer_encode.onnx")
               if not (codec_dir / f).is_file()]
    if missing:
        raise FileNotFoundError(f"codec files missing in {codec_dir}: {missing}")
    repo_dir = cache_root / ("models--" + repo.replace("/", "--"))
    snap = repo_dir / "snapshots" / "local"
    snap.mkdir(parents=True, exist_ok=True)
    (repo_dir / "refs").mkdir(exist_ok=True)
    (repo_dir / "refs" / "main").write_text("local", encoding="utf-8")
    for f in codec_dir.iterdir():
        if f.is_dir() or f.name.startswith("."):
            continue
        link = snap / f.name
        if link.is_symlink() or link.exists():
            if link.resolve() == f.resolve():
                continue
            link.unlink()
        try:
            link.symlink_to(f.resolve())
        except OSError:
            import shutil
            shutil.copy2(f, link)
    return cache_root


class VieneuEngine:
    """VieNeu-TTS v3 Turbo trên ONNX/CPU, chỉ đọc từ thư mục local. Phải tạo trước khi huggingface_hub được import."""

    def __init__(self, vieneu_dir: Path = config.VIENEU_DIR, codec_onnx_dir: Path = config.MOSS_CODEC_ONNX_DIR,
                 cache_root: Path = config.TTS_CACHE_DIR / "hf_hub", threads: int = 0) -> None:
        onnx_dir = vieneu_dir / config.VIENEU_ONNX_SUBDIR
        if not (onnx_dir / "vieneu_prefill.onnx").is_file():
            raise FileNotFoundError(f"VieNeu ONNX graphs not found in {onnx_dir}")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["HF_HUB_CACHE"] = str(prepare_codec_cache(codec_onnx_dir, cache_root))
        import huggingface_hub.constants as hfc

        if Path(hfc.HF_HUB_CACHE) != cache_root or not hfc.HF_HUB_OFFLINE:
            raise RuntimeError("huggingface_hub đã được import trước VieneuEngine: HF_HUB_CACHE/HF_HUB_OFFLINE "
                               "không có hiệu lực (tạo VieneuEngine trước mọi import khác dùng huggingface_hub)")
        from vieneu import Vieneu

        self.tts = Vieneu(mode="v3turbo", backend="onnx", backbone_repo=str(vieneu_dir), onnx_dir=str(onnx_dir),
                          threads=threads)
        self.sample_rate: int = int(self.tts.sample_rate)

    def synth(self, text: str, voice: str) -> tuple[np.ndarray, int]:
        audio = self.tts.infer(text, voice=voice)
        return np.asarray(audio, dtype=np.float32).reshape(-1), self.sample_rate

    def voices(self) -> list[str]:
        return [vid for _, vid in self.tts.list_preset_voices()]

    def voice_labels(self) -> list[tuple[str, str]]:
        return list(self.tts.list_preset_voices())


def rms_dbfs(x: np.ndarray) -> float:
    r = float(np.sqrt(np.mean(np.square(x, dtype=np.float64)))) if x.size else 0.0
    return 20 * np.log10(r) if r > 0 else float("-inf")


def postprocess(audio: np.ndarray, sr: int, out_sr: int = config.OUT_SAMPLE_RATE,
                target_dbfs: float = config.TARGET_RMS_DBFS, pad_s: float = config.PAD_S) -> bytes:
    """Resample ➔ chuẩn hóa RMS ➔ thêm im lặng đầu/cuối ➔ kẹp [−1, 1] ➔ PCM 16-bit little-endian."""
    x = np.asarray(audio, dtype=np.float32).reshape(-1)
    if x.size == 0:
        raise ValueError("empty audio")
    if sr != out_sr:
        import soxr

        x = soxr.resample(x, sr, out_sr).astype(np.float32)
    level = rms_dbfs(x)
    if np.isfinite(level):
        x = x * np.float32(10 ** ((target_dbfs - level) / 20))
    pad = np.zeros(int(round(pad_s * out_sr)), dtype=np.float32)
    x = np.clip(np.concatenate([pad, x, pad]), -1.0, 1.0)
    return (x * 32767.0).round().astype("<i2").tobytes()


def cache_key(text: str, voice: str, model_version: str = config.MODEL_VERSION) -> str:
    return hashlib.sha1((unicodedata.normalize("NFC", text) + voice + model_version).encode("utf-8")).hexdigest()


class TtsCache:
    """File .wav PCM 16-bit 24 kHz theo key."""

    def __init__(self, directory: Path = config.TTS_CACHE_DIR, sample_rate: int = config.OUT_SAMPLE_RATE) -> None:
        self.dir = directory
        self.sample_rate = sample_rate

    def path(self, key: str) -> Path:
        return self.dir / f"{key}.wav"

    def get(self, key: str) -> bytes | None:
        p = self.path(key)
        if not p.is_file():
            return None
        data, sr = sf.read(str(p), dtype="int16")
        if sr != self.sample_rate:
            return None
        return np.asarray(data, dtype="<i2").reshape(-1).tobytes()

    def put(self, key: str, pcm: bytes) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.path(key).with_suffix(".tmp.wav")
        sf.write(str(tmp), np.frombuffer(pcm, dtype="<i2"), self.sample_rate, subtype="PCM_16")
        tmp.replace(self.path(key))


@dataclass(frozen=True)
class Speech:
    pcm16: bytes
    sample_rate: int
    duration_s: float
    tts_ms: float
    cache_hit: bool


class Synthesizer:
    """Chuẩn hóa văn bản ➔ cache ➔ (miss) engine + hậu xử lý ➔ lưu cache. An toàn khi gọi từ một worker thread."""

    def __init__(self, engine: TTSEngine, cache: TtsCache, model_version: str = config.MODEL_VERSION) -> None:
        self.engine = engine
        self.cache = cache
        self.model_version = model_version

    def speak(self, text: str, voice: str) -> Speech:
        t0 = time.perf_counter()
        spoken = text_for_tts(text)
        key = cache_key(spoken, voice, self.model_version)
        pcm = self.cache.get(key)
        hit = pcm is not None
        if pcm is None:
            audio, sr = self.engine.synth(spoken, voice)
            pcm = postprocess(audio, sr, self.cache.sample_rate)
            self.cache.put(key, pcm)
        tts_ms = (time.perf_counter() - t0) * 1000.0
        return Speech(pcm, self.cache.sample_rate, len(pcm) / 2 / self.cache.sample_rate, tts_ms, hit)
