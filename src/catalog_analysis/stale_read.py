"""Stale-read analysis for the consistency experiments.

Definitions
-----------
A **WRITE** event commits `version` for `key` at `ts`.
A **READ** event returns `version` for `key` at `ts`.

A READ is **stale** iff, at `read.ts`, the latest committed version of
`key` is strictly newer than the returned version::

    is_stale = read.version < max(w.version for w in writes[key]
                                  if w.ts <= read.ts)

A READ with **no committed write before it** is *unverifiable* - the log
cannot prove freshness or staleness, so it is excluded from the
denominator::

    stale_read_rate = stale_reads / total_valid_reads * 100  (%)

Rates are broken down by `consistency_level`, `network_state`, `node`,
and by phase (before / during / after the network-partition window).

CLI:
  python -m src.catalog_analysis.stale_read \
      --data data/sample --out results/stale_read
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.catalog_analysis.top_partitions import detect_origin


def classify_reads(log: pd.DataFrame) -> pd.DataFrame:
    """Return READ rows with `latest_committed`, `is_stale`, `valid`, `phase`."""
    reads = log[log["event"] == "READ"].sort_values("ts")
    writes = (log[log["event"] == "WRITE"][["key", "ts", "version"]]
              .sort_values("ts"))

    merged = pd.merge_asof(reads, writes, on="ts", by="key",
                           suffixes=("", "_committed"))
    merged = merged.rename(columns={"version_committed": "latest_committed"})
    merged["valid"] = merged["latest_committed"].notna()
    merged["is_stale"] = merged["valid"] & (
        merged["version"] < merged["latest_committed"])

    # phase: before / during / after the PARTITIONED window (if any)
    part = log.loc[log["network_state"] == "PARTITIONED", "ts"]
    if len(part):
        start, end = part.min(), part.max()
        merged["phase"] = "PARTITIONED"
        merged.loc[merged["ts"] < start, "phase"] = "PRE_PARTITION"
        merged.loc[merged["ts"] > end, "phase"] = "POST_PARTITION"
    else:
        merged["phase"] = "NORMAL"
    return merged


def _rate(group: pd.DataFrame) -> dict:
    valid = int(group["valid"].sum())
    stale = int(group["is_stale"].sum())
    return {
        "reads": int(len(group)),
        "valid_reads": valid,
        "unverifiable_reads": int(len(group) - valid),
        "stale_reads": stale,
        "stale_read_rate_pct": round(stale / valid * 100, 4) if valid else None,
    }


def analyse(log: pd.DataFrame) -> dict:
    reads = classify_reads(log)
    out = {
        "total_reads": int(len(reads)),
        "overall": _rate(reads),
        "by_consistency_level": {
            str(k): _rate(g) for k, g in reads.groupby("consistency_level")},
        "by_network_state": {
            str(k): _rate(g) for k, g in reads.groupby("network_state")},
        "by_phase": {
            str(k): _rate(g) for k, g in reads.groupby("phase")},
        "by_node": {
            str(k): _rate(g) for k, g in reads.groupby("node")},
    }
    return out, reads


def run(data_dir: Path, out_dir: Path) -> dict:
    log = pd.read_csv(data_dir / "consistency_log.csv")
    origin = detect_origin(data_dir)
    result, reads = analyse(log)
    result["origin"] = origin

    out_dir.mkdir(parents=True, exist_ok=True)
    reads.to_csv(out_dir / "classified_reads.csv", index=False)
    (out_dir / "summary.json").write_text(json.dumps(result, indent=2))
    _write_report(result, out_dir / "report.md")
    return result


def _write_report(result: dict, path: Path) -> None:
    o = result["overall"]
    lines = [
        "# Stale Read Report",
        "",
        f"Data origin: **{result['origin']}**",
        "",
        "Definition: a READ is stale iff `version < latest committed "
        "version` for the same key at read time. "
        "`stale_read_rate = stale_reads / valid_reads * 100%`.",
        "",
        f"- total reads: {result['total_reads']:,}",
        f"- valid reads (decidable): {o['valid_reads']:,}",
        f"- unverifiable reads (no prior write): {o['unverifiable_reads']:,}",
        f"- stale reads: {o['stale_reads']:,}",
        f"- **stale read rate: "
        f"{o['stale_read_rate_pct'] if o['stale_read_rate_pct'] is not None else 'n/a'}%**",
        "",
        "## By consistency level",
        "",
        "| level | valid | stale | rate % |",
        "|---|---|---|---|",
    ]
    for lvl, r in sorted(result["by_consistency_level"].items()):
        rate = r["stale_read_rate_pct"]
        lines.append(f"| {lvl} | {r['valid_reads']} | {r['stale_reads']} | "
                     f"{rate if rate is not None else 'n/a'} |")
    lines += ["", "## By phase", "",
              "| phase | valid | stale | rate % |", "|---|---|---|---|"]
    for ph, r in sorted(result["by_phase"].items()):
        rate = r["stale_read_rate_pct"]
        lines.append(f"| {ph} | {r['valid_reads']} | {r['stale_reads']} | "
                     f"{rate if rate is not None else 'n/a'} |")
    lines += [
        "",
        "Note: rates under `simulated` origin reflect the seeder's "
        "injected stale probabilities, not real ScyllaDB behaviour.",
    ]
    path.write_text("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data/sample")
    ap.add_argument("--out", default="results/stale_read")
    args = ap.parse_args()
    res = run(Path(args.data), Path(args.out))
    print(json.dumps(res["overall"], indent=2))
    print(json.dumps(res["by_consistency_level"], indent=2))


if __name__ == "__main__":
    main()
