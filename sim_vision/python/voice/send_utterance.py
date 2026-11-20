"""Gửi thử một `utterance` tới STT server và in kết quả (kiểm chứng G12).

Chạy: python -m voice.send_utterance A_07_r [--distance 1] [--snr 20] [--noise none] [--utt-id 1]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from websockets.asyncio.client import connect

from voice import config


async def send(url: str, msg: dict, timeout_s: float) -> dict:
    async with connect(url) as ws:
        await ws.send(json.dumps(msg))
        return json.loads(await asyncio.wait_for(ws.recv(), timeout_s))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("clip_id")
    p.add_argument("--distance", type=float, default=1.0)
    p.add_argument("--snr", type=float, default=config.DEFAULT_SNR_DB)
    p.add_argument("--noise", default="none")
    p.add_argument("--utt-id", type=int, default=1)
    p.add_argument("--url", default=config.STT_WS_URL)
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    msg = {"type": "utterance", "utt_id": args.utt_id, "clip_id": args.clip_id, "distance_m": args.distance,
           "snr_db": args.snr, "noise": args.noise}
    reply = asyncio.run(send(args.url, msg, config.STT_TIMEOUT_S * 3))
    print(json.dumps(reply, ensure_ascii=False, indent=1))
    return 0 if reply.get("type") == "transcript" else 1


if __name__ == "__main__":
    sys.exit(main())
