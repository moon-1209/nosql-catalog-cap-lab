"""Top-partitions analysis: which CQL partitions attract the most traffic.

Reads an access log (`ts, request_id, op, category_id, product_id,
latency_ms`) and computes per-partition request statistics under both
schemas:

  Schema A  partition = (category_id)
  Schema B  partition = (category_id, bucket)  with
            bucket = crc32(product_id) % num_buckets

Metrics per partition: reads, writes, total traffic, share of total.
Aggregates: mean / max / min / std / max-mean ratio over partitions.
Output marks the data origin ("simulated" vs observed) read from the
dataset manifest - never mix the two silently.

CLI:
  python -m src.catalog_analysis.top_partitions \
      --data data/sample --top 10 --out results/top_partitions
"""

from __future__ import annotations

import argparse
import binascii
import json
from pathlib import Path

import numpy as np
import pandas as pd


def bucket_of(product_id: str, num_buckets: int) -> int:
    return binascii.crc32(product_id.encode()) % num_buckets


def partition_loads(access: pd.DataFrame, schema: str,
                    num_buckets: int) -> pd.DataFrame:
    """Per-partition read/write/total counts for schema 'a' or 'b'."""
    df = access
    if schema == "b":
        df = df.assign(
            bucket=df["product_id"].map(lambda p: bucket_of(p, num_buckets))
        )
        keys = ["category_id", "bucket"]
    else:
        keys = ["category_id"]

    counts = df.groupby(keys)["op"].value_counts().unstack(fill_value=0)
    for col in ("READ", "WRITE"):
        if col not in counts.columns:
            counts[col] = 0
    loads = counts.rename(columns={"READ": "reads", "WRITE": "writes"})
    loads["total"] = loads["reads"] + loads["writes"]
    loads["share"] = loads["total"] / loads["total"].sum()
    loads["latency_ms_mean"] = df.groupby(keys)["latency_ms"].mean()
    return loads.sort_values("total", ascending=False)


def summarise(loads: pd.DataFrame) -> dict:
    t = loads["total"]
    return {
        "partitions": int(len(t)),
        "total_requests": int(t.sum()),
        "mean_requests": float(t.mean()),
        "median_requests": float(t.median()),
        "max_requests": int(t.max()),
        "min_requests": int(t.min()),
        "std_requests": float(t.std()),
        "max_mean_ratio": float(t.max() / t.mean()) if t.mean() else None,
        "top_partition_share": float(t.max() / t.sum()) if t.sum() else None,
    }


def detect_origin(data_dir: Path) -> str:
    manifest = data_dir / "manifest.json"
    if manifest.exists():
        return json.loads(manifest.read_text()).get("origin", "unknown")
    return "unknown"


def run(data_dir: Path, out_dir: Path, top_n: int = 10,
        num_buckets: int = 16) -> dict:
    access = pd.read_csv(data_dir / "access_log.csv")
    origin = detect_origin(data_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    result = {"origin": origin, "top_n": top_n, "schemas": {}}
    for schema in ("a", "b"):
        loads = partition_loads(access, schema, num_buckets)
        loads.reset_index().to_csv(
            out_dir / f"partition_loads_schema_{schema}.csv", index=False)
        result["schemas"][schema] = {
            "summary": summarise(loads),
            "top": loads.head(top_n).reset_index()[
                ["category_id"] + (["bucket"] if schema == "b" else [])
                + ["reads", "writes", "total", "share"]
            ].to_dict("records"),
        }

    (out_dir / "summary.json").write_text(json.dumps(result, indent=2))
    _write_report(result, out_dir / "report.md")
    return result


def _write_report(result: dict, path: Path) -> None:
    lines = [
        "# Top Partitions Report",
        "",
        f"Data origin: **{result['origin']}** "
        + ("(simulated workload - replace with observed ScyllaDB logs for "
           "real measurements)" if result["origin"] == "simulated" else ""),
        "",
    ]
    for schema, r in result["schemas"].items():
        s = r["summary"]
        lines += [
            f"## Schema {schema.upper()}",
            "",
            f"- partitions: {s['partitions']}",
            f"- total requests: {s['total_requests']:,}",
            f"- mean / median / std per partition: {s['mean_requests']:.1f}"
            f" / {s['median_requests']:.1f} / {s['std_requests']:.1f}",
            f"- max partition load: {s['max_requests']:,}"
            f" ({s['top_partition_share']:.1%} of all traffic)",
            f"- max/mean ratio: {s['max_mean_ratio']:.2f}",
            "",
            f"Top {result['top_n']} partitions:",
            "",
            "| partition | reads | writes | total | share |",
            "|---|---|---|---|---|",
        ]
        for row in r["top"]:
            key = row["category_id"] + (
                f"/b{row['bucket']}" if "bucket" in row else "")
            lines.append(
                f"| {key} | {row['reads']} | {row['writes']} | "
                f"{row['total']} | {row['share']:.2%} |")
        lines.append("")
    path.write_text("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data/sample")
    ap.add_argument("--out", default="results/top_partitions")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--num-buckets", type=int, default=16)
    args = ap.parse_args()
    result = run(Path(args.data), Path(args.out), args.top, args.num_buckets)
    print(json.dumps({k: v["summary"] for k, v in result["schemas"].items()},
                     indent=2))


if __name__ == "__main__":
    main()
