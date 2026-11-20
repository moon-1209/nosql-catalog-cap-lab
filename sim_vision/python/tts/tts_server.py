"""TTS server WebSocket (G21). Nhận `speak`, trả `audio` hoặc `error` (Mục 2.5).

Chạy (venv riêng có gói vieneu): .venv-tts/bin/python -m tts.tts_server [--port 8767] [--voice "Ngọc Huyền"]
Log info chỉ có utt_id, độ dài text, tts_ms, cache_hit — KHÔNG có nội dung text.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from tts import config
from tts.tts_engine import Speech, Synthesizer, TTSEngine, TtsCache

log = logging.getLogger("tts_server")


class ProtocolError(Exception):
    def __init__(self, message: str, utt_id: int | None = None) -> None:
        super().__init__(message)
        self.message: str = message
        self.utt_id: int | None = utt_id


@dataclass(frozen=True)
class SpeakRequest:
    utt_id: int
    text: str
    voice: str


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def parse_speak(text: str | bytes, voices: set[str] | None = None) -> SpeakRequest:
    """Kiểm tra theo thứ tự type ➔ utt_id ➔ text ➔ voice; text rỗng / > MAX_TEXT_CHARS; giọng không có."""
    try:
        msg = json.loads(text)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        raise ProtocolError("invalid json") from None
    if not isinstance(msg, dict):
        raise ProtocolError("invalid json")
    utt_id = msg.get("utt_id") if _is_int(msg.get("utt_id")) else None
    checks: list[tuple[str, Callable[[Any], bool]]] = [
        ("type", lambda v: v == "speak"),
        ("utt_id", _is_int),
        ("text", lambda v: isinstance(v, str)),
        ("voice", lambda v: isinstance(v, str) and v != ""),
    ]
    for name, ok in checks:
        if name not in msg:
            raise ProtocolError(f"missing field: {name}", utt_id)
        if not ok(msg[name]):
            raise ProtocolError(f"invalid field: {name}", utt_id)
    body = msg["text"].strip()
    if body == "":
        raise ProtocolError("text empty", utt_id)
    if len(body) > config.MAX_TEXT_CHARS:
        raise ProtocolError("text too long", utt_id)
    if voices is not None and msg["voice"] not in voices:
        raise ProtocolError(f"voice not found: {msg['voice']}", utt_id)
    return SpeakRequest(msg["utt_id"], body, msg["voice"])


def build_error(utt_id: int | None, message: str) -> str:
    return json.dumps({"type": "error", "utt_id": utt_id, "message": message}, ensure_ascii=False)


def build_audio(utt_id: int, s: Speech) -> str:
    return json.dumps({
        "type": "audio", "utt_id": utt_id, "sample_rate": s.sample_rate, "channels": 1,
        "pcm16_b64": base64.b64encode(s.pcm16).decode("ascii"), "duration_s": round(s.duration_s, 3),
        "tts_ms": round(s.tts_ms, 1), "cache_hit": s.cache_hit,
    })


class TtsService:
    def __init__(self, synth: Synthesizer) -> None:
        self.synth = synth
        self.voices: set[str] = set(synth.engine.voices())

    def process(self, req: SpeakRequest) -> str:
        try:
            s = self.synth.speak(req.text, req.voice)
        except Exception as exc:  # noqa: BLE001 — lỗi một câu không làm dừng server
            log.warning("utt_id=%d error=%s", req.utt_id, type(exc).__name__)
            return build_error(req.utt_id, f"tts failed: {type(exc).__name__}")
        log.info("utt_id=%d text_len=%d tts_ms=%.1f cache_hit=%s", req.utt_id, len(req.text), s.tts_ms, s.cache_hit)
        return build_audio(req.utt_id, s)


@dataclass
class _Job:
    req: SpeakRequest
    ws: ServerConnection


class TtsServer:
    """Một worker (thread) dùng chung model; hàng chờ tối đa QUEUE_MAX (không tính câu đang tổng hợp)."""

    def __init__(self, service: TtsService, queue_max: int = config.QUEUE_MAX) -> None:
        self.service = service
        self.queue: asyncio.Queue[_Job] = asyncio.Queue(maxsize=queue_max)
        self._worker: asyncio.Task[None] | None = None

    async def _work(self) -> None:
        while True:
            job = await self.queue.get()
            reply = await asyncio.to_thread(self.service.process, job.req)
            try:
                await job.ws.send(reply)
            except ConnectionClosed:
                pass
            self.queue.task_done()

    async def handle_message(self, text: str | bytes, ws: ServerConnection) -> str | None:
        try:
            req = parse_speak(text, self.service.voices)
        except ProtocolError as e:
            log.warning("utt_id=%s error=%s", e.utt_id, e.message)
            return build_error(e.utt_id, e.message)
        try:
            self.queue.put_nowait(_Job(req, ws))
        except asyncio.QueueFull:
            log.warning("utt_id=%d error=tts busy", req.utt_id)
            return build_error(req.utt_id, "tts busy")
        return None

    async def handle_connection(self, ws: ServerConnection) -> None:
        try:
            async for msg in ws:
                reply = await self.handle_message(msg, ws)
                if reply is not None:
                    await ws.send(reply)
        except ConnectionClosed:
            pass

    async def start(self, host: str = config.TTS_WS_HOST, port: int = config.TTS_WS_PORT) -> Server:
        self._worker = asyncio.create_task(self._work())
        # Câu trả lời ~3–6 s âm thanh 24 kHz ➔ ~300 KB base64; nới giới hạn mặc định (1 MiB) cho chắc.
        return await serve(self.handle_connection, host, port, max_size=8 * 2**20)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="VieNeu-TTS v3 Turbo WebSocket server (G21)")
    p.add_argument("--port", type=int, default=config.TTS_WS_PORT)
    p.add_argument("--voice", default=config.ROBOT_VOICE, help="giọng robot phải có trong list_preset_voices()")
    p.add_argument("--fake", action="store_true", help="FakeTTS (sóng sin), không nạp model")
    return p.parse_args(argv)


async def _serve_forever(server: TtsServer, port: int) -> None:
    ws_server = await server.start(config.TTS_WS_HOST, port)
    log.info("listening on ws://%s:%d", config.TTS_WS_HOST, port)
    await ws_server.serve_forever()


def build_engine(fake: bool) -> TTSEngine:
    if fake:
        from tts.tts_engine import FakeTTS

        return FakeTTS()
    from tts.tts_engine import VieneuEngine

    return VieneuEngine()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        engine = build_engine(args.fake)
    except (FileNotFoundError, RuntimeError, ImportError) as e:
        print(f"ERROR: không nạp được TTS từ local: {e}", file=sys.stderr)
        return 1
    voices = engine.voices()
    if args.voice not in voices:
        print(f"ERROR: ROBOT_VOICE '{args.voice}' không có trong list_preset_voices(): {voices}", file=sys.stderr)
        return 1
    model_version = "fake" if args.fake else config.MODEL_VERSION
    service = TtsService(Synthesizer(engine, TtsCache(config.TTS_CACHE_DIR), model_version))
    log.info("tts ready: %s, voice=%s, %d voices, cache=%s", "fake" if args.fake else "vieneu v3 turbo onnx",
             args.voice, len(voices), config.TTS_CACHE_DIR)
    try:
        asyncio.run(_serve_forever(TtsServer(service), args.port))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
