"""Consistency heatmap + network-partition timeline.

Two figures, derived strictly from the consistency log (no inferred
violations - only reads provably stale per `stale_read.classify_reads`):

  1. `consistency_heatmap.png` - stale-read rate per (node x time bucket),
     one panel per consistency level; the partition window is outlined.
  2. `consistency_timeline.png` - event volume over time with stale reads
     overlaid and the four phases marked: normal / disruption start /
     partitioned / recovery.

CLI:
  python -m src.catalog_analysis.consistency_viz \
      --data data/sample --out results/figures
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.catalog_analysis.stale_read import classify_reads
from src.catalog_analysis.top_partitions import detect_origin

N_BINS = 30


def _window(log: pd.DataFrame):
    part = log.loc[log["network_state"] == "PARTITIONED", "ts"]
    return (int(part.min()), int(part.max())) if len(part) else (None, None)


def heatmap(log: pd.DataFrame, origin: str, out: Path) -> None:
    reads = classify_reads(log)
    reads = reads[reads["valid"]]
    if reads.empty:
        raise ValueError("no valid reads - cannot build heatmap")
    reads = reads.assign(bin=pd.cut(reads["ts"], N_BINS, labels=False))

    levels = sorted(reads["consistency_level"].unique())
    nodes = sorted(reads["node"].unique())
    fig, axes = plt.subplots(1, len(levels), figsize=(6 * len(levels), 4),
                           sharey=True, squeeze=False)
    w0, w1 = _window(log)
    for ax, level in zip(axes[0], levels):
        g = reads[reads["consistency_level"] == level]
        rate = (g.groupby(["node", "bin"], observed=True)["is_stale"]
                .mean().unstack(fill_value=np.nan)
                .reindex(index=nodes, columns=range(N_BINS)))
        im = ax.imshow(rate.to_numpy() * 100, aspect="auto", cmap="Reds",
                       vmin=0, origin="lower")
        ax.set_title(f"CL={level}")
        ax.set_xlabel("time bucket")
        ax.set_yticks(range(len(nodes)))
        ax.set_yticklabels(nodes)
        if w0 is not None:
            b0 = (w0 - log["ts"].min()) / (log["ts"].max() - log["ts"].min()) * N_BINS
            b1 = (w1 - log["ts"].min()) / (log["ts"].max() - log["ts"].min()) * N_BINS
            ax.axvspan(b0, b1, facecolor="none", edgecolor="blue",
                       lw=1.5, hatch="///", label="partition window")
            ax.legend(fontsize=8, loc="upper right")
        fig.colorbar(im, ax=ax, label="stale-read rate (%)")
    fig.suptitle(f"Consistency violations by node and time [{origin.upper()} DATA]")
    fig.tight_layout()
    fig.savefig(out / "consistency_heatmap.png", dpi=150)
    plt.close(fig)


def timeline(log: pd.DataFrame, origin: str, out: Path) -> None:
    reads = classify_reads(log)
    fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True,
                           gridspec_kw={"height_ratios": [2, 1]})
    t = pd.to_datetime(log["ts"], unit="ms")
    tr = pd.to_datetime(reads["ts"], unit="ms")

    ax = axes[0]
    for event, color in (("READ", "#1a5276"), ("WRITE", "#7d3c98")):
        sub = t[log["event"] == event]
        ax.hist(sub, bins=N_BINS, histtype="step", lw=1.4,
                label=f"{event.lower()}s", color=color)
    stale = reads[reads["is_stale"]]
    ax.scatter(pd.to_datetime(stale["ts"], unit="ms"),
               np.full(len(stale), ax.get_ylim()[1] * 0.05),
               marker="x", color="red", s=18, label="stale reads", zorder=3)
    ax.set_ylabel("events per bucket")
    ax.legend(fontsize=8)

    ax2 = axes[1]
    share = (reads.groupby(reads["consistency_level"])
             .apply(lambda g: g.set_index(pd.to_datetime(g["ts"], unit="ms"))
                    ["is_stale"].rolling(50, min_periods=10).mean(),
                    include_groups=False))
    for level, s in share.groupby(level=0):
        ax2.plot(s.index.get_level_values(-1), s.to_numpy() * 100,
                 lw=1.2, label=f"stale rate CL={level}")
    ax2.set_ylabel("stale rate (%, rolling)")
    ax2.set_xlabel("time")
    ax2.legend(fontsize=8)

    w0, w1 = _window(log)
    if w0 is not None:
        for a in axes:
            a.axvspan(pd.to_datetime(w0, unit="ms"),
                      pd.to_datetime(w1, unit="ms"),
                      color="orange", alpha=0.2)
            a.axvline(pd.to_datetime(w0, unit="ms"), color="darkorange",
                      ls="--", lw=1)
            a.axvline(pd.to_datetime(w1, unit="ms"), color="green",
                      ls="--", lw=1)
        axes[0].annotate("disruption start",
                         (pd.to_datetime(w0, unit="ms"), ax.get_ylim()[1] * .9),
                         fontsize=8, color="darkorange")
        axes[0].annotate("recovery",
                         (pd.to_datetime(w1, unit="ms"), ax.get_ylim()[1] * .8),
                         fontsize=8, color="green")

    axes[0].set_title(
        f"Read/Write timeline through the network partition "
        f"[{origin.upper()} DATA]")
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    fig.tight_layout()
    fig.savefig(out / "consistency_timeline.png", dpi=150)
    plt.close(fig)


def run(data_dir: Path, out_dir: Path) -> dict:
    log = pd.read_csv(data_dir / "consistency_log.csv")
    origin = detect_origin(data_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    heatmap(log, origin, out_dir)
    timeline(log, origin, out_dir)
    w0, w1 = _window(log)
    return {"origin": origin, "partition_window": [w0, w1]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data/sample")
    ap.add_argument("--out", default="results/figures")
    args = ap.parse_args()
    print(json.dumps(run(Path(args.data), Path(args.out)), indent=2))


if __name__ == "__main__":
    main()
