"""Độ dễ nghe của TTS (G23): câu trả lời đã sinh sẵn (G21) ➔ PhoWhisper (G12, noise none, 1 m) ➔ WER khứ hồi.

Chạy (venv chính, có torch): python -m tts.eval_tts_roundtrip ➔ reports/tts_roundtrip.md, reports/tts_roundtrip.csv
Tham chiếu = văn bản robot thật sự đọc (text_for_tts: số đã viết bằng chữ), vì STT cũng viết số bằng chữ.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from tts import config
from tts.text_for_tts import text_for_tts
from tts.tts_engine import TtsCache, cache_key

STT_SR: int = 16000
HIGH_WER: float = 0.2


def load_cached(cache: TtsCache, text: str, voice: str, model_version: str = config.MODEL_VERSION
                ) -> np.ndarray | None:
    """PCM 24 kHz trong cache ➔ float32 16 kHz (bỏ 100 ms im lặng hai đầu không ảnh hưởng STT)."""
    pcm = cache.get(cache_key(text_for_tts(text), voice, model_version))
    if pcm is None:
        return None
    import soxr

    x = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32767.0
    return soxr.resample(x, cache.sample_rate, STT_SR).astype(np.float32)


def evaluate(texts: list[str], voice: str, cache: TtsCache, transcribe, model_version: str = config.MODEL_VERSION
             ) -> pd.DataFrame:
    from voice.eval_stt import score
    from voice.text_norm import has_number_mismatch

    rows = []
    for t in texts:
        audio = load_cached(cache, t, voice, model_version)
        if audio is None:
            rows.append({"response": t, "spoken": text_for_tts(t), "hyp": None, "error": "not cached"})
            continue
        hyp = transcribe(audio)
        s = score(text_for_tts(t), hyp)
        # STT viết số bằng chữ số ("205", "1-1-2") ➔ đổi sang chữ như robot đọc để chỉ còn lỗi nghe thật.
        n = score(text_for_tts(t), text_for_tts(hyp.replace("-", " ")))
        rows.append({"response": t, "spoken": text_for_tts(t), "hyp": hyp, "error": "", **s,
                     "word_errors_num": n["word_errors"], "wer_num": n["wer"],
                     "number_mismatch": has_number_mismatch(t, hyp), "audio_s": audio.size / STT_SR})
    return pd.DataFrame(rows)


def render(df: pd.DataFrame, voice: str) -> str:
    ok = df[df["error"] == ""]
    wer = ok["word_errors"].sum() / ok["ref_words"].sum() if len(ok) else float("nan")
    wer_num = ok["word_errors_num"].sum() / ok["ref_words"].sum() if len(ok) else float("nan")
    high = ok[ok["wer_num"] > HIGH_WER].sort_values("wer_num", ascending=False)
    lines = ["# Độ dễ nghe của giọng robot: WER khứ hồi TTS ➔ STT (G23)", "",
             f"Giọng: **{voice}** (VieNeu-TTS v3 Turbo, ONNX/CPU). STT: PhoASR-whisper-small, không ồn, 1 m. "
             f"Tham chiếu là câu sau `text_for_tts` (số đọc bằng chữ).", "",
             "| Chỉ số | Giá trị |", "| :-- | :-- |",
             f"| Số câu | {len(df)} (thiếu cache: {int((df['error'] != '').sum())}) |",
             f"| WER khứ hồi (corpus), so nguyên văn | {wer:.1%} |",
             f"| **WER sau khi đổi số STT sang chữ** (chỉ còn lỗi nghe) | {wer_num:.1%} |",
             f"| Câu WER (đã đổi số) = 0 | {int((ok['wer_num'] == 0).sum())}/{len(ok)} |",
             f"| Câu WER (đã đổi số) > {HIGH_WER:.0%} | {len(high)} |", "",
             "WER nguyên văn cao chủ yếu vì STT viết số bằng chữ số (\"205\", \"1-1-2\") còn robot đọc bằng chữ.", "",
             f"## Câu có WER (đã đổi số) > {HIGH_WER:.0%}", ""]
    if high.empty:
        lines.append("Không có.")
    else:
        lines += ["| WER | Robot đọc | STT nghe được |", "| --: | :-- | :-- |"]
        lines += [f"| {r.wer_num:.0%} | {r.spoken} | {r.hyp} |" for r in high.itertuples()]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="TTS round-trip intelligibility via STT (G23)")
    p.add_argument("--voice", default=config.ROBOT_VOICE)
    p.add_argument("--out-dir", type=Path, default=config.REPORTS_DIR)
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    from nlu.policy import all_responses
    from voice import audio_sim
    from voice import config as voice_config
    from voice.transcriber import PhoWhisperTranscriber

    tr = PhoWhisperTranscriber(voice_config.STT_MODEL_ID, "auto", 1)

    def transcribe(audio: np.ndarray) -> str:
        x, _ = audio_sim.render(audio, 1.0, 30.0, "none", np.random.default_rng(0))
        return tr.transcribe(x, STT_SR)

    df = evaluate(all_responses(), args.voice, TtsCache(config.TTS_CACHE_DIR), transcribe)
    df.to_csv(args.out_dir / "tts_roundtrip.csv", index=False)
    (args.out_dir / "tts_roundtrip.md").write_text(render(df, args.voice), encoding="utf-8")
    print(f"wrote {args.out_dir / 'tts_roundtrip.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
