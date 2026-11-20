"""Gửi một ảnh tới YOLO server và in kết quả (dùng để kiểm chứng G2).

Chạy: python send_image.py <ảnh.jpg> [--url ws://127.0.0.1:8765]
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import sys

import cv2
from websockets.asyncio.client import connect

from protocol import WS_HOST, WS_PORT


async def send(path: str, url: str, frame_id: int) -> dict:
    img = cv2.imread(path)
    if img is None:
        raise SystemExit(f"cannot read image: {path}")
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    assert ok
    msg = {"type": "frame", "frame_id": frame_id, "width": img.shape[1], "height": img.shape[0],
           "jpeg_b64": base64.b64encode(buf.tobytes()).decode("ascii")}
    async with connect(url, max_size=2**24) as ws:
        await ws.send(json.dumps(msg))
        return json.loads(await ws.recv())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("images", nargs="+")
    p.add_argument("--url", default=f"ws://{WS_HOST}:{WS_PORT}")
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    for i, path in enumerate(args.images):
        print(path, json.dumps(asyncio.run(send(path, args.url, i))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
