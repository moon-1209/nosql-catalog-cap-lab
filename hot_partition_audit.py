#!/usr/bin/env python3
"""
hot_partition_audit.py — trích metric tải TỪNG NODE và TỪNG SHARD từ Prometheus API,
tính chỉ số mất cân bằng max/mean, xuất CSV/JSON cho Uyên vẽ biểu đồ Schema A vs B.

    # cửa sổ lấy từ một run của chaos_runner (bỏ 60s warm-up đầu, 10s cuối)
    ./hot_partition_audit.py --run ../runs/E1-A_xxx --ks shop --cf products_by_category --label E1-A
    # hoặc tự chỉ định thời gian
    ./hot_partition_audit.py --start 2026-11-12T14:00:00+07:00 --end 2026-11-12T14:05:00+07:00 --label thu
    ./hot_partition_audit.py --last 10m
    # so sánh trước/sau tối ưu (bằng chứng cổng 15/11)
    ./hot_partition_audit.py compare E1-A/hot_partition_summary.json E1-B/hot_partition_summary.json --out so_sanh.md

CÁC GÓC NHÌN (view) được tính — và vì sao cần nhiều góc nhìn:
  intra_node_shard  max/mean giữa các shard TRONG CÙNG 1 node, lấy node tệ nhất. Đây là chỉ số
                    CHÍNH: Scylla là shard-per-core, 1 partition chỉ thuộc 1 shard trên mỗi replica,
                    nên hot partition = hot shard. Chỉ số này KHÔNG bị ảnh hưởng bởi topology
                    (node4 ở rack1 chỉ giữ ~50% dữ liệu nhưng các shard của nó vẫn phải đều nhau).
                    Cần SCYLLA_SMP ≥ 2.
  cluster_shard     max/mean giữa mọi shard của cụm (tham khảo).
  node              max/mean giữa các node. Với 3 node & RF=3 mọi node giữ mọi partition nên
                    view này luôn ≈ 1 → KHÔNG dùng để kết luận hot partition.
  node_normalized   tải node chia cho % sở hữu hiệu dụng (nodetool status ks cf). Dùng khi có
                    node4 (N > RF): khử phần lệch "cấu trúc" do rack1 có 2 node.
  coordinator       số request CQL mỗi node nhận với vai trò coordinator — nếu lệch là do client
                    (driver không token-aware / ghim 1 node), KHÔNG phải do schema.
  cpu_shard         max/mean CPU reactor giữa các shard.
Với n phần tử, max/mean nằm trong [1, n]: 1 = đều tuyệt đối; n = toàn bộ tải dồn vào 1 phần tử.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB_ROOT / "lib"))
import labctl  # noqa: E402
from promlib import (Prom, PromError, finite, fmt_iso, jsonable, load_run_window,  # noqa: E402
                     parse_duration, parse_time, summarize, write_csv)

VIEWS_ORDER = ["intra_node_shard", "cluster_shard", "node", "node_normalized", "coordinator", "cpu_shard"]


def sel(cluster: str, extra: str = "") -> str:
    parts = []
    if cluster:
        parts.append(f'cluster=~"{cluster}"')
    if extra:
        parts.append(extra)
    return "{" + ",".join(parts) + "}"


def build_queries(w: str, cluster: str, ks: str | None, cf: str | None) -> dict[str, str]:
    s = sel(cluster)
    q = {
        "shard_reads": f"sum by (instance, shard) (rate(scylla_database_total_reads{s}[{w}]))",
        "shard_writes": f"sum by (instance, shard) (rate(scylla_database_total_writes{s}[{w}]))",
        "shard_cpu": f"max by (instance, shard) (scylla_reactor_utilization{s})",
        "node_coord": f"sum by (instance) (rate(scylla_transport_requests_served{s}[{w}]))",
    }
    if ks and cf:
        t = sel(cluster, f'ks="{ks}",cf="{cf}"')
        q["table_reads"] = f"sum by (instance) (rate(scylla_column_family_read_latency_count{t}[{w}]))"
        q["table_writes"] = f"sum by (instance) (rate(scylla_column_family_write_latency_count{t}[{w}]))"
    return q


def fetch(prom: Prom, queries: dict[str, str], start: float, end: float, step: float):
    """→ data[metric][member][ts] = value ; member = (instance, shard) hoặc (instance, '')"""
    data: dict[str, dict[tuple, dict[float, float]]] = {}
    for name, expr in queries.items():
        series = prom.range(expr, start, end, step)
        d = defaultdict(dict)
        for labels, pts in series:
            member = (labels.get("instance", "?"), labels.get("shard", ""))
            for ts, v in pts:
                d[member][ts] = v
        data[name] = dict(d)
        print(f"  {name:<13} {len(d):>3} series   ← {expr}")
    return data


def combine_sum(a: dict, b: dict) -> dict:
    """Cộng 2 metric cùng member/timestamp (thiếu 1 bên thì lấy bên còn lại)."""
    out = defaultdict(dict)
    for src in (a, b):
        for m, pts in src.items():
            for ts, v in pts.items():
                if math.isnan(v):
                    continue
                out[m][ts] = out[m].get(ts, 0.0) + v
    return dict(out)


def group_by_node(shard_data: dict) -> dict:
    out = defaultdict(lambda: defaultdict(float))
    for (inst, _shard), pts in shard_data.items():
        for ts, v in pts.items():
            out[(inst, "")][ts] += v
    return {m: dict(p) for m, p in out.items()}


def ratio_stats(values: dict[tuple, float]) -> dict | None:
    xs = {m: v for m, v in values.items() if v is not None and not math.isnan(v)}
    if len(xs) < 2:
        return None
    vals = list(xs.values())
    mean = sum(vals) / len(vals)
    if mean <= 0:
        return None
    mx = max(vals)
    hottest = max(xs, key=xs.get)
    return {"max": mx, "mean": mean, "max_over_mean": mx / mean,
            "cv": statistics.pstdev(vals) / mean, "n": len(vals),
            "hottest": hottest[0] + (f"/s{hottest[1]}" if hottest[1] != "" else "")}


def imbalance_series(data: dict, timestamps: list[float], mode: str) -> list[tuple[float, dict]]:
    """mode: 'all' = so mọi member; 'intra' = so trong từng node rồi lấy node tệ nhất."""
    out = []
    for ts in timestamps:
        if mode == "all":
            st = ratio_stats({m: pts.get(ts) for m, pts in data.items()})
            if st:
                out.append((ts, st))
        else:
            per_node = defaultdict(dict)
            for (inst, shard), pts in data.items():
                per_node[inst][(inst, shard)] = pts.get(ts)
            best = None
            for inst, members in per_node.items():
                st = ratio_stats(members)
                if st and (best is None or st["max_over_mean"] > best["max_over_mean"]):
                    best = {**st, "worst_node": inst}
            if best:
                out.append((ts, best))
    return out


def normalize_by_ownership(node_data: dict, owns: dict[str, float]) -> dict:
    out = {}
    for (inst, shard), pts in node_data.items():
        o = owns.get(inst)
        if o:
            out[(inst, shard)] = {ts: v / (o / 100.0) for ts, v in pts.items()}
    return out


def member_table(data: dict, t_lo: float, t_hi: float) -> list[dict]:
    rows = []
    for (inst, shard), pts in sorted(data.items()):
        vals = finite(v for ts, v in pts.items() if t_lo <= ts <= t_hi)
        rows.append({"instance": inst, "shard": shard, "mean": (sum(vals) / len(vals)) if vals else math.nan})
    tot = sum(r["mean"] for r in rows if not math.isnan(r["mean"]))
    for r in rows:
        r["share_pct"] = (r["mean"] / tot * 100) if tot and not math.isnan(r["mean"]) else math.nan
    return rows


# ---------------------------------------------------------------------------
def audit(a) -> int:
    if a.run:
        t0, t1 = load_run_window(a.run)
        start, end = t0 + a.trim_start, t1 - a.trim_end
        label = a.label or Path(a.run).name
        out = Path(a.out_dir) if a.out_dir else Path(a.run) / "hot_partition"
    else:
        if a.last:
            end, start = time.time(), time.time() - parse_duration(a.last)
        elif a.start and a.end:
            start, end = parse_time(a.start), parse_time(a.end)
        else:
            print("Cần --run, hoặc --start/--end, hoặc --last", file=sys.stderr)
            return 2
        label = a.label or "audit"
        out = Path(a.out_dir) if a.out_dir else labctl.EVIDENCE_DIR / "tuan2" / f"hot_partition_{label}_{time.strftime('%Y%m%d_%H%M%S')}"
    if end - start < 3 * parse_duration(a.step):
        print(f"Cửa sổ quá ngắn ({end - start:.0f}s) sau khi cắt warm-up/cool-down", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)

    prom = Prom(a.prom)
    print(f"[{label}] Prometheus {a.prom} | {fmt_iso(start)} → {fmt_iso(end)} ({end - start:.0f}s) | "
          f"step {a.step}, rate[{a.window}]")
    queries = build_queries(a.window, a.cluster, a.ks, a.cf)
    try:
        data = fetch(prom, queries, start, end, parse_duration(a.step))
    except PromError as e:
        print(f"Lỗi truy vấn Prometheus: {e}", file=sys.stderr)
        return 1

    shard_ops = combine_sum(data.get("shard_reads", {}), data.get("shard_writes", {}))
    if not shard_ops:
        print("Không có dữ liệu scylla_database_total_* trong cửa sổ này (sai thời gian? Prometheus chưa cào?)",
              file=sys.stderr)
        return 1
    node_ops = group_by_node(shard_ops)
    table_ops = combine_sum(data.get("table_reads", {}), data.get("table_writes", {})) if a.ks else {}
    node_basis = table_ops if table_ops else node_ops

    owns: dict[str, float] = {}
    if a.ownership == "auto" and a.ks:
        try:
            owns = labctl.ownership(a.ks, a.cf)
        except Exception as e:  # noqa: BLE001
            print(f"[WARN] Không lấy được ownership tự động: {e}", file=sys.stderr)
    elif a.ownership and a.ownership != "auto":
        owns = {k: float(v) for k, v in (kv.split("=") for kv in a.ownership.split(","))}

    timestamps = sorted({ts for pts in shard_ops.values() for ts in pts})
    shard_counts = defaultdict(int)
    for inst, _ in shard_ops:
        shard_counts[inst] += 1
    views = {
        "intra_node_shard": imbalance_series(shard_ops, timestamps, "intra")
        if max(shard_counts.values()) >= 2 else [],
        "cluster_shard": imbalance_series(shard_ops, timestamps, "all"),
        "node": imbalance_series(node_basis, timestamps, "all"),
        "node_normalized": imbalance_series(normalize_by_ownership(node_basis, owns), timestamps, "all")
        if owns else [],
        "coordinator": imbalance_series(data.get("node_coord", {}), timestamps, "all"),
        "cpu_shard": imbalance_series(data.get("shard_cpu", {}), timestamps, "all"),
    }

    # ---- CSV dạng dài cho Uyên ----
    def long_rows():
        named = {"shard_ops": shard_ops, "node_ops": node_ops, **data}
        if table_ops:
            named["table_ops"] = table_ops
        for metric, d in named.items():
            for (inst, shard), pts in sorted(d.items()):
                for ts, v in sorted(pts.items()):
                    yield [int(ts * 1000), fmt_iso(ts), label, metric, inst, shard, f"{v:.6g}"]
    n_ts = write_csv(out / "hot_partition_timeseries.csv",
                     ["ts_ms", "iso", "label", "metric", "instance", "shard", "value"], long_rows())

    def imb_rows():
        for view, series in views.items():
            for ts, st in series:
                yield [int(ts * 1000), fmt_iso(ts), label, view, f"{st['max']:.6g}", f"{st['mean']:.6g}",
                       f"{st['max_over_mean']:.4f}", f"{st['cv']:.4f}", st["n"], st["hottest"],
                       st.get("worst_node", "")]
    write_csv(out / "hot_partition_imbalance.csv",
              ["ts_ms", "iso", "label", "view", "max", "mean", "max_over_mean", "cv", "n", "hottest", "worst_node"],
              imb_rows())

    summary = {
        "label": label, "prometheus": a.prom, "start_ms": int(start * 1000), "end_ms": int(end * 1000),
        "start_iso": fmt_iso(start), "end_iso": fmt_iso(end), "step": a.step, "rate_window": a.window,
        "ks": a.ks, "cf": a.cf, "node_basis": "table_ops" if table_ops else "node_ops(all tables)",
        "ownership_pct": owns, "queries": queries, "shards_per_node": dict(shard_counts),
        "views": {}, "members": {
            "shard_ops": member_table(shard_ops, start, end),
            "node_basis": member_table(node_basis, start, end),
        },
    }
    for view, series in views.items():
        ratios = [st["max_over_mean"] for _, st in series]
        hot = defaultdict(int)
        for _, st in series:
            hot[st.get("worst_node") or st["hottest"]] += 1
        summary["views"][view] = {
            "max_over_mean": summarize(ratios),
            "cv_mean": (sum(st["cv"] for _, st in series) / len(series)) if series else math.nan,
            "most_often_hottest": max(hot, key=hot.get) if hot else None,
            "n_members": series[0][1]["n"] if series else 0,
        }
    (out / "hot_partition_summary.json").write_text(
        json.dumps(jsonable(summary), ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- báo cáo ra màn hình ----
    print(f"\n{'view':<18}{'n':>4}{'p50 max/mean':>15}{'p95':>9}{'max':>9}   hay nóng nhất")
    for view in VIEWS_ORDER:
        v = summary["views"].get(view)
        if not v or v["max_over_mean"]["n"] == 0:
            print(f"{view:<18}{'-':>4}{'(không có dữ liệu)':>33}")
            continue
        m = v["max_over_mean"]
        print(f"{view:<18}{v['n_members']:>4}{m['p50']:>15.3f}{m['p95']:>9.3f}{m['max']:>9.3f}   {v['most_often_hottest']}")
    print("\nTải trung bình theo shard (ops/s):")
    for r in summary["members"]["shard_ops"]:
        print(f"  {r['instance']:<14} shard {r['shard']:<3} {r['mean']:>10.1f}  ({r['share_pct']:.1f}%)")
    print(f"\n→ {out}  ({n_ts} dòng timeseries)")
    return 0


# ---------------------------------------------------------------------------
def compare(paths: list[str], out_md: str | None) -> int:
    a = json.loads(Path(paths[0]).read_text(encoding="utf-8"))
    b = json.loads(Path(paths[1]).read_text(encoding="utf-8"))
    la, lb = a["label"], b["label"]
    lines = [f"# So sánh mất cân bằng tải: {la} vs {lb}", "",
             f"- {la}: {a['start_iso']} → {a['end_iso']} (bảng {a.get('ks')}.{a.get('cf')})",
             f"- {lb}: {b['start_iso']} → {b['end_iso']} (bảng {b.get('ks')}.{b.get('cf')})", "",
             f"| View | p50 max/mean {la} | p50 max/mean {lb} | Thay đổi | p95 {la} | p95 {lb} |",
             "|---|---:|---:|---:|---:|---:|"]
    verdicts = []
    for view in VIEWS_ORDER:
        va, vb = a["views"].get(view, {}), b["views"].get(view, {})
        ma, mb = (va.get("max_over_mean") or {}), (vb.get("max_over_mean") or {})
        pa, pb = ma.get("p50"), mb.get("p50")
        if pa is None or pb is None:
            lines.append(f"| {view} | – | – | – | – | – |")
            continue
        # đo mức "vượt quá cân bằng": (ratio - 1). Giảm phần vượt này mới là cải thiện thật.
        ea, eb = pa - 1, pb - 1
        if ea < 0.02 and eb < 0.02:
            change = "cả hai ≈ cân bằng"
        elif ea < 0.02:
            change = f"tăng lệch (+{eb:.2f})"
        else:
            change = f"{(eb - ea) / ea * 100:+.0f}% phần lệch"
        lines.append(f"| {view} | {pa:.3f} | {pb:.3f} | {change} | {ma.get('p95', float('nan')):.3f} | "
                     f"{mb.get('p95', float('nan')):.3f} |")
        if view == "intra_node_shard" and ea >= 0.02:
            verdicts.append(f"Chỉ số chính (shard trong cùng node): {la} = {pa:.2f}, {lb} = {pb:.2f} → phần lệch "
                            f"so với cân bằng thay đổi {(eb - ea) / ea * 100:+.0f}%.")
    lines += ["", "Cách đọc: 1.00 = tải chia đều tuyệt đối; với n phần tử, giá trị tối đa là n. "
              "Cột *Thay đổi* so sánh phần vượt (ratio − 1).", ""] + verdicts
    text = "\n".join(lines) + "\n"
    print(text)
    if out_md:
        Path(out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(out_md).write_text(text, encoding="utf-8")
        print(f"→ {out_md}")
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "compare":
        ap = argparse.ArgumentParser(prog="hot_partition_audit.py compare")
        ap.add_argument("summaries", nargs=2)
        ap.add_argument("--out")
        c = ap.parse_args(argv[1:])
        return compare(c.summaries, c.out)

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prom", default=labctl.LAB_ENV.get("PROM_URL", "http://localhost:9090"))
    ap.add_argument("--run", help="thư mục run của chaos_runner (đọc T0/T_end từ summary.json)")
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--last", help="vd 10m")
    ap.add_argument("--trim-start", type=float, default=60, help="bỏ N giây đầu (warm-up) khi dùng --run")
    ap.add_argument("--trim-end", type=float, default=10)
    ap.add_argument("--step", default="5s")
    ap.add_argument("--window", default="30s", help="cửa sổ rate()")
    ap.add_argument("--cluster", default=labctl.LAB_ENV.get("SCYLLA_CLUSTER_NAME", ""),
                    help="lọc nhãn cluster (chuỗi rỗng = không lọc)")
    ap.add_argument("--ks")
    ap.add_argument("--cf")
    ap.add_argument("--ownership", default="auto",
                    help="'auto' (nodetool status ks cf) | 'scylla-node1=50,scylla-node2=100,...' | ''")
    ap.add_argument("--label")
    ap.add_argument("--out-dir")
    return audit(ap.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
