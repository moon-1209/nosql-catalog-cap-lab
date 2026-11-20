"""Ve bieu do tu cac run THAT da commit (legacy contract).

Chart nao cung ghi ro run_id nguon + ghi chu tinh trang du lieu.
Run CAP_ALL duoc gan nhan "INVALID RUN (setup defect)" - khong phai CAP result.

    .venv/bin/python scripts/chart_committed_runs.py \
        --experiments experiments --out results/committed_runs/charts
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from analyze_committed_runs import load_access_log, load_events

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def fig(ax_title=""):
    f, ax = plt.subplots(figsize=(8, 4.5))
    if ax_title:
        ax.set_title(ax_title, fontsize=11)
    return f, ax


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiments", default="experiments")
    ap.add_argument("--out", default="results/committed_runs/charts")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    E = args.experiments

    # ---- 1. E1a vs E1b latency (CAVEAT: workload khac nhau - zipf vs seq) ----
    runs = {
        "E1a schema A (zipf)": "E1a_ScyllaDB/20261118163502_71591fb6",
        "E1b schema B (sequential)": "E1b_ScyllaDB/20261118163826_70a13d55",
    }
    f, ax = fig("E1a vs E1b latency - real ScyllaDB run 18/11\n"
                "(workloads NOT comparable: zipf keys vs sequential keys - "
                "pending rerun voi contract v2)")
    for label, rd in runs.items():
        ops = load_access_log(os.path.join(E, rd, "access_log.csv"))
        lats = sorted(o["lat"] for o in ops if o["ok"])
        xs = [100.0 * i / len(lats) for i in range(len(lats))]
        ax.plot(xs, lats, label=f"{label}\n  run {rd.split('/')[-1]}")
    ax.set_xlabel("percentile (%)")
    ax.set_ylabel("latency (ms)")
    ax.legend(fontsize=8)
    f.tight_layout()
    f.savefig(os.path.join(args.out, "e1_latency_cdf.png"), dpi=130)
    plt.close(f)

    # ---- 2. CAP success rate by phase ----
    f, ax = fig("CAP E2-E5: success rate per phase - real ScyllaDB partition "
                "(docker network disconnect node3, ~20s)")
    caps = {
        "ONE\n20261118164217_51d70a18": "CAP_ONE/20261118164217_51d70a18",
        "QUORUM\n20261118164246_1e06bf4f":
            "CAP_QUORUM/20261118164246_1e06bf4f",
        "ALL\n20261118164314_7e93eceb\n(INVALID RUN - "
            "setup defect)": "CAP_ALL/20261118164314_7e93eceb",
    }
    x, w = range(len(caps)), 0.25
    for i, (label, rd) in enumerate(caps.items()):
        ops = load_access_log(os.path.join(E, rd, "access_log.csv"))
        evs = load_events(os.path.join(E, rd, "consistency_log.csv"))
        s = next(e for e in evs if e["event"].endswith("_start"))["ts"]
        e = next(e for e in evs if e["event"].endswith("_end"))["ts"]
        ph = [
            [o for o in ops if o["ts"] < s],
            [o for o in ops if s <= o["ts"] < e],
            [o for o in ops if o["ts"] >= e],
        ]
        pcts = [100.0 * sum(1 for o in p if o["ok"]) / len(p) if p else 0
                for p in ph]
        for j, (name, v) in enumerate(zip(("pre", "partition", "post"),
                                          pcts)):
            ax.bar(i + (j - 1) * w, v, w,
                   label=name if i == 0 else None,
                   color=["#4caf50", "#ff9800", "#2196f3"][j])
    ax.set_xticks(list(x))
    ax.set_xticklabels(list(caps.keys()), fontsize=7)
    ax.set_ylabel("success %")
    ax.set_ylim(0, 110)
    ax.legend()
    ax.text(2, 5, "fail ke ca\npre-partition\n= setup defect,\nkhong phai CAP",
            ha="center", fontsize=7, color="#c62828")
    f.tight_layout()
    f.savefig(os.path.join(args.out, "cap_success_phases.png"), dpi=130)
    plt.close(f)

    # ---- 3. E6 failover timeline ----
    f, ax = fig("E6 MongoDB failover - write latency timeline\n"
                "run 20261118165508_a46786bb (replSetStepDown 10s)")
    rd = "E6_Mongo_Failover/20261118165508_a46786bb"
    ops = load_access_log(os.path.join(E, rd, "access_log.csv"))
    evs = load_events(os.path.join(E, rd, "consistency_log.csv"))
    t0 = ops[0]["ts"]
    ts = [(o["ts"] - t0) / 1000.0 for o in ops]
    lats = [o["lat"] for o in ops]
    ax.plot(ts, lats, ".", ms=2, label="write op")
    for e in evs:
        lbl = "stepdown" if "start" in e["event"] else "elected"
        ax.axvline((e["ts"] - t0) / 1000.0, ls="--",
                   c="red" if "start" in e["event"] else "green",
                   label=lbl)
    ax.set_xlabel("t (s)")
    ax.set_ylabel("latency (ms)")
    ax.legend()
    f.tight_layout()
    f.savefig(os.path.join(args.out, "e6_failover_timeline.png"), dpi=130)
    plt.close(f)

    # ---- 4. LWT outcome ----
    f, ax = fig("LWT oversell: 50 buyers, 1 item - run 20261118164826_d623b720")
    ops = load_access_log(
        os.path.join(E, "LWT/20261118164826_d623b720/access_log.csv"))
    ok = sum(1 for o in ops if o["ok"])
    ax.bar(["won (was_applied)", "lost"], [ok, len(ops) - ok],
           color=["#4caf50", "#ef5350"])
    ax.set_ylabel("ops")
    for i, v in enumerate([ok, len(ops) - ok]):
        ax.text(i, v + 0.5, str(v), ha="center")
    f.tight_layout()
    f.savefig(os.path.join(args.out, "lwt_outcome.png"), dpi=130)
    plt.close(f)

    print("charts ->", args.out)


if __name__ == "__main__":
    main()
