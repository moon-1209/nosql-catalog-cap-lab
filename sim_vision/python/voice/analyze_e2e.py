"""Batch đầu cuối với NLU PhoBERT + TTS (G23): logs/dialogue_batch_*.csv ➔ reports/e2e_summary.md.

Chạy: python -m voice.analyze_e2e [--batch logs/dialogue_batch_X.csv]
Báo: tỉ lệ hoàn thành lượt, phân bố action, intent accuracy, recall cap_cuu, độ trễ từ lúc NPC nói xong đến lúc
robot bắt đầu nói, tách STT (stt_ms), TTS (tts_ms) và phần còn lại (NLU + mạng + khung hình Godot).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from voice import config
from voice.analyze_dialogue import LOGS_DIR, cap_cuu, latest, merge
from voice.eval_stt import REPORTS_DIR


def latency_split(df: pd.DataFrame) -> pd.DataFrame:
    """Chỉ lượt có âm thanh (tts_error rỗng). other = latency − stt − tts."""
    ok = df[df["completed"] & df["latency_ms"].notna() & df["tts_ms"].notna()].copy()
    ok["other_ms"] = ok["latency_ms"] - ok["stt_ms"] - ok["tts_ms"]
    rows = []
    for col, name in (("latency_ms", "Tổng (NPC nói xong ➔ robot bắt đầu nói)"), ("stt_ms", "STT"),
                      ("tts_ms", "TTS"), ("other_ms", "NLU + mạng + khung hình")):
        v = ok[col]
        rows.append({"phần": name, "TB": v.mean(), "p50": v.median(), "p95": v.quantile(0.95) if len(v) else np.nan})
    return pd.DataFrame(rows)


def render(df: pd.DataFrame, batch_name: str) -> str:
    done = df[df["completed"]]
    recall, missed = cap_cuu(df)
    tts_err = df.loc[df["completed"], "tts_error"].fillna("").replace("", "không lỗi").value_counts()
    hits = done["tts_cache_hit"].astype(str).str.lower().eq("true").mean() if len(done) else float("nan")
    actions = done["action"].fillna("(null)").value_counts()
    lines = [
        "# Batch đầu cuối: STT ➔ NLU PhoBERT ➔ policy ➔ TTS (G23)", "",
        f"Nguồn: `logs/{batch_name}`. STT server chạy `--nlu phobert`; TTS server VieNeu v3 Turbo (cache sinh sẵn).",
        "", "> **Hạn chế:** chỉ giọng A (nam, 20 tuổi); mỗi episode dừng ở lượt trả lời đầu tiên nên nhánh clarify "
        "(người bệnh nói lại) không chạy trong batch, chỉ được kiểm bằng test GUT.", "",
        "## Tổng hợp", "", "| Chỉ số | Giá trị |", "| :-- | :-- |",
        f"| Episode | {len(df)} |",
        f"| Hoàn thành lượt | {len(done)}/{len(df)} ({len(done) / len(df):.1%}) |",
        f"| Lỗi STT / episode | {', '.join(f'{k}: {v}' for k, v in df.loc[~df['completed'], 'error'].value_counts().items()) or 'không'} |",
        f"| Kết quả TTS (lượt hoàn thành) | {', '.join(f'{k}: {v}' for k, v in tts_err.items())} |",
        f"| TTS cache hit | {hits:.1%} |",
        f"| Intent accuracy | {done['intent_ok'].mean():.1%} |",
        f"| Recall cap_cuu | {recall:.1%} ({int((df['intent_true'] == 'cap_cuu').sum())} lượt) |", "",
        "## Phân bố action", "", "| action | số lượt |", "| :-- | --: |",
        *[f"| {k} | {v} |" for k, v in actions.items()], "",
        "## Độ trễ (ms)", "", "| Phần | TB | p50 | p95 |", "| :-- | --: | --: | --: |",
        *[f"| {r.phần} | {r.TB:.0f} | {r.p50:.0f} | {r.p95:.0f} |" for r in latency_split(df).itertuples()], "",
        "## Lượt cap_cuu bị bỏ sót", "",
    ]
    lines += [f"- ep {r.episode} `{r.clip_id}` {r.noise}/{r.snr_db:g} dB, {r.distance_m:.2f} m: \"{r.hyp_text}\" ➔ "
              f"{r.intent_pred}" for r in missed.itertuples()] or ["Không có."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Analyze end-to-end dialogue batch (G23)")
    p.add_argument("--batch", type=Path, default=None)
    p.add_argument("--data-dir", type=Path, default=config.DATA_DIR)
    p.add_argument("--out", type=Path, default=REPORTS_DIR / "e2e_summary.md")
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    batch = args.batch or latest(LOGS_DIR, "dialogue_batch_*.csv")
    if batch is None or not batch.is_file():
        print("ERROR: không có logs/dialogue_batch_*.csv", file=sys.stderr)
        return 1
    df = merge(pd.read_csv(batch), pd.read_csv(config.manifest_path(args.data_dir), dtype=str))
    if "tts_ms" not in df:
        print("ERROR: batch không có cột TTS (chạy lại dialogue_batch sau G22)", file=sys.stderr)
        return 1
    args.out.write_text(render(df, batch.name), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
