"""Hot-partition comparison charts: Schema A vs Schema B.

Produces, from an access log (or precomputed partition loads):

  1. request-distribution histograms per schema (load balance shape)
  2. per-partition load bar chart, sorted, top partitions highlighted
  3. metric comparison bars: max load, mean load, max/mean ratio,
     top-partition traffic share

All figures are labelled with the data origin (simulated / observed)
read from the dataset manifest.

CLI:
  python -m src.catalog_analysis.hot_partition_charts \
      --data data/sample --out results/figures
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.catalog_analysis.top_partitions import (
    detect_origin, partition_loads, summarise)

A_COLOR, B_COLOR = "#c0392b", "#1a5276"


def _tag(origin: str) -> str:
    return f"[{origin.upper()} DATA]"


def chart_distributions(loads_a: pd.DataFrame, loads_b: pd.DataFrame,
                        origin: str, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=False)
    for ax, loads, color, name in (
            (axes[0], loads_a, A_COLOR, "Schema A (category)"),
            (axes[1], loads_b, B_COLOR, "Schema B (category+bucket)")):
        ax.hist(loads["total"], bins=30, color=color, edgecolor="white")
        ax.axvline(loads["total"].mean(), color="black", ls="--", lw=1,
                   label=f"mean = {loads['total'].mean():.0f}")
        ax.axvline(loads["total"].max(), color="orange", ls=":", lw=1.5,
                   label=f"max = {loads['total'].max():.0f}")
        ax.set_title(f"{name} {_tag(origin)}")
        ax.set_xlabel("requests per partition")
        ax.set_ylabel("number of partitions")
        ax.legend(fontsize=8)
    fig.suptitle("Request distribution across partitions")
    fig.tight_layout()
    fig.savefig(out / "hot_partition_distribution.png", dpi=150)
    plt.close(fig)


def chart_load_bars(loads_a: pd.DataFrame, loads_b: pd.DataFrame,
                    origin: str, out: Path, top_n: int = 25) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=False)
    for ax, loads, color, name in (
            (axes[0], loads_a, A_COLOR, "Schema A"),
            (axes[1], loads_b, B_COLOR, "Schema B")):
        top = loads["total"].head(top_n)
        mean = loads["total"].mean()
        ax.bar(range(len(top)), top.values, color=color)
        ax.axhline(mean, color="black", ls="--", lw=1,
                   label=f"mean = {mean:.0f}")
        ax.set_ylabel("requests")
        ax.set_title(f"{name}: top {top_n} partitions by requests {_tag(origin)}")
        ax.legend(fontsize=8)
    axes[1].set_xlabel("partition rank (descending traffic)")
    fig.tight_layout()
    fig.savefig(out / "hot_partition_top_loads.png", dpi=150)
    plt.close(fig)


def chart_metric_comparison(sum_a: dict, sum_b: dict,
                            origin: str, out: Path) -> None:
    metrics = [
        ("max_requests", "Max load\n(requests)"),
        ("mean_requests", "Mean load\n(requests)"),
        ("max_mean_ratio", "Max/Mean\nratio"),
        ("top_partition_share", "Top partition\ntraffic share"),
    ]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = range(len(metrics))
    w = 0.35
    va = [sum_a[k] for k, _ in metrics]
    vb = [sum_b[k] for k, _ in metrics]
    ax.bar([i - w / 2 for i in x], va, w, label="Schema A", color=A_COLOR)
    ax.bar([i + w / 2 for i in x], vb, w, label="Schema B", color=B_COLOR)
    for i, (a, b) in enumerate(zip(va, vb)):
        ax.text(i - w / 2, a, f"{a:.2f}", ha="center", va="bottom", fontsize=8)
        ax.text(i + w / 2, b, f"{b:.2f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels([lbl for _, lbl in metrics])
    ax.set_ylabel("value (requests for load metrics, ratio otherwise)")
    ax.set_title(f"Hot-partition metrics: Schema A vs Schema B {_tag(origin)}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "hot_partition_metric_comparison.png", dpi=150)
    plt.close(fig)


def run(data_dir: Path, out_dir: Path, num_buckets: int = 16) -> dict:
    access = pd.read_csv(data_dir / "access_log.csv")
    origin = detect_origin(data_dir)
    loads_a = partition_loads(access, "a", num_buckets)
    loads_b = partition_loads(access, "b", num_buckets)
    sum_a, sum_b = summarise(loads_a), summarise(loads_b)

    out_dir.mkdir(parents=True, exist_ok=True)
    chart_distributions(loads_a, loads_b, origin, out_dir)
    chart_load_bars(loads_a, loads_b, origin, out_dir)
    chart_metric_comparison(sum_a, sum_b, origin, out_dir)
    return {"origin": origin, "schema_a": sum_a, "schema_b": sum_b}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data/sample")
    ap.add_argument("--out", default="results/figures")
    ap.add_argument("--num-buckets", type=int, default=16)
    args = ap.parse_args()
    print(json.dumps(run(Path(args.data), Path(args.out),
                         args.num_buckets), indent=2))


if __name__ == "__main__":
    main()
