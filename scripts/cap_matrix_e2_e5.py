"""E2-E5: CAP Matrix tren ScyllaDB voi network partition THAT.

Khac ban cu (remediation theo TEAM_PIPELINE_COMPLETENESS_AUDIT.md):
  * consistency_log.csv chi chua su kien READ/WRITE THAT co `version` ->
    stale_read.py cua Uyen tinh duoc stale rate (ban cu ghi chaos markers
    -> khong do duoc gi).
  * Chaos lifecycle (partition_start/end) tach sang chaos_events.csv.
  * Health gate TRUOC khi tiem loi + sau khi heal: verify du so node UP
    va 1 probe op o CL dang test thanh cong. Neu cluster chua khoe, run
    bi danh dau "aborted_unhealthy" trong manifest thay vi sinh du lieu sai.
    (Root cause CAP_ALL 100% fail: node3 chua rejoin sau run QUORUM -
    khong co wait-for-UP; + LocalAddressTranslator lam driver khong thay
    topology that.)
  * Khuyen nghi chay BEN TRONG lab-net (nhu E6) de dung IP that:
      SCYLLA_CONTACT_POINTS=10.88.88.11,10.88.88.12,10.88.88.13
    Translator 127.0.0.1 chi la fallback khi chay tu host.

Che do chaos:
  * --internal-chaos (mac dinh): script tu `docker network disconnect/connect`.
  * --external-chaos: KHONG goi docker - dung khi chay duoi chaos_runner
    cua Lam (--harness-cmd); truyen --partition-at/--heal-at trung voi
    timeline scenario de gan nhan network_state dung.
"""
import argparse
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cassandra import ConsistencyLevel
from data_contract import (
    get_run_id, get_output_dir, init_access_log, init_consistency_log,
    init_chaos_log, write_access_log, write_consistency_log,
    write_chaos_event, new_manifest, finalize_manifest, now_ms,
)

from lab_connect import connect, ensure_keyspace, wait_cluster_ready

EXPECTED_NODES = 3


def isolate_node(target="scylla-node3"):
    subprocess.run(["docker", "network", "disconnect", "lab-net", target],
                   capture_output=True)


def heal_node(target="scylla-node3"):
    subprocess.run(["docker", "network", "connect", "lab-net", target],
                   capture_output=True)


