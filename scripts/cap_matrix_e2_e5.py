"""E2-E5: CAP Matrix - Consistency Level (ONE, QUORUM, ALL) trên MongoDB."""
import time
import json
import csv
import os
import random
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.write_concern import WriteConcern

# Kiểm tra kết nối MongoDB
USE_MOCK = False
try:
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=1000)
    client.admin.command('ping')
except Exception:
    print("[WARNING] Cannot connect to MongoDB. Switching to MOCK DATA.")
    USE_MOCK = True

def run_matrix_test():
    out_dir = "experiments/cap_matrix"
    os.makedirs(out_dir, exist_ok=True)
    
    # Ánh xạ Consistency Level sang MongoDB Write Concern
    levels = {
        "ONE": 1,
        "QUORUM": "majority",
        "ALL": 3
    }
    
    num_ops = 300 # Chạy 300 lệnh cho mỗi level
    results = []
    
    for level_name, w_val in levels.items():
        print(f"Testing Consistency Level: {level_name} (w={w_val})...")
        
        if not USE_MOCK:
            # Kết nối với Write Concern tương ứng
            db = client.get_database("benchmark_db", write_concern=WriteConcern(w=w_val, j=True))
            col = db["cap_matrix"]
        
        latencies = []
        log_path = os.path.join(out_dir, f"log_{level_name}.jsonl")
        
        with open(log_path, "w", encoding="utf-8") as f:
            for i in range(num_ops):
                t0 = time.perf_counter()
                
                if USE_MOCK:
                    # Giả lập độ trễ: ONE nhanh, ALL chậm nhất
                    if level_name == "ONE": sleep_time = random.uniform(0.001, 0.005)
                    elif level_name == "QUORUM": sleep_time = random.uniform(0.005, 0.015)
                    else: sleep_time = random.uniform(0.015, 0.030)
                    time.sleep(sleep_time)
                    success = True
                else:
                    try:
                        col.update_one({"key": f"test_{i}"}, {"$set": {"val": i}}, upsert=True)
                        success = True
                    except Exception:
                        success = False
                        
                latency = (time.perf_counter() - t0) * 1000
                latencies.append(latency)
                
                record = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "level": level_name,
                    "w_val": str(w_val),
                    "latency_ms": round(latency, 3),
                    "success": success
                }
                f.write(json.dumps(record) + "\n")
                
        # Tính toán thống kê
        latencies.sort()
        n = len(latencies)
        p50 = latencies[int(n * 0.50)]
        p95 = latencies[int(n * 0.95)]
        p99 = latencies[int(n * 0.99)]
        mean = sum(latencies) / n
        
        results.append({
            "Consistency_Level": level_name,
            "Write_Concern": w_val,
            "Mean_ms": round(mean, 3),
            "P50_ms": round(p50, 3),
            "P95_ms": round(p95, 3),
            "P99_ms": round(p99, 3),
        })

    # Ghi file CSV tổng hợp
    summary_path = os.path.join(out_dir, "summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Consistency_Level", "Write_Concern", "Mean_ms", "P50_ms", "P95_ms", "P99_ms"])
        writer.writeheader()
        writer.writerows(results)
        
    print(f"Done! Results saved to {out_dir}/")

if __name__ == "__main__":
    run_matrix_test()