#!/usr/bin/env python3
"""
mini_load.py — bộ tạo tải CQL nhỏ để Lâm TỰ KIỂM TRA pipeline giám sát và tạo tải nền
khi DEMO (để panel Grafana có chuyển động). KHÔNG thay thế harness đo chính thức của Duy.

Cài driver (một lần, trong WSL):  python3 -m pip install --user scylla-driver
Ví dụ:
    # tạo bảng + chạy 500 ops/s trong 5 phút, khóa phân bố Zipf (có hot key)
    python3 mini_load.py --create --rate 500 --duration 300 --dist zipf
    # client "nằm trong AZ3": chỉ nói chuyện với node3 (dùng khi demo partition)
    python3 mini_load.py --pin 10.88.88.13 --cl-read ONE --rate 50 --duration 120
Mỗi giây in 1 dòng: ok ghi/đọc, lỗi Unavailable / Timeout / khác, p50/p99 (ms); --out ghi CSV.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import os
import random
import sys
import threading
import time
from collections import defaultdict

try:
    from cassandra import ConsistencyLevel, OperationTimedOut, ReadTimeout, Unavailable, WriteTimeout
    from cassandra.cluster import EXEC_PROFILE_DEFAULT, Cluster, ExecutionProfile, NoHostAvailable
    from cassandra.policies import DCAwareRoundRobinPolicy, TokenAwarePolicy, WhiteListRoundRobinPolicy
except ImportError:
    sys.exit("Chưa có driver: python3 -m pip install --user scylla-driver")

try:
    from cassandra.io.libevreactor import LibevConnection as ConnClass
except Exception:  # noqa: BLE001  (Python 3.12+ không còn asyncore → dùng asyncio)
    from cassandra.io.asyncioreactor import AsyncioConnection as ConnClass


def classify(exc: BaseException) -> str:
    if isinstance(exc, Unavailable):
        return "unavailable"
    if isinstance(exc, (WriteTimeout, ReadTimeout, OperationTimedOut)):
        return "timeout"
    if isinstance(exc, NoHostAvailable):
        errs = list(getattr(exc, "errors", {}).values())
        if errs and all(isinstance(e, Unavailable) for e in errs):
            return "unavailable"
        return "nohost"
    return "other"


class Stats:
    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.c = defaultdict(int)
        self.lat = []

    def ok(self, kind: str, ms: float):
        with self.lock:
            self.c[f"ok_{kind}"] += 1
            self.lat.append(ms)

    def err(self, kind: str, cat: str):
        with self.lock:
            self.c[f"err_{cat}"] += 1
            self.c[f"err_{kind}"] += 1

    def snapshot(self):
        with self.lock:
            c, lat = dict(self.c), sorted(self.lat)
            self.reset()
        def pct(q):
            return lat[min(len(lat) - 1, int(q * len(lat)))] if lat else float("nan")
        return c, pct(0.50), pct(0.99)


def zipf_cdf(n: int, s: float) -> list[float]:
    w = [1.0 / (k ** s) for k in range(1, n + 1)]
    tot, acc, out = sum(w), 0.0, []
    for x in w:
        acc += x
        out.append(acc / tot)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hosts", default=os.environ.get("CQL_HOSTS", "10.88.88.11,10.88.88.12,10.88.88.13"))
    ap.add_argument("--dc", default="dc1")
    ap.add_argument("--pin", help="chỉ gửi request tới 1 node (IP) — mô phỏng client nằm trong 1 AZ")
    ap.add_argument("--ks", default="lab_load")
    ap.add_argument("--table", default="kv")
    ap.add_argument("--create", action="store_true", help="tạo keyspace RF=3 + bảng nếu chưa có")
    ap.add_argument("--rate", type=float, default=200, help="ops/giây mục tiêu (open-loop)")
    ap.add_argument("--duration", type=float, default=60)
    ap.add_argument("--write-ratio", type=float, default=0.3)
    ap.add_argument("--keys", type=int, default=10000)
    ap.add_argument("--dist", choices=["uniform", "zipf"], default="uniform")
    ap.add_argument("--zipf-s", type=float, default=1.1)
    ap.add_argument("--cl-write", default="QUORUM")
    ap.add_argument("--cl-read", default="QUORUM")
    ap.add_argument("--max-inflight", type=int, default=256)
    ap.add_argument("--out", help="ghi CSV theo từng giây")
    a = ap.parse_args()

    hosts = [a.pin] if a.pin else a.hosts.split(",")
    lbp = WhiteListRoundRobinPolicy([a.pin]) if a.pin else TokenAwarePolicy(DCAwareRoundRobinPolicy(local_dc=a.dc))
    profile = ExecutionProfile(load_balancing_policy=lbp, request_timeout=12)
    cluster = Cluster(hosts, execution_profiles={EXEC_PROFILE_DEFAULT: profile}, connection_class=ConnClass,
                      protocol_version=4, connect_timeout=5)
    session = cluster.connect()

    if a.create:
        session.execute(f"CREATE KEYSPACE IF NOT EXISTS {a.ks} WITH replication = "
                        "{'class': 'NetworkTopologyStrategy', 'replication_factor': 3}")
        session.execute(f"CREATE TABLE IF NOT EXISTS {a.ks}.{a.table} (k text PRIMARY KEY, v bigint, ts timestamp)")

    w_stmt = session.prepare(f"UPDATE {a.ks}.{a.table} SET v = ?, ts = toTimestamp(now()) WHERE k = ?")
    r_stmt = session.prepare(f"SELECT v FROM {a.ks}.{a.table} WHERE k = ?")
    w_stmt.consistency_level = getattr(ConsistencyLevel, a.cl_write.upper())
    r_stmt.consistency_level = getattr(ConsistencyLevel, a.cl_read.upper())

    cdf = zipf_cdf(a.keys, a.zipf_s) if a.dist == "zipf" else None
    stats, sem = Stats(), threading.BoundedSemaphore(a.max_inflight)
    seq = [0]

    def pick_key() -> str:
        i = bisect.bisect_left(cdf, random.random()) if cdf else random.randrange(a.keys)
        return f"k{min(i, a.keys - 1)}"

    def fire():
        is_write = random.random() < a.write_ratio
        kind = "w" if is_write else "r"
        key = pick_key()
        t0 = time.perf_counter()
        if not sem.acquire(blocking=False):
            stats.err(kind, "client_overload")
            return
        seq[0] += 1
        fut = session.execute_async(w_stmt, (seq[0], key)) if is_write else session.execute_async(r_stmt, (key,))

        def on_ok(_res):
            stats.ok(kind, (time.perf_counter() - t0) * 1000)
            sem.release()

        def on_err(exc):
            stats.err(kind, classify(exc))
            sem.release()
        fut.add_callbacks(on_ok, on_err)

    writer = None
    if a.out:
        f = open(a.out, "w", newline="", encoding="utf-8")
        writer = csv.writer(f)
        writer.writerow(["ts_ms", "ok_w", "ok_r", "err_unavailable", "err_timeout", "err_nohost", "err_other",
                         "err_client_overload", "p50_ms", "p99_ms"])
    print(f"mini_load → {hosts} | {a.rate:g} ops/s | {a.dist} | CL ghi={a.cl_write} đọc={a.cl_read}"
          f"{' | PIN ' + a.pin if a.pin else ''}")
    print(f"{'giờ':<9}{'ok_w':>7}{'ok_r':>7}{'unavail':>9}{'timeout':>9}{'nohost':>8}{'khác':>6}{'p50ms':>8}{'p99ms':>8}")

    interval = 1.0 / a.rate
    start = time.perf_counter()
    next_op, next_report = start, start + 1
    try:
        while time.perf_counter() - start < a.duration:
            now = time.perf_counter()
            while next_op <= now:
                fire()
                next_op += interval
            if now >= next_report:
                c, p50, p99 = stats.snapshot()
                row = [time.time_ns() // 1_000_000, c.get("ok_w", 0), c.get("ok_r", 0), c.get("err_unavailable", 0),
                       c.get("err_timeout", 0), c.get("err_nohost", 0), c.get("err_other", 0),
                       c.get("err_client_overload", 0), round(p50, 2), round(p99, 2)]
                print(f"{time.strftime('%H:%M:%S'):<9}{row[1]:>7}{row[2]:>7}{row[3]:>9}{row[4]:>9}{row[5]:>8}"
                      f"{row[6]:>6}{row[8]:>8}{row[9]:>8}", flush=True)
                if writer:
                    writer.writerow(row)
                next_report += 1
            time.sleep(max(0.0, min(next_op, next_report) - time.perf_counter()))
    except KeyboardInterrupt:
        pass
    finally:
        cluster.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