def run_experiment_for_cl(cl_name, cl_enum, args):
    run_id = get_run_id()
    out_dir = get_output_dir(f"CAP_{cl_name}", run_id)
    access_log = init_access_log(out_dir)
    consistency_log = init_consistency_log(out_dir)
    chaos_log = init_chaos_log(out_dir)
    manifest = new_manifest(run_id, f"CAP_{cl_name}", "cap_partition",
                            config={
                                "consistency_level": cl_name,
                                "partition_at_s": args.partition_at,
                                "heal_at_s": args.heal_at,
                                "duration_s": args.duration,
                                "chaos": "external" if args.external_chaos
                                         else "internal",
                            })
    state = {"network": "NORMAL", "version": 0}
    stop = threading.Event()

    print(f"\n--- CL={cl_name} ---")
    cluster, session = connect()
    ensure_keyspace(session, "catalog")
    session.execute(
        "CREATE TABLE IF NOT EXISTS cap_kv (key int PRIMARY KEY, "
        "version int, val text)")

    stmt_w = session.prepare(
        "INSERT INTO cap_kv (key, version, val) VALUES (?, ?, ?)")
    stmt_w.consistency_level = cl_enum
    stmt_r = session.prepare("SELECT version FROM cap_kv WHERE key = ?")
    stmt_r.consistency_level = cl_enum

    # ---- HEALTH GATE: cluster phai khoe truoc khi do ----
    n_up = wait_cluster_ready(cluster, label="pre-run")
    manifest["extra"]["pre_run_up_nodes"] = n_up
    if n_up < EXPECTED_NODES:
        finalize_manifest(out_dir, manifest, op_count=0,
                          extra={"status": "aborted_unhealthy_cluster",
                                 "detail": f"chi {n_up}/{EXPECTED_NODES} "
                                           "node UP - khong phai ket qua CAP"})
        print(f"ABORT {cl_name}: chi {n_up} node UP - rerun sau khi heal xong")
        cluster.shutdown()
        return
    # Probe op o CL dang test - neu ALL khong ghi duoc khi healthy thi dung
    try:
        session.execute(stmt_w, (0, 0, "probe"))
    except Exception as e:
        finalize_manifest(out_dir, manifest, op_count=0,
                          extra={"status": "aborted_probe_failed",
                                 "detail": str(e)[:200]})
        print(f"ABORT {cl_name}: probe WRITE that bai khi healthy: {e}")
        cluster.shutdown()
        return

    def workload():
        op_seq = 0
        while not stop.is_set():
            op_seq += 1
            key = op_seq % 100
            # WRITE: version = op_seq (monotonic per key vi key<100 va seq tang)
            state["version"] += 1
            v = state["version"]
            t0 = time.perf_counter()
            try:
                session.execute(stmt_w, (key, v, f"val{v}"))
                lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "WRITE", lat, True,
                                 product_id=str(key))
                write_consistency_log(consistency_log, run_id, "WRITE",
                                      key, v, cl_name, args.node_label,
                                      state["network"], True)
            except Exception as e:
                lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "WRITE", lat, False,
                                 product_id=str(key), error=str(e)[:80])
                write_consistency_log(consistency_log, run_id, "WRITE",
                                      key, v, cl_name, args.node_label,
                                      state["network"], False,
                                      error=type(e).__name__)
            # READ: log version QUAN SAT duoc -> tinh stale boi Uyen
            t0 = time.perf_counter()
            try:
                row = session.execute(stmt_r, (key,)).one()
                observed = row.version if row else 0
                lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "READ", lat, True,
                                 product_id=str(key))
                write_consistency_log(consistency_log, run_id, "READ",
                                      key, observed, cl_name, args.node_label,
                                      state["network"], True)
            except Exception as e:
                lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "READ", lat, False,
                                 product_id=str(key), error=str(e)[:80])
                write_consistency_log(consistency_log, run_id, "READ",
                                      key, -1, cl_name, args.node_label,
                                      state["network"], False,
                                      error=type(e).__name__)
            time.sleep(args.interval_ms / 1000.0)

    t = threading.Thread(target=workload)
    t.start()
    t0_run = time.time()

    # Healthy phase
    time.sleep(args.partition_at)
    write_chaos_event(chaos_log, run_id, "partition_start",
                      target="scylla-node3", detail=f"CL={cl_name}")
    state["network"] = "PARTITIONED"
    if not args.external_chaos:
        print(">>> disconnect node3")
        isolate_node()

    # Partitioned phase
    time.sleep(max(0, args.heal_at - args.partition_at))
    if not args.external_chaos:
        heal_node()
    write_chaos_event(chaos_log, run_id, "partition_end",
                      target="scylla-node3")

    # Recovery phase - cho node rejoin THAT SU truoc khi gan nhan NORMAL lai
    # (root-cause fix: ban cu danh NORMAL ngay -> ops thoi gian rejoin bi
    #  gan sai trang thai; va node chua UP da sang run CL tiep theo).
    n_up = wait_cluster_ready(cluster, label="post-heal")
    manifest["extra"]["post_heal_up_nodes"] = n_up
    state["network"] = "NORMAL" if n_up >= EXPECTED_NODES else "PARTITIONED"
    remaining = args.duration - (time.time() - t0_run)
    if remaining > 0:
        time.sleep(remaining)

    stop.set()
    t.join()
    finalize_manifest(out_dir, manifest,
                      extra={"status": "completed"})
    print(f"--- xong {cl_name} -> {out_dir} ---")
    cluster.shutdown()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--partition-at", type=float, default=10.0,
                    help="giay tinh tu run start ma partition bat dau")
    ap.add_argument("--heal-at", type=float, default=30.0)
    ap.add_argument("--duration", type=float, default=45.0)
    ap.add_argument("--interval-ms", type=float, default=10.0)
    ap.add_argument("--node-label", default="client",
                    help="nhan 'node' trong consistency_log (coordinator)")
    ap.add_argument("--external-chaos", action="store_true",
                    help="khong goi docker - chay duoi chaos_runner cua Lam")
    ap.add_argument("--levels", default="ONE,QUORUM,ALL")
    args = ap.parse_args()

    levels = {"ONE": ConsistencyLevel.ONE,
              "QUORUM": ConsistencyLevel.QUORUM,
              "ALL": ConsistencyLevel.ALL}
    for name in args.levels.split(","):
        run_experiment_for_cl(name.strip(), levels[name.strip()], args)


if __name__ == "__main__":
    main()
