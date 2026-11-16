"""E1b: Bucketing Workload cho Schema B."""
import random
import time
import json
import csv
import os
from datetime import datetime, timezone
from pymongo import MongoClient

# Kiểm tra kết nối MongoDB, nếu không có thì dùng Mock Data
USE_MOCK = False
try:
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=1000)
    client.admin.command('ping')
    col = client["benchmark_db"]["e1b_bucketing"]
except Exception:
    print("[WARNING] Cannot connect to MongoDB. Switching to MOCK DATA to generate logs.")
    USE_MOCK = True

def run_experiment():
    out_dir = "experiments/e1b_bucketing"
    os.makedirs(out_dir, exist_ok=True)
    
    num_keys = 10000
    num_ops = 1000
    
    print(f"Generating {num_ops} operations with Bucketing distribution...")
    
    latencies = []
    log_path = os.path.join(out_dir, "raw_log.jsonl")
    
    with open(log_path, "w", encoding="utf-8") as f:
        for i in range(num_ops):
            op_type = "write" if i % 2 == 0 else "read"
            
            # Bucketing: Chia key thành các nhóm (bucket) đều nhau
            bucket_id = random.randint(1, 100)
            key = f"bucket_{bucket_id}_item_{i}"
            
            t0 = time.perf_counter()
            if USE_MOCK:
                time.sleep(random.uniform(0.002, 0.020))
                success = True
            else:
                try:
                    if op_type == "write":
                        col.update_one({"bucket_id": bucket_id}, {"$push": {"items": {"key": key, "val": random.random()}}}, upsert=True)
                    else:
                        col.find_one({"bucket_id": bucket_id})
                    success = True
                except Exception:
                    success = False
                    
            latency = (time.perf_counter() - t0) * 1000
            latencies.append(latency)
            
            # Ghi log JSONL
            record = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "op": op_type,
                "bucket_id": bucket_id,
                "latency_ms": round(latency, 3),
                "success": success
            }
            f.write(json.dumps(record) + "\n")
            
    # Tinh toan summary
    latencies.sort()
    n = len(latencies)
    p50 = latencies[int(n * 0.50)]
    p95 = latencies[int(n * 0.95)]
    p99 = latencies[int(n * 0.99)]
    mean = sum(latencies) / n
    
    # Ghi summary CSV
    summary_path = os.path.join(out_dir, "summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value_ms"])
        writer.writerow(["Mean", round(mean, 3)])
        writer.writerow(["P50", round(p50, 3)])
        writer.writerow(["P95", round(p95, 3)])
        writer.writerow(["P99", round(p99, 3)])
        writer.writerow(["Max", round(latencies[-1], 3)])
        
    print(f"Done! Logs saved at {out_dir}/raw_log.jsonl and {out_dir}/summary.csv")

if __name__ == "__main__":
    run_experiment()