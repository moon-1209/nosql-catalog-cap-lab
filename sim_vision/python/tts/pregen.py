"""Sinh sẵn giọng nói cho mọi câu trả lời có thể có (G21): nlu.policy.all_responses() ➔ cache TTS.

Chạy (venv có vieneu): .venv-tts/bin/python -m tts.pregen [--voice "Ngọc Huyền"]
"""

from __future__ import annotations

import argparse
import sys
import time

from tts import config
from tts.tts_engine import Synthesizer, TTSEngine, TtsCache


def pregen(synth: Synthesizer, texts: list[str], voice: str, log=print) -> dict[str, float]:
    t0 = time.perf_counter()
    hits = 0
    miss_ms: list[float] = []
    for i, text in enumerate(texts, 1):
        s = synth.speak(text, voice)
        hits += s.cache_hit
        if not s.cache_hit:
            miss_ms.append(s.tts_ms)
        log(f"[{i}/{len(texts)}] {'hit ' if s.cache_hit else 'miss'} {s.tts_ms:7.0f} ms {s.duration_s:5.2f} s")
    total = time.perf_counter() - t0
    return {"n": len(texts), "hits": hits, "misses": len(miss_ms), "total_s": total,
            "mean_miss_ms": sum(miss_ms) / len(miss_ms) if miss_ms else 0.0}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pre-generate TTS cache for every robot response (G21)")
    p.add_argument("--voice", default=config.ROBOT_VOICE)
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    from tts.tts_engine import VieneuEngine

    engine: TTSEngine = VieneuEngine()                       # trước mọi import dùng huggingface_hub
    if args.voice not in engine.voices():
        print(f"ERROR: voice '{args.voice}' không có: {engine.voices()}", file=sys.stderr)
        return 1
    from nlu.policy import all_responses

    r = pregen(Synthesizer(engine, TtsCache(config.TTS_CACHE_DIR)), all_responses(), args.voice)
    print(f"{r['n']} câu, {r['misses']} sinh mới (trung bình {r['mean_miss_ms']:.0f} ms), {r['hits']} có sẵn; "
          f"tổng {r['total_s']:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
