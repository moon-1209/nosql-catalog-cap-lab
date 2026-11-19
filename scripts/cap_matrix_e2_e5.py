"""E2-E5: CAP Matrix tren ScyllaDB voi Network Partition thuc te (Tich hop chaos.sh)."""
import time, subprocess, threading, os
from cassandra.cluster import Cluster
from cassandra import ConsistencyLevel
from cassandra.policies import AddressTranslator
from data_contract import (get_run_id, get_output_dir, init_access_log, write_access_log, init_consistency_log, write_consistency_log, write_manifest)

# Sử dụng đúng class giống hệt file E1a đã chạy thành công
class LocalAddressTranslator(AddressTranslator):
    def translate(self, addr):
        return '127.0.0.1'

def call_chaos(action, target, mode="full"):
    cmd = ["bash", "scripts/chaos.sh", action, target]
    if action == "partition":
        cmd.extend(["--mode", mode])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"[CHAOS] {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"[CHAOS ERROR] {e.stderr.strip()}")
        raise e

def run_experiment_for_cl(cl_name, cl_enum):
    run_id = get_run_id()
    out_dir = get_output_dir(f"CAP_{cl_name}", run_id)
    access_log = init_access_log(out_dir)
    consistency_log = init_consistency_log(out_dir)
    write_manifest(out_dir, run_id, f"CAP_{cl_name}", {"cl": cl_name, "chaos_tool": "chaos.sh"})
    
    print(f"\n--- Bat dau test Consistency Level: {cl_name} ---")
    
    # Bỏ port=9042, dùng đúng translator của E1a
    cluster = Cluster(['127.0.0.1'], address_translator=LocalAddressTranslator())
    session = cluster.connect()
    
    session.execute("CREATE KEYSPACE IF NOT EXISTS catalog WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3}")
    session.execute("CREATE TABLE IF NOT EXISTS catalog.product_cap (id int PRIMARY KEY, val int)")
    time.sleep(3)
    
    stmt_write = session.prepare("INSERT INTO catalog.product_cap (id, val) VALUES (?, ?)")
    stmt_write.consistency_level = cl_enum
    stmt_read = session.prepare("SELECT val FROM catalog.product_cap WHERE id = ?")
    stmt_read.consistency_level = cl_enum

    stop_event = threading.Event()
    def workload():
        op_count = 0
        while not stop_event.is_set():
            op_count += 1
            key = op_count % 100
            
            t0 = time.perf_counter()
            try:
                session.execute(stmt_write, (key, op_count))
                w_lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "WRITE", w_lat, True, product_id=str(key))
                write_consistency_log(consistency_log, run_id, "WRITE", str(key), str(op_count), cl_name, "node1", "normal", True)
            except Exception as e:
                w_lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "WRITE", w_lat, False, product_id=str(key), error=str(e)[:50])
                write_consistency_log(consistency_log, run_id, "WRITE", str(key), str(op_count), cl_name, "node1", "error", False, str(e)[:50])
            
            t0 = time.perf_counter()
            try:
                session.execute(stmt_read, (key,))
                r_lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "READ", r_lat, True, product_id=str(key))
                write_consistency_log(consistency_log, run_id, "READ", str(key), str(op_count), cl_name, "node1", "normal", True)
            except Exception as e:
                r_lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "READ", r_lat, False, product_id=str(key), error=str(e)[:50])
                write_consistency_log(consistency_log, run_id, "READ", str(key), str(op_count), cl_name, "node1", "error", False, str(e)[:50])
            
            time.sleep(0.01)

    t = threading.Thread(target=workload)
    t.start()
    time.sleep(3)
    
    write_consistency_log(consistency_log, run_id, "partition_start", "ALL", "0", cl_name, "node3", "disconnected", True)
    call_chaos("partition", "scylla-node3", mode="full")
    time.sleep(20)
    call_chaos("heal", "scylla-node3")
    write_consistency_log(consistency_log, run_id, "partition_end", "ALL", "0", cl_name, "node3", "reconnected", True)
    
    print(">>> Da phuc hoi mang. Cho 10s de cluster on dinh...")
    time.sleep(10)
    
    stop_event.set()
    t.join()
    cluster.shutdown()
    print(f"--- Hoan tat test {cl_name} ---")

if __name__ == "__main__":
    run_experiment_for_cl("ONE", ConsistencyLevel.ONE)
    run_experiment_for_cl("QUORUM", ConsistencyLevel.QUORUM)
    run_experiment_for_cl("ALL", ConsistencyLevel.ALL)