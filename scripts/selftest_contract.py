"""Self-test Data Contract v2 - KHONG can ScyllaDB.

Sinh mot run dir synthetic (gan nhan origin="synthetic" trong manifest) qua
dung API data_contract ma cac experiment that dung -> dung de verify pipeline
Uyen doc duoc output truoc khi chay cluster that.

    python scripts/selftest_contract.py --out /tmp/duy_selftest

Sau do chay modules cua Uyen:
    python -m src.catalog_analysis.top_partitions --data <run_dir> --out r1
    python -m src.catalog_analysis.stale_read    --data <run_dir> --out r2
    python -m src.catalog_analysis.bootstrap_ci  --data <run_dir> --out r3
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_contract import (
    get_run_id, init_access_log, init_consistency_log, init_chaos_log,
    write_access_log, write_consistency_log, write_chaos_event,
    new_manifest, finalize_manifest,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    run_id = get_run_id()
    out_dir = os.path.join(args.out, "SELFTEST", run_id)
    os.makedirs(out_dir, exist_ok=True)
    access = init_access_log(out_dir)
    consistency = init_consistency_log(out_dir)
    chaos = init_chaos_log(out_dir)
    manifest = new_manifest(run_id, "SELFTEST", "contract_selftest")
    manifest["origin"] = "synthetic"  # KHONG gan observed - day la du lieu gia

    # access_log: 200 ops xen ke READ/WRITE, 2 category nong/lanh + 1 failed op
    for i in range(200):
        cat = "gaming" if i % 5 else "pets"
        write_access_log(access, run_id, "WRITE" if i % 2 == 0 else "READ",
                         latency_ms=1.5 + (i % 7) * 0.3,
                         success=(i != 77), category_id=cat,
                         product_id=f"pid-{i}",
                         error="" if i != 77 else "synthetic_timeout",
                         ts_ms=1700000000000 + i * 10)

    # consistency_log: 3 version tang dan/key; 1 READ stale co chu dich
    # (doc version 1 khi version 2 da commit -> merge_asof phai bat duoc)
    ts = 1700000000000
    for v in (1, 2, 3):
        write_consistency_log(consistency, run_id, "WRITE", "k1", v,
                              "ONE", "node1", "NORMAL", True,
                              ts_ms=ts + v * 100)
    write_consistency_log(consistency, run_id, "READ", "k1", 1,
                          "ONE", "node1", "NORMAL", True,
                          ts_ms=ts + 350)  # stale: v1 < v3
    write_consistency_log(consistency, run_id, "READ", "k1", 3,
                          "ONE", "node1", "NORMAL", True,
                          ts_ms=ts + 400)  # fresh
    # failed read trong partition - KHONG duoc tinh stale
    write_consistency_log(consistency, run_id, "READ", "k1", -1,
                          "ALL", "node3", "PARTITIONED", False,
                          error="Unavailable", ts_ms=ts + 500)
    write_chaos_event(chaos, run_id, "partition_start", target="node3",
                      ts_ms=ts + 450)

    finalize_manifest(out_dir, manifest, op_count=200,
                      extra={"note": "synthetic - khong phai du lieu cluster"})
    print(out_dir)


if __name__ == "__main__":
    main()
