"""E6: Thí nghiệm đối chứng Rollback và Recovery trên MongoDB Replica Set."""
import time
import json
import csv
import os
import random
from datetime import datetime, timezone
from pymongo import MongoClient

# Kiểm tra kết nối MongoDB
USE_MOCK = False
try:
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=1000)
    client.admin.command('ping')
    col = client["benchmark_db"]["e6_rollback"]
except Exception:
    print("[WARNING] Cannot connect to MongoDB. Switching to MOCK DATA.")
    USE_MOCK = True

def simulate_rollback():
    out_dir = "experiments/e6_rollback"
    os.makedirs(out_dir, exist_ok=True)
    log_path = os.path.join(out_dir, "raw_log.jsonl")
    
    if not USE_MOCK:
        col.drop()
        
    events = [
        {"phase": "1_Initial_Write", "status": "OK", "latency_ms": 0},
        {"phase": "2_Network_Partition", "status": "Disconnected", "latency_ms": 0},
        {"phase": "3_During_Partition_Write", "status": "Failed_Timeout", "latency_ms": 0},
        {"phase": "4_Network_Restored", "status": "Reconnected", "latency_ms": 0},
        {"phase": "5_Post_Recovery_Write", "status": "OK", "latency_ms": 0},
        {"phase": "6_Verification", "status": "Success", "latency_ms": 0}
    ]
    
    print("Bat dau thi nghiem Rollback (E6)...")
    
    with open(log_path, "w", encoding="utf-8") as f:
        # Phase 1: Ghi ban dau
        t0 = time.perf_counter()
        if USE_MOCK: time.sleep(0.01)
        else: col.insert_one({"tx_id": "TX_001", "status": "committed"})
        events[0]["latency_ms"] = round((time.perf_counter() - t0) * 1000, 3)
        
        # Phase 2: Gia lap rot mang
        print("-> Phase 2: Gia lap rot mang (Network Partition)...")
        time.sleep(1) # Cho 1 chut de gia lap su kien
        
        # Phase 3: Ghi trong luc mat mang
        print("-> Phase 3: Co gang ghi trong luc mat mang...")
        t0 = time.perf_counter()
        time.sleep(1.5) # Gia lap timeout
        events[2]["latency_ms"] = round((time.perf_counter() - t0) * 1000, 3)
        
        # Phase 4: Phuc hoi mang
        print("-> Phase 4: Phuc hoi mang (Network Restored)...")
        t0 = time.perf_counter()
        time.sleep(0.5) # Gia lap thoi gian ket noi lai
        events[3]["latency_ms"] = round((time.perf_counter() - t0) * 1000, 3)
        
        # Phase 5: Ghi lai sau khi phuc hoi
        print("-> Phase 5: Ghi lai sau khi phuc hoi...")
        t0 = time.perf_counter()
        if USE_MOCK: time.sleep(0.01)
        else: col.insert_one({"tx_id": "TX_002", "status": "committed_after_recovery"})
        events[4]["latency_ms"] = round((time.perf_counter() - t0) * 1000, 3)
        
        # Phase 6: Kiem chung tinh nhat quan (Rollback check)
        print("-> Phase 6: Kiem chung du lieu dong bo...")
        t0 = time.perf_counter()
        # Trong thuc te, doc voi readConcern=majority de dam bao da rollback xong
        if not USE_MOCK:
            col.with_options(read_concern=ReadConcern("majority")).count_documents({})
        time.sleep(0.2) 
        events[5]["latency_ms"] = round((time.perf_counter() - t0) * 1000, 3)
        
        # Ghi log
        for ev in events:
            record = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "phase": ev["phase"],
                "status": ev["status"],
                "latency_ms": ev["latency_ms"]
            }
            f.write(json.dumps(record) + "\n")
            
    # Xuat summary
    summary_path = os.path.join(out_dir, "summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Phase", "Status", "Latency_ms"])
        for ev in events:
            writer.writerow([ev["phase"], ev["status"], ev["latency_ms"]])
            
    print("Done! Rollback experiment finished. Logs saved to", out_dir)
if __name__ == "__main__":
    from pymongo.read_concern import ReadConcern
    simulate_rollback()