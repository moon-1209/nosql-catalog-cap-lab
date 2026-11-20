"""Phan tich cac run THU da commit trong experiments/ (Data Contract cu).

Muc dich: trich evidence that tu run 18/11 truoc khi contract v2 ra doi.
Script doc duoc CA dinh dang cu (ts ISO8601, op lowercase, khong manifest)
VA dinh dang v2 (epoch ms, READ/WRITE, manifest). Gan nhan ro
`origin=observed + contract=legacy` trong ket qua.

    python scripts/analyze_committed_runs.py --experiments experiments \
        --out results/committed_runs
"""
import argparse
import csv
import json
import os
from collections import defaultdict


def parse_ts(v):
    """Tra ve epoch ms float: chap nhan epoch int hoac ISO8601."""
    v = v.strip()
    try:
        return float(v)
    except ValueError:
        from datetime import datetime
        return datetime.fromisoformat(v).timestamp() * 1000.0


def load_access_log(path):
    ops = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ops.append({
                "ts": parse_ts(r["ts"]),
                "op": r["op"].strip().upper(),
                "lat": float(r["latency_ms"]),
                "ok": str(r["success"]).strip().lower() == "true",
                "err": r.get("error", ""),
                "detail": r.get("op_detail") or r["op"].strip().lower(),
            })
    ops.sort(key=lambda o: o["ts"])
    return ops


def load_events(path):
    """Chaos markers - o file cu chung nam trong consistency_log.csv."""
    if not os.path.exists(path):
        return []
    evs = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            evs.append({"ts": parse_ts(r["ts"]), "event": r["event"],
                        "target": r.get("key") or r.get("target", "")})
    return evs


def pct(n, d):
    return round(100.0 * n / d, 2) if d else None


def analyze_run(run_dir):
    ops = load_access_log(os.path.join(run_dir, "access_log.csv"))
    evs = load_events(os.path.join(run_dir, "consistency_log.csv"))
    if not evs:
        evs = load_events(os.path.join(run_dir, "chaos_events.csv"))
    if not ops:
        return None
    t0 = ops[0]["ts"]
    lat_all = [o["lat"] for o in ops if o["ok"]]
    out = {
        "run_dir": run_dir,
        "contract": "v2" if os.path.exists(
            os.path.join(run_dir, "manifest.json")) else "legacy",
        "n_ops": len(ops),
        "n_ok": sum(1 for o in ops if o["ok"]),
        "n_fail": sum(1 for o in ops if not o["ok"]),
        "duration_s": round((ops[-1]["ts"] - t0) / 1000.0, 2),
        "ops_per_s": round(len(ops) / max(0.001,
                         (ops[-1]["ts"] - t0) / 1000.0), 1),
        "latency_ms": {
            "mean": round(sum(lat_all) / len(lat_all), 2) if lat_all else None,
            "p50": sorted(lat_all)[len(lat_all) // 2] if lat_all else None,
            "p95": sorted(lat_all)[int(len(lat_all) * 0.95)]
                   if lat_all else None,
            "max": round(max(lat_all), 2) if lat_all else None,
        },
        "chaos_events": evs,
    }
    # Pha theo chaos event dau tien kieu *_start/_end
    starts = [e for e in evs if e["event"].endswith("_start")]
    ends = [e for e in evs if e["event"].endswith("_end")]
    if starts and ends:
        s, e = starts[0]["ts"], ends[0]["ts"]
        pre = [o for o in ops if o["ts"] < s]
        dur = [o for o in ops if s <= o["ts"] < e]
        post = [o for o in ops if o["ts"] >= e]
        out["phases"] = {
            "pre": {"n": len(pre), "ok_pct": pct(
                sum(1 for o in pre if o["ok"]), len(pre))},
            "during": {"n": len(dur), "ok_pct": pct(
                sum(1 for o in dur if o["ok"]), len(dur)),
                "duration_s": round((e - s) / 1000.0, 1)},
            "post": {"n": len(post), "ok_pct": pct(
                sum(1 for o in post if o["ok"]), len(post))},
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiments", default="experiments")
    ap.add_argument("--out", default="results/committed_runs")
    args = ap.parse_args()

    results = {}
    for exp in sorted(os.listdir(args.experiments)):
        exp_dir = os.path.join(args.experiments, exp)
        if not os.path.isdir(exp_dir):
            continue
        for run in sorted(os.listdir(exp_dir)):
            run_dir = os.path.join(exp_dir, run)
            if not os.path.isdir(run_dir) or not os.path.exists(
                    os.path.join(run_dir, "access_log.csv")):
                continue
            r = analyze_run(run_dir)
            if r:
                results[f"{exp}/{run}"] = r
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "analysis.json"), "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: {kk: r[kk] for kk in
                          ("n_ops", "n_ok", "n_fail", "contract")}
                      for k, r in results.items()}, indent=2))


if __name__ == "__main__":
    main()
