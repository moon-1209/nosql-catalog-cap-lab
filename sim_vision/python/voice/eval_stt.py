"""Đánh giá STT offline (G13): WER/CER theo người, kiểu đọc, loại ồn, SNR, khoảng cách.

Chạy: python -m voice.eval_stt [--grid default|quick] [--model DIR] [--beams 1] [--fake]
Ra:   reports/stt_eval_<timestamp>.csv, reports/stt_summary.md, reports/wer_vs_snr.png, reports/wer_vs_distance.png
Gọi Transcriber trực tiếp (không qua WebSocket). Kết quả STT được cache ở reports/stt_cache/.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import zlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import jiwer
import numpy as np
import pandas as pd

from voice import audio_sim, config
from voice.stt_server import ClipStore, read_manifest
from voice.text_norm import has_number_mismatch, normalize
from voice.transcriber import FakeTranscriber, Transcriber

REPORTS_DIR: Path = Path(__file__).resolve().parents[2] / "reports"
DEFAULT_SEED: int = 0
BOOTSTRAP_N: int = 1000
NONE_SNR_DB: float = 30.0          # "none" chỉ chạy với 1 SNR; giá trị không ảnh hưởng (không có ồn)
DIMENSIONS: tuple[str, ...] = ("speaker", "take", "noise", "snr_db", "distance_m")
EVAL_COLS: list[str] = ["clip_id", "speaker", "take", "intent_true", "ref_verified", "distance_m", "snr_db", "noise",
                        "effective_snr_db", "text_ref", "hyp", "wer", "cer", "word_errors", "ref_words",
                        "char_errors", "ref_chars", "number_mismatch", "intent_pred", "intent_ok", "cached", "error"]


@dataclass(frozen=True)
class Condition:
    distance_m: float
    snr_db: float
    noise: str


def build_grid(name: str) -> list[Condition]:
    if name == "default":
        dists, snrs, noises = (0.5, 1.0, 2.0, 3.0), (30.0, 20.0, 10.0, 5.0), ("white", "babble")
    elif name == "quick":
        dists, snrs, noises = (1.0, 3.0), (20.0, 5.0), ("babble",)
    else:
        raise ValueError(f"unknown grid: {name}")
    grid = [Condition(d, NONE_SNR_DB, "none") for d in dists]
    return grid + [Condition(d, s, n) for n in noises for s in snrs for d in dists]


def condition_seed(seed: int, clip_id: str, c: Condition) -> int:
    return zlib.crc32(f"{seed}:{clip_id}:{c.distance_m}:{c.snr_db}:{c.noise}".encode())


class SttCache:
    """Cache hyp theo (clip_id, distance, snr, noise, seed, model, beams), lưu dạng JSON lines."""

    def __init__(self, path: Path | None) -> None:
        self.path = path
        self.data: dict[str, str] = {}
        if path is not None and path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self.data[rec["key"]] = rec["hyp"]

    @staticmethod
    def key(clip_id: str, c: Condition, seed: int, model: str, beams: int) -> str:
        return json.dumps([clip_id, c.distance_m, c.snr_db, c.noise, seed, model, beams])

    def get(self, key: str) -> str | None:
        return self.data.get(key)

    def put(self, key: str, hyp: str) -> None:
        self.data[key] = hyp
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key, "hyp": hyp}, ensure_ascii=False) + "\n")


def score(ref: str, hyp: str) -> dict[str, float | int]:
    """WER/CER sau chuẩn hóa, kèm số lỗi và độ dài ref để gộp theo corpus."""
    r, h = normalize(ref), normalize(hyp)
    w = jiwer.process_words(r, h)
    c = jiwer.process_characters(r, h)
    we = w.substitutions + w.deletions + w.insertions
    ce = c.substitutions + c.deletions + c.insertions
    nw, nc = len(r.split()), len(r)
    return {"wer": we / nw, "cer": ce / nc, "word_errors": we, "ref_words": nw, "char_errors": ce, "ref_chars": nc}


def corpus_wer(df: pd.DataFrame) -> float:
    n = df["ref_words"].sum()
    return float(df["word_errors"].sum() / n) if n else float("nan")


def bootstrap_ci(df: pd.DataFrame, n: int = BOOTSTRAP_N, seed: int = DEFAULT_SEED,
                 errors: str = "word_errors", length: str = "ref_words") -> tuple[float, float]:
    """KTC 95% của WER corpus, bootstrap theo clip (lấy lại clip có hoàn lại)."""
    per_clip = df.groupby("clip_id")[[errors, length]].sum()
    if per_clip.empty:
        return float("nan"), float("nan")
    e, w = per_clip[errors].to_numpy(float), per_clip[length].to_numpy(float)
    idx = np.random.default_rng(seed).integers(0, len(per_clip), size=(n, len(per_clip)))
    vals = e[idx].sum(axis=1) / w[idx].sum(axis=1)
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def load_classifier() -> Callable[[str], str] | None:
    try:
        from voice import intent
    except ImportError:
        return None
    return lambda text: intent.classify(text).intent


def evaluate(store: ClipStore, transcriber: Transcriber, grid: Iterable[Condition], model: str, beams: int,
             cache: SttCache, seed: int = DEFAULT_SEED, classify: Callable[[str], str] | None = None,
             progress: Callable[[int, int], None] | None = None) -> pd.DataFrame:
    """Mỗi dòng một clip × một điều kiện. Lỗi một clip ➔ cột `error`, không dừng cả lượt."""
    grid = list(grid)
    rows: list[dict] = []
    total = len(grid) * len(store.manifest)
    for c in grid:
        for clip_id, m in sorted(store.manifest.items()):
            verified = str(m["ref_verified"]) == "True"
            row: dict = {"clip_id": clip_id, "speaker": m["speaker"], "take": m["take"], "intent_true": m["intent"],
                         "ref_verified": verified, "distance_m": c.distance_m, "snr_db": c.snr_db, "noise": c.noise,
                         "text_ref": m["text_ref"], "error": ""}
            key = cache.key(clip_id, c, seed, model, beams)
            try:
                rng = np.random.default_rng(condition_seed(seed, clip_id, c))
                audio, eff = audio_sim.render(store.speech(clip_id), c.distance_m, c.snr_db, c.noise, rng,
                                              store.noise_fn(clip_id))
                row["effective_snr_db"] = eff if math.isfinite(eff) else None
                hyp = cache.get(key)
                row["cached"] = hyp is not None
                if hyp is None:
                    hyp = transcriber.transcribe(audio, config.SAMPLE_RATE, clip_id)
                    cache.put(key, hyp)
                row["hyp"] = hyp
                if verified:
                    row.update(score(m["text_ref"], hyp))
                    row["number_mismatch"] = has_number_mismatch(m["text_ref"], hyp)
                if classify is not None:
                    row["intent_pred"] = classify(hyp)
                    row["intent_ok"] = row["intent_pred"] == m["intent"]
            except Exception as exc:  # noqa: BLE001
                row["error"] = f"{type(exc).__name__}: {exc}"
            rows.append(row)
            if progress is not None:
                progress(len(rows), total)
    return pd.DataFrame(rows, columns=EVAL_COLS)


def summarize(df: pd.DataFrame, seed: int = DEFAULT_SEED, n_boot: int = BOOTSTRAP_N) -> dict[str, pd.DataFrame]:
    """Bảng WER theo từng chiều (chỉ clip đã xác minh, không lỗi), kèm KTC 95% và số clip."""
    ok = df[(df["error"] == "") & df["ref_verified"].astype(bool) & df["ref_words"].notna()]
    out: dict[str, pd.DataFrame] = {}
    for dim in ("all",) + DIMENSIONS:
        # SNR của "none" chỉ là giá trị giữ chỗ ➔ không đưa vào bảng theo SNR.
        src = ok[ok["noise"] != "none"] if dim == "snr_db" else ok
        groups = [("all", ok)] if dim == "all" else list(src.groupby(dim, sort=True))
        recs = []
        for val, g in groups:
            lo, hi = bootstrap_ci(g, n_boot, seed)
            recs.append({dim: val, "wer": corpus_wer(g), "ci_lo": lo, "ci_hi": hi,
                         "cer": float(g["char_errors"].sum() / g["ref_chars"].sum()),
                         "number_mismatch": float(g["number_mismatch"].astype(bool).mean()),
                         "n_clips": g["clip_id"].nunique(), "n_rows": len(g)})
        out[dim] = pd.DataFrame(recs)
    return out


def intent_table(df: pd.DataFrame, by: str) -> pd.DataFrame:
    ok = df[(df["error"] == "") & df["intent_ok"].notna()]
    return ok.groupby(by)["intent_ok"].agg(acc="mean", n="size").reset_index()


def plot(df: pd.DataFrame, out_dir: Path) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ok = df[(df["error"] == "") & df["ref_verified"].astype(bool) & df["ref_words"].notna()]
    paths = []
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for noise, g in ok.groupby("noise"):
        if noise == "none":
            ax.axhline(corpus_wer(g), ls="--", c="gray", label="none (không ồn)")
            continue
        pts = g.groupby("snr_db").apply(corpus_wer, include_groups=False).sort_index()
        ax.plot(pts.index, pts.values, marker="o", label=noise)
    ax.set(xlabel="SNR tại 1 m (dB)", ylabel="WER", title="WER theo SNR (trung bình mọi khoảng cách)")
    ax.invert_xaxis()
    ax.grid(alpha=0.3)
    ax.legend()
    paths.append(out_dir / "wer_vs_snr.png")
    fig.tight_layout()
    fig.savefig(paths[-1], dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for noise, g in ok.groupby("noise"):
        pts = g.groupby("distance_m").apply(corpus_wer, include_groups=False).sort_index()
        ax.plot(pts.index, pts.values, marker="o", label=noise)
    ax.set(xlabel="Khoảng cách (m)", ylabel="WER", title="WER theo khoảng cách (trung bình mọi SNR)")
    ax.grid(alpha=0.3)
    ax.legend()
    paths.append(out_dir / "wer_vs_distance.png")
    fig.tight_layout()
    fig.savefig(paths[-1], dpi=120)
    plt.close(fig)
    return paths


def _fmt(t: pd.DataFrame) -> str:
    cols = list(t.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(":--" for _ in cols) + " |"]
    for r in t.itertuples(index=False):
        lines.append("| " + " | ".join(f"{v:.3f}" if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(lines)


def write_summary(df: pd.DataFrame, tables: dict[str, pd.DataFrame], path: Path, meta: dict[str, str]) -> None:
    verified = df[df["ref_verified"].astype(bool)]["clip_id"].nunique()
    parts = [f"# Đánh giá STT ({meta['model']}, beams={meta['beams']})", "",
             f"- Thời điểm: {meta['time']}; file chi tiết: `{meta['csv']}`; seed {meta['seed']}; lưới `{meta['grid']}`.",
             f"- {df['clip_id'].nunique()} clip, {verified} clip đã xác minh transcript (WER chỉ tính trên các clip này), "
             f"{len(df)} dòng, {int((df['error'] != '').sum())} dòng lỗi.",
             "- WER, CER gộp theo corpus (tổng lỗi / tổng từ). KTC 95%: bootstrap theo clip, "
             f"{BOOTSTRAP_N} lần. `number_mismatch`: tỉ lệ câu có số trong ref mà hyp viết khác dạng.",
             "- Dữ liệu: chỉ có 1 người nói (A, nam, 20 tuổi); chưa đại diện cho giọng nữ hay người cao tuổi.", ""]
    for dim, t in tables.items():
        parts += [f"## WER theo {dim}" if dim != "all" else "## Tổng", "", _fmt(t), ""]
    if df["intent_ok"].notna().any():
        for by in ("take", "noise", "distance_m"):
            parts += [f"## Độ chính xác intent theo {by} (mọi clip, kể cả `_n`)", "", _fmt(intent_table(df, by)), ""]
    parts += ["## Biểu đồ", "", "![WER theo SNR](wer_vs_snr.png)", "", "![WER theo khoảng cách](wer_vs_distance.png)", ""]
    path.write_text("\n".join(parts), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--grid", default="default", choices=["default", "quick"])
    p.add_argument("--model", default=config.STT_MODEL_ID)
    p.add_argument("--beams", type=int, default=1, choices=range(1, 6))
    p.add_argument("--device", default="auto")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--fake", action="store_true", help="FakeTranscriber (trả text_ref) để kiểm tra đường ống")
    p.add_argument("--data-dir", type=Path, default=config.DATA_DIR)
    p.add_argument("--out", type=Path, default=REPORTS_DIR)
    args = p.parse_args(sys.argv[1:] if argv is None else argv)

    mpath = config.manifest_path(args.data_dir)
    if not mpath.is_file():
        print(f"ERROR: {mpath} not found: run `python -m voice.prepare_data` first", file=sys.stderr)
        return 1
    store = ClipStore(read_manifest(mpath), config.wav_dir(args.data_dir), args.data_dir / "noise")
    if args.fake:
        transcriber: Transcriber = FakeTranscriber({c: r["text_ref"] for c, r in store.manifest.items()})
        model, cache = "fake", SttCache(None)
    else:
        from voice.transcriber import PhoWhisperTranscriber
        transcriber = PhoWhisperTranscriber(args.model, args.device, args.beams)
        model = Path(args.model).name
        cache = SttCache(args.out / "stt_cache" / "cache.jsonl")
    args.out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()

    def progress(i: int, n: int) -> None:
        if i % 100 == 0 or i == n:
            print(f"  {i}/{n} ({time.time() - t0:.0f} s)", flush=True)

    grid = build_grid(args.grid)
    df = evaluate(store, transcriber, grid, model, args.beams, cache, args.seed, load_classifier(), progress)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = args.out / f"stt_eval_{stamp}.csv"
    df.to_csv(csv_path, index=False)
    tables = summarize(df, args.seed)
    plot(df, args.out)
    write_summary(df, tables, args.out / "stt_summary.md",
                  {"model": model, "beams": str(args.beams), "time": stamp, "csv": csv_path.name,
                   "seed": str(args.seed), "grid": args.grid})
    print(tables["all"].to_string(index=False))
    print(f"➔ {csv_path}, {args.out / 'stt_summary.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
