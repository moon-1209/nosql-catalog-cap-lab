"""Bootstrap 95% confidence intervals for benchmark metrics.

Two resampling schemes are provided because benchmark observations are
often *not* independent (latency drifts, partitions correlate neighbours):

  * ``method="iid"``    - classic bootstrap: resample rows with
                        replacement.  Use only when observations are
                        exchangeable.
  * ``method="block"``  - moving-block bootstrap: resample contiguous
                        blocks of ``block_len`` consecutive observations,
                        preserving short-range time dependence.

A bootstrap CI describes sampling uncertainty of the statistic - it is
**not** causal evidence and does not fix biased measurement.

CLI:
  python -m src.catalog_analysis.bootstrap_ci \
      --data data/sample --out results/bootstrap
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.catalog_analysis.stale_read import classify_reads
from src.catalog_analysis.top_partitions import detect_origin


def _clean(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return x[np.isfinite(x)]


def _block_resample(x: np.ndarray, block_len: int,
                    rng: np.random.Generator) -> np.ndarray:
    n = len(x)
    starts = rng.integers(0, n - block_len + 1,
                          size=int(np.ceil(n / block_len)))
    out = np.concatenate([x[s:s + block_len] for s in starts])
    return out[:n]


def bootstrap_ci(data, stat_fn=np.mean, n_resamples: int = 2000,
                 seed: int | None = None, method: str = "iid",
                 block_len: int = 50, alpha: float = 0.05,
                 min_samples: int = 30) -> dict:
    """Percentile bootstrap CI for `stat_fn` over `data`.

    Returns dict(estimate, ci_low, ci_high, n, method); CI fields are
    None when the sample is unusable.
    """
    x = _clean(data)
    if len(x) < min_samples or method not in ("iid", "block"):
        return {"estimate": float(stat_fn(x)) if len(x) else None,
                "ci_low": None, "ci_high": None, "n": int(len(x)),
                "method": method,
                "note": "insufficient data" if len(x) < min_samples
                        else "unknown method"}
    rng = np.random.default_rng(seed)
    if method == "block":
        block_len = max(1, min(block_len, len(x) - 1))
        stats = [stat_fn(_block_resample(x, block_len, rng))
                 for _ in range(n_resamples)]
    else:
        stats = [stat_fn(x[rng.integers(0, len(x), len(x))])
                 for _ in range(n_resamples)]
    lo, hi = np.percentile(stats, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"estimate": float(stat_fn(x)), "ci_low": float(lo),
            "ci_high": float(hi), "n": int(len(x)), "method": method,
            "resamples": n_resamples, "alpha": alpha}


def run(data_dir: Path, out_dir: Path, n_resamples: int = 2000,
        seed: int = 42) -> dict:
    origin = detect_origin(data_dir)
    access = pd.read_csv(data_dir / "access_log.csv")
    log = pd.read_csv(data_dir / "consistency_log.csv")
    reads = classify_reads(log)

    kw = dict(n_resamples=n_resamples, seed=seed)
    results = {
        "origin": origin,
        "method_note": ("iid bootstrap for exchangeable metrics; "
                        "moving-block bootstrap (block=50) for "
                        "time-ordered latency"),
        "metrics": {
            "latency_ms_mean_block": bootstrap_ci(
                access["latency_ms"].to_numpy(), np.mean,
                method="block", block_len=50, **kw),
            "latency_ms_p95_iid": bootstrap_ci(
                access["latency_ms"].to_numpy(),
                lambda x: np.percentile(x, 95), **kw),
            # bootstrap the requests, not the 20 partition aggregates:
            # each resample recomputes the top category's traffic share
            "top_partition_share_schema_a": bootstrap_ci(
                pd.Categorical(access["category_id"]).codes,
                lambda codes: np.bincount(
                    codes.astype(np.int64)).max() / len(codes), **kw),
        },
        "stale_rate_by_level": {},
    }
    for level, g in reads.groupby("consistency_level"):
        g = g[g["valid"]]
        results["stale_rate_by_level"][str(level)] = bootstrap_ci(
            g["is_stale"].to_numpy(dtype=float), np.mean, **kw)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(results, indent=2))
    _plot(access["latency_ms"].to_numpy(),
          results["metrics"]["latency_ms_mean_block"], origin,
          out_dir / "bootstrap_latency_mean.png", seed, n_resamples)
    return results


def _plot(latency: np.ndarray, ci: dict, origin: str, path: Path,
          seed: int, n_resamples: int) -> None:
    x = _clean(latency)
    rng = np.random.default_rng(seed)
    stats = [np.mean(_block_resample(x, 50, rng)) for _ in range(n_resamples)]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(stats, bins=40, color="#1a5276", alpha=0.8, edgecolor="white")
    for v, lbl, c in ((ci["estimate"], "estimate", "black"),
                      (ci["ci_low"], "CI 2.5%", "red"),
                      (ci["ci_high"], "CI 97.5%", "red")):
        if v is not None:
            ax.axvline(v, color=c, ls="--", lw=1.2,
                       label=f"{lbl} = {v:.2f} ms")
    ax.set_xlabel("mean latency (ms)")
    ax.set_ylabel("bootstrap resamples")
    ax.set_title(f"Block-bootstrap distribution, mean latency "
                 f"[{origin.upper()} DATA]")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data/sample")
    ap.add_argument("--out", default="results/bootstrap")
    ap.add_argument("--resamples", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    res = run(Path(args.data), Path(args.out), args.resamples, args.seed)
    print(json.dumps(res["metrics"], indent=2))


if __name__ == "__main__":
    main()
