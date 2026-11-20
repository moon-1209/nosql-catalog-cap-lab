"""YOLO server WebSocket (G2). Nhận `frame`, trả `detections` hoặc `error` (Mục 2.2).

Chạy: python yolo_server.py --model yolov8n.pt [--port 8765]
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from detector import Detector
from protocol import WS_HOST, WS_PORT, ProtocolError, build_detections, build_error, parse_frame

log = logging.getLogger("yolo_server")


async def process_message(text: str | bytes, detector: Detector) -> str:
    """Xử lý một message, luôn trả chuỗi JSON để gửi lại (không ném lỗi giao thức)."""
    try:
        frame_id, img = parse_frame(text)
    except ProtocolError as e:
        log.warning("frame_id=%s error=%s", e.frame_id, e.message)
        return build_error(e.frame_id, e.message)
    dets, infer_ms = await asyncio.to_thread(detector.detect, img)
    log.info("frame_id=%d n_det=%d infer_ms=%.1f", frame_id, len(dets), infer_ms)
    return build_detections(frame_id, dets, infer_ms)


async def handle_connection(ws: ServerConnection, detector: Detector) -> None:
    """Đọc liên tục; chỉ giữ message mới nhất chưa xử lý, các message chờ cũ hơn bị bỏ."""
    latest: list[str | bytes] = []  # tối đa 1 phần tử
    has_new = asyncio.Event()
    closed = asyncio.Event()

    async def reader() -> None:
        try:
            async for msg in ws:
                if latest:
                    log.debug("dropped stale pending message")
                latest[:] = [msg]
                has_new.set()
        except ConnectionClosed:
            pass
        finally:
            closed.set()
            has_new.set()

    reader_task = asyncio.create_task(reader())
    try:
        while True:
            await has_new.wait()
            has_new.clear()
            if not latest:
                if closed.is_set():
                    break
                continue
            msg = latest.pop()
            reply = await process_message(msg, detector)
            try:
                await ws.send(reply)
            except ConnectionClosed:
                break
    finally:
        reader_task.cancel()


async def start_server(detector: Detector, host: str = WS_HOST, port: int = WS_PORT) -> Server:
    return await serve(lambda ws: handle_connection(ws, detector), host, port, max_size=2**24)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="YOLOv8n person detection WebSocket server")
    p.add_argument("--model", default="yolov8n.pt", help="đường dẫn yolov8n.pt (không tự tải)")
    p.add_argument("--port", type=int, default=WS_PORT)
    return p.parse_args(argv)


async def _serve_forever(detector: Detector, port: int) -> None:
    server = await start_server(detector, WS_HOST, port)
    log.info("listening on ws://%s:%d", WS_HOST, port)
    await server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # Kiểm tra trước: ultralytics sẽ tự tải model nếu không thấy file, điều này bị cấm.
    if not os.path.isfile(args.model):
        print(f"ERROR: model file not found: {args.model}", file=sys.stderr)
        return 1
    from detector import YoloDetector

    detector = YoloDetector(args.model)
    log.info("loaded model %s", args.model)
    try:
        asyncio.run(_serve_forever(detector, args.port))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
