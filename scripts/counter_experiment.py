"""Counter: Native Counter tren ScyllaDB."""
import time
import concurrent.futures
from lab_connect import connect, ensure_keyspace
from data_contract import (get_run_id, get_output_dir, init_access_log,
    write_access_log, new_manifest, finalize_manifest)

def run_experiment():
    run_id = get_run_id()
    out_dir = get_output_dir("Counter", run_id)
    access_log = init_access_log(out_dir)
    manifest = new_manifest(run_id, "COUNTER", "counter_increment", config={
        "table": "catalog.counter_test", "threads": 20, "ops": 100})

    cluster, session = connect()
    ensure_keyspace(session, "catalog")
    session.execute("DROP TABLE IF EXISTS catalog.counter_test")
    session.execute("CREATE TABLE IF NOT EXISTS catalog.counter_test (id int PRIMARY KEY, views counter)")
    
    session.execute("UPDATE catalog.counter_test SET views = views + 0 WHERE id = 1")

    def increment(ticket):
        stmt = session.prepare("UPDATE catalog.counter_test SET views = views + 1 WHERE id = 1")
        t0 = time.perf_counter()
        success = True
        err_msg = ""
        try:
            session.execute(stmt, timeout=10.0)
        except Exception as e:
            success = False
            err_msg = str(e)[:50]
            
        lat = (time.perf_counter() - t0) * 1000
        write_access_log(access_log, run_id, "WRITE", lat, success, product_id="1", error=err_msg, op_detail="COUNTER_INC")

    print("Bat dau 100 luong tang bien dem dong thoi...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        list(executor.map(increment, range(1, 101)))
        
    final_val = session.execute("SELECT views FROM catalog.counter_test WHERE id = 1").one()[0]
    print(f"Tong so lan tang: 100. Gia tri Counter cuoi cung: {final_val} (Phai bang 100)")
    finalize_manifest(out_dir, manifest, op_count=100)
    print(f"Logs saved at {out_dir}")
    cluster.shutdown()

if __name__ == "__main__":
    run_experiment()
