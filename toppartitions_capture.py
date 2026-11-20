#!/usr/bin/env python3
"""
toppartitions_capture.py — chụp `nodetool toppartitions` trên MỌI node CÙNG LÚC.

LƯU Ý (đính chính so với bản kế hoạch): `toppartitions` KHÔNG phải metric của Prometheus.
Đây là lệnh nodetool (gọi REST API cổng 10000 của từng node), lấy mẫu các partition
nóng nhất mà CHÍNH node đó phục vụ trong một khoảng thời gian. Vì vậy phải chạy trên
tất cả node song song rồi gộp lại; còn tải theo node/shard thì lấy từ Prometheus
(hot_partition_audit.py).

    ./toppartitions_capture.py --ks shop --cf products_by_category --duration-ms 30000
    ./toppartitions_capture.py --parse-only raw_scylla-node1.txt      # chỉ thử bộ phân tích

Kết quả (--out-dir, mặc định evidence/tuan2/toppartitions_<thời_gian>/):
    raw_<node>.txt            output gốc của nodetool
    toppartitions.csv         node, sampler, rank, ks, cf, partition_key, count, error, cardinality, ...
    toppartitions_summary.json  gộp theo partition trên toàn cụm + tỉ trọng của top-1/top-5
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB_ROOT / "lib"))
import labctl  # noqa: E402
from promlib import write_csv  # noqa: E402

_SAMPLER = re.compile(r"^(READ|WRITE)S Sampler:")
_CARD = re.compile(r"Cardinality:\s*~?(\d+)\s*\((\d+) capacity\)")
_PART = re.compile(r"^\((?P<ks>[^:()]+):(?P<cf>[^)]+)\)\s+(?P<key>.*)$")


def parse_toppartitions(text: str) -> list[dict]:
    """Tách output của scylla nodetool toppartitions thành các bản ghi."""
    rows, sampler, card, cap, rank = [], None, None, None, 0
    for raw in text.splitlines():
        line = raw.strip()
        m = _SAMPLER.match(line)
        if m:
            sampler, card, cap, rank = m.group(1).lower() + "s", None, None, 0
            continue
        m = _CARD.search(line)
        if m:
            card, cap = int(m.group(1)), int(m.group(2))
            continue
        if not sampler or not line or line.startswith("Top ") or line.startswith("Nothing recorded"):
            continue
        if line.startswith("Partition") and "Count" in line:
            continue
        parts = line.rsplit(None, 2)
        if len(parts) != 3 or not parts[1].lstrip("-").isdigit() or not parts[2].lstrip("-").isdigit():
            continue
        rank += 1
        pm = _PART.match(parts[0])
        rows.append({
            "sampler": sampler, "rank": rank,
            "ks": pm.group("ks") if pm else "", "cf": pm.group("cf") if pm else "",
            "partition_key": pm.group("key") if pm else parts[0],
            "count": int(parts[1]), "error": int(parts[2]),
            "cardinality": card, "capacity": cap,
        })
    return rows


def capture(node: str, ks: str, cf: str, duration_ms: int, capacity: int, top: int) -> tuple[str, str, int]:
    cmd = ["docker", "exec", node, "nodetool", "toppartitions",
           "--ks-filters", ks, "--cf-filters", f"{ks}:{cf}",
           "-d", str(duration_ms), "-s", str(capacity), "-k", str(top)]
    p = labctl.run(cmd, timeout=duration_ms / 1000 + 90)
    return node, (p.stdout if p.returncode == 0 else p.stdout + p.stderr), p.returncode


def summarize(rows: list[dict]) -> dict:
    out = {}
    for sampler in ("reads", "writes"):
        agg: dict[str, int] = {}
        for r in rows:
            if r["sampler"] == sampler:
                agg[r["partition_key"]] = agg.get(r["partition_key"], 0) + r["count"]
        total = sum(agg.values())
        top = sorted(agg.items(), key=lambda kv: -kv[1])
        out[sampler] = {
            "sum_topk_counts": total,
            "top": [{"partition_key": k, "count": v, "share_of_topk": (v / total) if total else None}
                    for k, v in top[:20]],
            "top1_share_of_topk": (top[0][1] / total) if total else None,
            "top5_share_of_topk": (sum(v for _, v in top[:5]) / total) if total else None,
        }
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ks")
    ap.add_argument("--cf")
    ap.add_argument("--duration-ms", type=int, default=30000)
    ap.add_argument("--capacity", type=int, default=1024, help="càng lớn càng chính xác (mặc định nodetool: 256)")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--nodes", help="danh sách container, mặc định mọi node scylla đang chạy")
    ap.add_argument("--out-dir")
    ap.add_argument("--parse-only", nargs="+", metavar="RAW_FILE", help="chỉ phân tích file output có sẵn")
    a = ap.parse_args(argv)

    if a.parse_only:
        for f in a.parse_only:
            rows = parse_toppartitions(Path(f).read_text(encoding="utf-8"))
            print(json.dumps({"file": f, "rows": rows, "summary": summarize(rows)}, ensure_ascii=False, indent=2))
        return 0

    if not (a.ks and a.cf):
        ap.error("cần --ks và --cf")
    if a.top >= a.capacity:
        ap.error("--top phải nhỏ hơn --capacity (ràng buộc của nodetool)")
    nodes = a.nodes.split(",") if a.nodes else labctl.scylla_nodes()
    if not nodes:
        print("Không có node scylla nào đang chạy", file=sys.stderr)
        return 1
    out = Path(a.out_dir) if a.out_dir else labctl.EVIDENCE_DIR / "tuan2" / f"toppartitions_{time.strftime('%Y%m%d_%H%M%S')}"
    out.mkdir(parents=True, exist_ok=True)

    ts_start = time.time_ns() // 1_000_000
    print(f"Lấy mẫu toppartitions {a.ks}.{a.cf} trong {a.duration_ms / 1000:g}s trên {', '.join(nodes)} ...")
    with ThreadPoolExecutor(max_workers=len(nodes)) as ex:
        results = list(ex.map(lambda n: capture(n, a.ks, a.cf, a.duration_ms, a.capacity, a.top), nodes))
    ts_end = time.time_ns() // 1_000_000

    all_rows = []
    for node, text, rc in results:
        (out / f"raw_{node}.txt").write_text(text, encoding="utf-8")
        if rc != 0:
            print(f"[WARN] {node}: nodetool lỗi (rc={rc}) — xem raw_{node}.txt", file=sys.stderr)
        for r in parse_toppartitions(text):
            all_rows.append({"node": node, **r})

    header = ["node", "sampler", "rank", "ks", "cf", "partition_key", "count", "error",
              "cardinality", "capacity", "duration_ms", "ts_start_ms", "ts_end_ms"]
    write_csv(out / "toppartitions.csv", header,
              ([r["node"], r["sampler"], r["rank"], r["ks"], r["cf"], r["partition_key"], r["count"], r["error"],
                r["cardinality"], r["capacity"], a.duration_ms, ts_start, ts_end] for r in all_rows))
    summ = {"ks": a.ks, "cf": a.cf, "nodes": nodes, "duration_ms": a.duration_ms, "capacity": a.capacity,
            "ts_start_ms": ts_start, "ts_end_ms": ts_end, "cluster": summarize(all_rows),
            "per_node_cardinality": {n: next((r["cardinality"] for r in all_rows if r["node"] == n), None)
                                     for n in nodes}}
    (out / "toppartitions_summary.json").write_text(json.dumps(summ, ensure_ascii=False, indent=2), encoding="utf-8")

    for sampler in ("reads", "writes"):
        s = summ["cluster"][sampler]
        print(f"\n{sampler.upper()} — top partition gộp toàn cụm (tỉ trọng trong top-{a.top} mỗi node):")
        for i, t in enumerate(s["top"][:10], 1):
            share = f"{t['share_of_topk'] * 100:5.1f}%" if t["share_of_topk"] is not None else "  n/a"
            print(f"  {i:>2}. {t['partition_key'][:50]:<50} {t['count']:>10}  {share}")
    print(f"\n→ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
