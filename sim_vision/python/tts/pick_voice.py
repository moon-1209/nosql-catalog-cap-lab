"""In danh sách giọng có sẵn và sinh 1 câu mẫu cho mỗi giọng vào reports/voices/ để người dùng chọn (G21, U4).

Chạy: .venv-tts/bin/python -m tts.pick_voice
Không dùng tính năng clone giọng.
"""

from __future__ import annotations

import sys

import numpy as np
import soundfile as sf

from tts import config
from tts.text_for_tts import text_for_tts
from tts.tts_engine import postprocess

SAMPLE: str = "Dạ, phòng 205 ở tầng 2. Mời anh chị đi theo tôi. Anh chị cần gì cứ gọi tôi nhé."


def main() -> int:
    from tts.tts_engine import VieneuEngine

    engine = VieneuEngine()
    out = config.REPORTS_DIR / "voices"
    out.mkdir(parents=True, exist_ok=True)
    lines = ["# Giọng mẫu VieNeu-TTS v3 Turbo (G21)", "", f"Câu: \"{SAMPLE}\"", "",
             "| # | Giọng (id) | Mô tả | File |", "| --: | :-- | :-- | :-- |"]
    for i, (label, vid) in enumerate(engine.voice_labels(), 1):
        audio, sr = engine.synth(text_for_tts(SAMPLE), vid)
        name = f"{i:02d}_{vid.replace(' ', '_')}.wav"
        sf.write(str(out / name), np.frombuffer(postprocess(audio, sr), dtype="<i2"), config.OUT_SAMPLE_RATE,
                 subtype="PCM_16")
        lines.append(f"| {i} | {vid} | {label.split('—', 1)[-1].strip()} | `{name}` |")
        print(f"{i:2d}. {label} ➔ {name}")
    (out / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"ROBOT_VOICE hiện tại: {config.ROBOT_VOICE}. Nghe các file trong {out} rồi chọn.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
