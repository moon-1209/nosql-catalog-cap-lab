"""Phân tích batch hội thoại (G17): logs/dialogue_batch_*.csv ➔ reports/dialogue_summary.md.

Chạy: python -m voice.analyze_dialogue [--batch logs/dialogue_batch_X.csv] [--stt-csv reports/stt_eval_X.csv]
Ghép log với manifest (text_ref, intent_true). WER chỉ tính trên clip ref_verified. Recall cap_cuu báo riêng.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from voice import config
from voice.eval_stt import REPORTS_DIR, bootstrap_ci, corpus_wer, score

LOGS_DIR: Path = REPORTS_DIR.parent / "logs"
G13_DISTANCES: tuple[float, ...] = (1.0, 2.0)


def merge(batch: pd.DataFrame, manifest: pd.DataFrame) -> pd.DataFrame:
    m = manifest[["clip_id", "text_ref", "intent", "ref_verified"]].rename(columns={"intent": "intent_true"})
    df = batch.merge(m, on="clip_id", how="left")
    df["ref_verified"] = df["ref_verified"].astype(str) == "True"
    df["completed"] = df["completed"].astype(str).str.lower() == "true"
    df["intent_ok"] = df["completed"] & (df["intent_pred"] == df["intent_true"])
    # Batch trước khi sửa (2026-10-22) ghi đè mốc NPC nói xong khi NPC nói lại (clarify) ➔ độ trễ âm, bỏ.
    df.loc[df["latency_ms"] < 0, "latency_ms"] = np.nan
    scored = [score(r.text_ref, r.hyp_text) if r.completed and r.ref_verified and isinstance(r.hyp_text, str)
              else {} for r in df.itertuples()]
    s = pd.DataFrame(scored, index=df.index)
    for col in ("wer", "word_errors", "ref_words"):
        df[col] = s[col] if col in s else np.nan
    return df


def by_group(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """Theo `key`: số episode, khoảng cách trung bình, WER (corpus, clip ref_verified), intent accuracy."""
    rows = []
    for k, g in df.groupby(key, sort=True):
        done = g[g["completed"]]
        w = done[done["ref_verified"]]
        rows.append({key: k, "n": len(g), "completed": len(done), "distance_m": done["distance_m"].mean(),
                     "wer": corpus_wer(w) if len(w) else np.nan, "n_wer": len(w),
                     "intent_acc": done["intent_ok"].mean() if len(done) else np.nan})
    return pd.DataFrame(rows)


def cap_cuu(df: pd.DataFrame) -> tuple[float, pd.DataFrame]:
    cc = df[df["intent_true"] == "cap_cuu"]
    if cc.empty:
        return float("nan"), cc
    return float(cc["intent_ok"].mean()), cc[~cc["intent_ok"]]


def g13_reference(stt: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """WER của G13 cho cùng clip ref_verified, cùng (noise, snr_db), ở 1 m và 2 m."""
    rows = []
    clips = set(df.loc[df["ref_verified"], "clip_id"])
    for (noise, snr), g in df[df["completed"] & df["ref_verified"]].groupby(["noise", "snr_db"]):
        sub = stt[stt["clip_id"].isin(clips) & (stt["noise"] == noise) & stt["wer"].notna()]
        if noise != "none":
            sub = sub[sub["snr_db"] == snr]
        row = {"noise": noise, "snr_db": snr, "batch_distance_m": g["distance_m"].mean(), "batch_wer": corpus_wer(g),
               "n_batch": len(g)}
        for d in G13_DISTANCES:
            row[f"g13_wer_{d:g}m"] = corpus_wer(sub[sub["distance_m"] == d])
        rows.append(row)
    return pd.DataFrame(rows)


def representative_errors(df: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    bad = df[df["completed"] & ~df["intent_ok"]].copy()
    if len(bad) < k:
        extra = df[df["completed"] & df["intent_ok"] & df["wer"].notna()].sort_values("wer", ascending=False)
        bad = pd.concat([bad, extra.head(k - len(bad))])
    return bad.sort_values("wer", ascending=False, na_position="last").head(k)


def _fmt(v: object, pct: bool = False) -> str:
    if isinstance(v, float):
        if np.isnan(v):
            return "—"
        return f"{v:.1%}" if pct else f"{v:.2f}"
    return str(v)


def _table(df: pd.DataFrame, pct_cols: tuple[str, ...] = ()) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + " :-- |" * len(cols)]
    for r in df.itertuples(index=False):
        lines.append("| " + " | ".join(_fmt(v, c in pct_cols or c.startswith(("wer", "g13_wer", "batch_wer")))
                                       for c, v in zip(cols, r)) + " |")
    return "\n".join(lines)


def render(df: pd.DataFrame, stt: pd.DataFrame | None, batch_name: str) -> str:
    done = df[df["completed"]]
    w = done[done["ref_verified"]]
    lo, hi = bootstrap_ci(w) if len(w) else (float("nan"), float("nan"))
    lat = done["latency_ms"].dropna()
    recall, missed = cap_cuu(df)
    errors = df.loc[~df["completed"], "error"].value_counts()
    lines = [
        "# Batch hội thoại NPC ➔ robot (G17)", "",
        f"Nguồn: `logs/{batch_name}`. Speaker: {', '.join(sorted(df['speaker'].unique()))}.", "",
        "> **Hạn chế:** kịch bản dự kiến 2 người nói 20 tuổi (A nam, B nữ) nhưng hiện mới có giọng A; kết quả chưa "
        "đại diện cho người cao tuổi, giọng nữ hay giọng địa phương khác. Bản đồ bệnh viện là giả lập.", "",
        "## Tổng hợp", "",
        "| Chỉ số | Giá trị |", "| :-- | :-- |",
        f"| Episode | {len(df)} |",
        f"| Hoàn thành một lượt | {len(done)}/{len(df)} ({len(done) / len(df):.1%}) |",
        f"| Lỗi | {', '.join(f'{k}: {v}' for k, v in errors.items()) or 'không'} |",
        f"| WER (clip ref_verified, {len(w)} lượt) | {_fmt(corpus_wer(w) if len(w) else float('nan'), True)} "
        f"[KTC 95% {_fmt(lo, True)}, {_fmt(hi, True)}] |",
        f"| Intent accuracy (lượt hoàn thành) | {_fmt(done['intent_ok'].mean() if len(done) else float('nan'), True)} |",
        f"| **Recall cap_cuu** | {_fmt(recall, True)} ({int((df['intent_true'] == 'cap_cuu').sum())} lượt) |",
        f"| NPC nói xong ➔ có phụ đề (ms) | trung bình {_fmt(lat.mean())}, p50 {_fmt(lat.median())}, "
        f"p95 {_fmt(lat.quantile(0.95) if len(lat) else float('nan'))} |",
        f"| stt_ms trung bình | {_fmt(done['stt_ms'].mean())} |", "",
        "## Theo khoảng cách (mức H_TARGET)", "", _table(by_group(df, "h_target"), ("intent_acc",)), "",
        "## Theo điều kiện ồn", "", _table(by_group(df, "noise"), ("intent_acc",)), "",
    ]
    if stt is not None:
        lines += ["## So với G13 (cùng clip, cùng noise/SNR)", "",
                  "Batch có khoảng cách nói 1.4–2.0 m nên WER nên nằm giữa cột 1 m và 2 m của G13; số lượt nhỏ nên dao "
                  "động lớn.", "", _table(g13_reference(stt, df)), ""]
    lines += ["## Lượt cap_cuu bị bỏ sót", ""]
    if missed.empty:
        lines.append("Không có.")
    else:
        lines += [f"- ep {r.episode} `{r.clip_id}` {r.noise}/{r.snr_db:g} dB, {r.distance_m:.2f} m: "
                  f"hyp \"{r.hyp_text}\" ➔ {r.intent_pred}" for r in missed.itertuples()]
    lines += ["", "## 5 lượt sai tiêu biểu", "", "| clip_id | hyp | intent dự đoán | intent đúng | WER |",
              "| :-- | :-- | :-- | :-- | :-- |"]
    for r in representative_errors(df).itertuples():
        lines.append(f"| {r.clip_id} | {r.hyp_text} | {r.intent_pred} | {r.intent_true} | {_fmt(r.wer, True)} |")
    return "\n".join(lines) + "\n"


def latest(directory: Path, pattern: str) -> Path | None:
    found = sorted(directory.glob(pattern))
    return found[-1] if found else None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Analyze dialogue batch (G17)")
    p.add_argument("--batch", type=Path, default=None)
    p.add_argument("--stt-csv", type=Path, default=None)
    p.add_argument("--data-dir", type=Path, default=config.DATA_DIR)
    p.add_argument("--out", type=Path, default=REPORTS_DIR / "dialogue_summary.md")
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    batch = args.batch or latest(LOGS_DIR, "dialogue_batch_*.csv")
    if batch is None or not batch.is_file():
        print("ERROR: không có logs/dialogue_batch_*.csv: chạy tools/dialogue_batch.tscn trước", file=sys.stderr)
        return 1
    stt_csv = args.stt_csv or latest(REPORTS_DIR, "stt_eval_*.csv")
    df = merge(pd.read_csv(batch), pd.read_csv(config.manifest_path(args.data_dir), dtype=str))
    stt = pd.read_csv(stt_csv) if stt_csv is not None and stt_csv.is_file() else None
    args.out.write_text(render(df, stt, batch.name), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
