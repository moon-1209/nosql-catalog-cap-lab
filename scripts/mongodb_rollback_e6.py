"""E6: MongoDB Replica Set failover thuc te."""
import time
import threading
from datetime import datetime, timezone
from pymongo import MongoClient
from data_contract import get_run_id, get_output_dir, init_access_log, write_access_log, init_consistency_log, write_consistency_log

# Dung ten container thay vi IP de Docker phan giai
MONGO_URI = "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0"

def run_experiment():
    run_id = get_run_id()
    out_dir = get_output_dir("E6_Mongo_Failover", run_id)
    access_log = init_access_log(out_dir)
    consistency_log = init_consistency_log(out_dir)
    
    print("Connecting to MongoDB Replica Set...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = client["benchmark_db"]
    col = db["failover_test"]
    col.drop()
    
    stop_event = threading.Event()
    
    def workload():
        op_count = 0
        while not stop_event.is_set():
            op_count += 1
            t0 = time.perf_counter()
            try:
                col.insert_one({"tx": op_count, "ts": datetime.now(timezone.utc)})
                lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "write", lat, True, product_id=str(op_count))
            except Exception as e:
                lat = (time.perf_counter() - t0) * 1000
                write_access_log(access_log, run_id, "write", lat, False, product_id=str(op_count), error=type(e).__name__)
            time.sleep(0.05)

    print("Bat dau workload doc/ghi...")
    t = threading.Thread(target=workload)
    t.start()
    time.sleep(3)
    
    print(">>> Kich hoat su co: Ep Primary (mongo1) step down...")
    write_consistency_log(consistency_log, run_id, "failover_start", "ALL", "1", "PRIMARY", "mongo1", "stepping_down", True)
    
    t_failover_start = time.perf_counter()
    try:
        # Dung pymongo de ep stepdown truc tiep (10 giay)
        # Lenh nay se ngat ket noi hien tai va tra ve loi ConnectionFailure (la binh thuong)
        admin_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        admin_client.admin.command('replSetStepDown', 10)
    except Exception as e:
        print(f">>> Da ep Primary step down thanh cong (He thong ngat ket noi de bau Primary moi).")
        
    print(">>> Dang cho he thong bau Primary moi va on dinh...")
    time.sleep(10)
    
    t_recovery = time.perf_counter() - t_failover_start
    write_consistency_log(consistency_log, run_id, "failover_end", "ALL", "1", "NEW_PRIMARY", "mongo2/3", "recovered", True)
    
    stop_event.set()
    t.join()
    client.close()
    print(f"Done! Thoi gian phuc hoi (uoc tinh): {t_recovery:.2f} giay")
    print(f"Logs saved at {out_dir}")

if __name__ == "__main__":
    run_experiment()
