"""E2-E5: CAP Matrix tren ScyllaDB voi Network Partition thuc te."""
import time
import subprocess
import threading
from cassandra.cluster import Cluster
from cassandra import ConsistencyLevel
from cassandra.policies import AddressTranslator
from data_contract import (
    get_run_id, get_output_dir,
    init_access_log, write_access_log,
    init_consistency_log, write_consistency_log
)

class LocalAddressTranslator(AddressTranslator):
    def translate(self, addr):
        return '127.0.0.1'

def isolate_node3():
    print(">>> Dang ngat mang Node 3 (Network Partition)...")
    subprocess.run(["docker", "network", "disconnect", "lab-net", "scylla-node3"], capture_output=True)

def restore_node3():
    print(">>> Dang phuc hoi mang Node 3...")
    subprocess.run(["docker", "network", "connect", "lab-net", "scylla-node3"], capture_output=True)

def run_experiment_for_cl(cl_name, cl_enum):
    run_id = get_run_id()
    out_dir = get_output_dir(f"CAP_{cl_name}", run_id)
    access_log = init_access_log(out_dir)
    consistency_log = init_consistency_log(out_dir)
    
    print(f"\n--- Bat dau test Consistency Level: {cl_name} ---")
    cluster = Cluster(['127.0.0.1'], address_translator=LocalAddressTranslator())
    session = cluster.connect()
    session.execute("CREATE KEYSPACE IF NOT EXISTS catalog WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3}")
    session.execute("CREATE TABLE IF NOT EXISTS catalog.product_cap (id int PRIMARY KEY, val int)")
    
    stmt_write = session.prepare("INSERT INTO catalog.product_cap (id, val) VALUES (?, ?)")
    stmt_write.consistency_level = cl_enum
    stmt_read = session.prepare("SELECT val FROM catalog.product_cap WHERE id = ?")
    stmt_read.consistency_level = cl_enum

    # Worker Thread chay workload lien tuc
    stop_event = threading.Event()
    def workload():
        op_count = 0
        while not stop_event.is_set():
            op_count += 1
            key = op_count % 100
            # Ghi log su kien vao consistency_log de danh dau trang thai mang
            is_normal = not stop_event.is_set() 
            
            # Write
            t0 = time.perf_counter()
            try:
                session.execute(stmt_write, (key, op_count))
                w_lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "write", w_lat, True, product_id=str(key))
            except Exception as e:
                w_lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "write", w_lat, False, product_id=str(key), error=str(e)[:50])
            
            # Read
            t0 = time.perf_counter()
            try:
                session.execute(stmt_read, (key,))
                r_lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "read", r_lat, True, product_id=str(key))
            except Exception as e:
                r_lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "read", r_lat, False, product_id=str(key), error=str(e)[:50])
            
            time.sleep(0.01) # 10ms interval

    # Chay ngam workload
    t = threading.Thread(target=workload)
    t.start()

    time.sleep(3) # Chay binh thuong 3s
    
    # Ghi log su kien bat dau partition
    write_consistency_log(consistency_log, run_id, "partition_start", "ALL", "1", cl_name, "scylla-node3", "disconnected", True)
    isolate_node3()
    
    time.sleep(20) # Giu partition trong 20s
    
    # Ghi log su kien phuc hoi
    restore_node3()
    write_consistency_log(consistency_log, run_id, "partition_end", "ALL", "1", cl_name, "scylla-node3", "reconnected", True)
    print(">>> Da phuc hoi mang. Cho 5s de cluster on dinh...")
    
    time.sleep(5) # Cho cluster on dinh lai
    
    # Dung workload
    stop_event.set()
    t.join()
    cluster.shutdown()
    print(f"--- Hoan tat test {cl_name} ---")

if __name__ == "__main__":
    run_experiment_for_cl("ONE", ConsistencyLevel.ONE)
    run_experiment_for_cl("QUORUM", ConsistencyLevel.QUORUM)
    run_experiment_for_cl("ALL", ConsistencyLevel.ALL)
