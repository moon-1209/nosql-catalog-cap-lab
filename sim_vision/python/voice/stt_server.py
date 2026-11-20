"""STT server WebSocket (G12). Nhận `utterance`, trả `transcript` hoặc `error` (Mục 2.2).

Chạy: python -m voice.stt_server [--device auto|mps|cuda|cpu] [--beams 1] [--port 8766] [--nlu rule|phobert]
Log mức info chỉ có utt_id, clip_id, audio_s, stt_ms (và intent, action của G20) — KHÔNG có văn bản.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import math
import sys
import time
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from voice import audio_sim, config
from voice.transcriber import Transcriber

log = logging.getLogger("stt_server")

QUEUE_MAX: int = 4

# classify(text) ➔ (intent, intent_conf, slots); build(intent, slots) ➔ response.
Classify = Callable[[str], tuple[str, float, dict[str, str]]]
Respond = Callable[[str, dict[str, str]], str]
# G20: (text, trạng thái hội thoại của kết nối) ➔ {intent, intent_conf, slots, response, action, target, ...}.
Dialogue = Callable[[str, dict[str, Any]], dict[str, Any]]


class ProtocolError(Exception):
    def __init__(self, message: str, utt_id: int | None = None) -> None:
        super().__init__(message)
        self.message: str = message
        self.utt_id: int | None = utt_id


@dataclass(frozen=True)
class Utterance:
    utt_id: int
    clip_id: str
    distance_m: float
    snr_db: float
    noise: str


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v: Any) -> bool:
    return (_is_int(v) or isinstance(v, float)) and math.isfinite(v)


def parse_utterance(text: str | bytes) -> Utterance:
    """Kiểm tra message `utterance` theo thứ tự type ➔ utt_id ➔ clip_id ➔ distance_m ➔ snr_db ➔ noise."""
    try:
        msg = json.loads(text)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        raise ProtocolError("invalid json") from None
    if not isinstance(msg, dict):
        raise ProtocolError("invalid json")
    raw_id = msg.get("utt_id")
    utt_id = raw_id if _is_int(raw_id) else None
    checks: list[tuple[str, Callable[[Any], bool]]] = [
        ("type", lambda v: v == "utterance"),
        ("utt_id", _is_int),
        ("clip_id", lambda v: isinstance(v, str) and v != ""),
        ("distance_m", lambda v: _is_num(v) and v >= 0),
        ("snr_db", _is_num),
        ("noise", lambda v: isinstance(v, str) and v != ""),
    ]
    for name, ok in checks:
        if name not in msg:
            raise ProtocolError(f"missing field: {name}", utt_id)
        if not ok(msg[name]):
            raise ProtocolError(f"invalid field: {name}", utt_id)
    return Utterance(msg["utt_id"], msg["clip_id"], float(msg["distance_m"]), float(msg["snr_db"]), msg["noise"])


def build_error(utt_id: int | None, message: str) -> str:
    return json.dumps({"type": "error", "utt_id": utt_id, "message": message}, ensure_ascii=False)


def build_transcript(utt: Utterance, text: str, intent: str | None, intent_conf: float | None,
                     slots: dict[str, str] | None, response: str | None, stt_ms: float, audio_s: float,
                     effective_snr_db: float, action: str | None = None, target: str | None = None) -> str:
    return json.dumps({
        "type": "transcript", "utt_id": utt.utt_id, "clip_id": utt.clip_id, "text": text,
        "intent": intent, "intent_conf": intent_conf, "slots": slots, "response": response,
        "stt_ms": round(stt_ms, 1), "audio_s": round(audio_s, 2),
        # JSON không có inf: noise="none" ➔ null.
        "effective_snr_db": round(effective_snr_db, 2) if math.isfinite(effective_snr_db) else None,
        "action": action, "target": target,
    }, ensure_ascii=False)


def utterance_seed(utt_id: int, clip_id: str) -> int:
    """Seed ổn định giữa các lần chạy (hash() của Python bị ngẫu nhiên hóa cho chuỗi)."""
    return zlib.crc32(f"{utt_id}:{clip_id}".encode())


def read_manifest(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return {r["clip_id"]: r for r in csv.DictReader(f)}


class ClipStore:
    """Đọc wav đã xử lý (có cache) và tạo nguồn ồn cho từng clip."""

    def __init__(self, manifest: dict[str, dict[str, str]], wav_dir: Path, noise_dir: Path) -> None:
        self.manifest = manifest
        self.wav_dir = wav_dir
        self.noise_dir = noise_dir
        self._cache: dict[str, np.ndarray] = {}

    def _load(self, path: Path) -> np.ndarray:
        key = str(path)
        if key not in self._cache:
            audio, sr = sf.read(key, dtype="float32", always_2d=True)
            if sr != config.SAMPLE_RATE:
                raise ValueError(f"{path.name}: sample rate {sr} != {config.SAMPLE_RATE}")
            self._cache[key] = audio.mean(axis=1).astype(np.float32)
        return self._cache[key]

    def speech(self, clip_id: str) -> np.ndarray:
        return self._load(self.wav_dir / f"{clip_id}.wav")

    def has_noise(self, noise: str) -> bool:
        return noise in audio_sim.BUILTIN_NOISES or (self.noise_dir / f"{noise}.wav").is_file()

    def babble_pool(self, clip_id: str) -> list[str]:
        """Clip của người khác; chưa có người khác ➔ clip cùng người nhưng khác câu."""
        me = self.manifest[clip_id]
        others = [c for c, r in self.manifest.items() if r["speaker"] != me["speaker"]]
        return sorted(others or [c for c, r in self.manifest.items() if r["sentence_id"] != me["sentence_id"]])

    def noise_fn(self, clip_id: str) -> audio_sim.NoiseFn:
        def fn(noise: str, n: int, rng: np.random.Generator) -> np.ndarray:
            if noise == "babble":
                pool = self.babble_pool(clip_id)
                k = min(int(rng.integers(audio_sim.BABBLE_MIN, audio_sim.BABBLE_MAX + 1)), len(pool))
                picks = rng.choice(len(pool), size=k, replace=False)
                return audio_sim.make_babble([self.speech(pool[i]) for i in sorted(picks)], n, rng)
            return audio_sim.fit_length(self._load(self.noise_dir / f"{noise}.wav"), n, rng)
        return fn


def load_nlu(mode: str = "rule", device: str = "auto") -> Dialogue | tuple[Classify, Respond] | None:
    """NLU + policy (G20, `mode` rule|phobert); chưa có G20 ➔ intent và câu trả lời G14; không có gì ➔ None (null)."""
    try:
        from nlu.dialogue import build_engine
    except ImportError:
        build_engine = None
    if build_engine is not None:
        return build_engine(mode, device)
    try:
        from voice import intent, responses
    except ImportError:
        return None

    def classify(text: str) -> tuple[str, float, dict[str, str]]:
        r = intent.classify(text)
        return r.intent, r.conf, r.slots

    return classify, responses.build


class SttService:
    """Xử lý một utterance (chạy trong thread). Mọi lỗi ➔ message `error`."""

    def __init__(self, store: ClipStore, transcriber: Transcriber,
                 nlu: Dialogue | tuple[Classify, Respond] | None = None) -> None:
        self.store = store
        self.transcriber = transcriber
        self.nlu = nlu

    def validate(self, utt: Utterance) -> None:
        if utt.clip_id not in self.store.manifest:
            raise ProtocolError(f"clip not found: {utt.clip_id}", utt.utt_id)
        if not self.store.has_noise(utt.noise):
            raise ProtocolError(f"noise not found: {utt.noise}", utt.utt_id)

    def process(self, utt: Utterance, state: dict[str, Any] | None = None) -> str:
        try:
            speech = self.store.speech(utt.clip_id)
            rng = np.random.default_rng(utterance_seed(utt.utt_id, utt.clip_id))
            audio, eff = audio_sim.render(speech, utt.distance_m, utt.snr_db, utt.noise, rng,
                                          self.store.noise_fn(utt.clip_id))
            t0 = time.perf_counter()
            text = self.transcriber.transcribe(audio, config.SAMPLE_RATE, utt.clip_id)
            stt_ms = (time.perf_counter() - t0) * 1000.0
        except Exception as exc:  # noqa: BLE001 — lỗi một utterance không làm dừng server
            log.warning("utt_id=%d clip_id=%s error=%s", utt.utt_id, utt.clip_id, type(exc).__name__)
            return build_error(utt.utt_id, f"stt failed: {type(exc).__name__}")
        intent = conf = slots = response = action = target = None
        if isinstance(self.nlu, tuple):
            intent, conf, slots = self.nlu[0](text)
            response = self.nlu[1](intent, slots)
        elif self.nlu is not None:
            d = self.nlu(text, state if state is not None else {})
            intent, conf, slots, response, action, target = (d["intent"], d["intent_conf"], d["slots"], d["response"],
                                                             d["action"], d["target"])
        audio_s = audio.size / config.SAMPLE_RATE
        log.info("utt_id=%d clip_id=%s audio_s=%.2f stt_ms=%.1f", utt.utt_id, utt.clip_id, audio_s, stt_ms)
        return build_transcript(utt, text, intent, conf, slots, response, stt_ms, audio_s, eff, action, target)


@dataclass
class _Job:
    utt: Utterance
    ws: ServerConnection
    state: dict[str, Any]


class SttServer:
    """Một worker dùng chung model; hàng chờ tối đa QUEUE_MAX utterance (không tính cái đang chạy)."""

    def __init__(self, service: SttService, queue_max: int = QUEUE_MAX) -> None:
        self.service = service
        self.queue: asyncio.Queue[_Job] = asyncio.Queue(maxsize=queue_max)
        self._worker: asyncio.Task[None] | None = None

    async def _work(self) -> None:
        while True:
            job = await self.queue.get()
            reply = await asyncio.to_thread(self.service.process, job.utt, job.state)
            try:
                await job.ws.send(reply)
            except ConnectionClosed:
                pass
            self.queue.task_done()

    async def handle_message(self, text: str | bytes, ws: ServerConnection,
                             state: dict[str, Any] | None = None) -> str | None:
        """Trả lỗi cần gửi ngay, hoặc None nếu đã xếp hàng."""
        try:
            utt = parse_utterance(text)
            self.service.validate(utt)
        except ProtocolError as e:
            log.warning("utt_id=%s error=%s", e.utt_id, e.message)
            return build_error(e.utt_id, e.message)
        try:
            self.queue.put_nowait(_Job(utt, ws, state if state is not None else {}))
        except asyncio.QueueFull:
            log.warning("utt_id=%d error=stt busy", utt.utt_id)
            return build_error(utt.utt_id, "stt busy")
        return None

    async def handle_connection(self, ws: ServerConnection) -> None:
        state: dict[str, Any] = {}            # trạng thái hội thoại G20 (clarify_count, last_response) của kết nối
        try:
            async for msg in ws:
                reply = await self.handle_message(msg, ws, state)
                if reply is not None:
                    await ws.send(reply)
        except ConnectionClosed:
            pass

    async def start(self, host: str = config.STT_WS_HOST, port: int = config.STT_WS_PORT) -> Server:
        self._worker = asyncio.create_task(self._work())
        return await serve(self.handle_connection, host, port)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PhoASR-whisper-small STT WebSocket server")
    p.add_argument("--model", default=config.STT_MODEL_ID)
    p.add_argument("--device", default="auto", choices=["auto", "mps", "cuda", "cpu"])
    p.add_argument("--beams", type=int, default=1, choices=range(1, 6))
    p.add_argument("--port", type=int, default=config.STT_WS_PORT)
    p.add_argument("--data-dir", type=Path, default=config.DATA_DIR)
    p.add_argument("--nlu", default="rule", choices=["rule", "phobert"], help="G20: luật G14 hoặc PhoBERT (G19)")
    return p.parse_args(argv)


async def _serve_forever(server: SttServer, port: int) -> None:
    ws_server = await server.start(config.STT_WS_HOST, port)
    log.info("listening on ws://%s:%d", config.STT_WS_HOST, port)
    await ws_server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    manifest_path = config.manifest_path(args.data_dir)
    if not manifest_path.is_file():
        print(f"ERROR: {manifest_path} not found: run `python -m voice.prepare_data` (G11) first", file=sys.stderr)
        return 1
    if not Path(args.model).is_dir():
        print(f"ERROR: model directory not found: {args.model}", file=sys.stderr)
        return 1
    from voice.transcriber import PhoWhisperTranscriber

    log.info("Loading STT model (%s)...", Path(args.model).name)
    store = ClipStore(read_manifest(manifest_path), config.wav_dir(args.data_dir), args.data_dir / "noise")
    transcriber = PhoWhisperTranscriber(args.model, args.device, args.beams)
    log.info("model %s on device=%s beams=%d, %d clips", Path(args.model).name, transcriber.device,
             args.beams, len(store.manifest))
    nlu = load_nlu(args.nlu, args.device)
    log.info("nlu=%s", args.nlu if not isinstance(nlu, tuple) else "rule (G14, no policy)")
    if nlu is None:
        log.warning("intent module not available: intent/response = null")
    try:
        asyncio.run(_serve_forever(SttServer(SttService(store, transcriber, nlu)), args.port))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
