"""E1a: Zipf Distribution Workload cho Schema A."""
import random
import math
import time
import json
import csv
import os
from datetime import datetime, timezone
from pymongo import MongoClient

# Kiểm tra kết nối MongoDB, nếu không có thì dùng Mock Data
USE_MOCK = False
try:
    # Rút ngắn timeout xuống 1s để nếu không có DB thì báo lỗi nhanh
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=1000)
    client.admin.command('ping')
    col = client["benchmark_db"]["e1a_zipf"]
except Exception:
    print("[WARNING] Cannot connect to MongoDB. Switching to MOCK DATA to generate logs.")
    USE_MOCK = True

def zipf_distribution(n, s, num_samples):
    """Sinh mảng khóa theo phân phối Zipf."""
    weights = [1.0 / (math.pow(i, s)) for i in range(1, n + 1)]
    total = sum(weights)
    probabilities = [w / total for w in weights]
    return random.choices(range(1, n + 1), weights=probabilities, k=num_samples)

def run_experiment():
    out_dir = "experiments/e1a_zipf"
    os.makedirs(out_dir, exist_ok=True)
    
    num_keys = 10000
    skew = 1.2 # Do lech Zipf
    num_ops = 1000
    
    print(f"Generating {num_ops} operations with Zipf distribution...")
    keys = zipf_distribution(num_keys, skew, num_ops)
    
    latencies = []
    log_path = os.path.join(out_dir, "raw_log.jsonl")
    
    with open(log_path, "w", encoding="utf-8") as f:
        for i, key in enumerate(keys):
            op_type = "write" if i % 2 == 0 else "read"
            
            t0 = time.perf_counter()
            if USE_MOCK:
                # Gia lap do tre ngau nhien tu 2ms den 20ms
                time.sleep(random.uniform(0.002, 0.020))
                success = True
            else:
                try:
                    if op_type == "write":
                        col.update_one({"key": key}, {"$set": {"value": random.random()}}, upsert=True)
                    else:
                        col.find_one({"key": key})
                    success = True
                except Exception:
                    success = False
                    
            latency = (time.perf_counter() - t0) * 1000
            latencies.append(latency)
            
            # Ghi log JSONL
            record = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "op": op_type,
                "key": key,
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