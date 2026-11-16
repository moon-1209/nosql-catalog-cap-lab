"""Benchmark harness — Đo latency bằng HdrHistogram cho MongoDB."""
import time
import os
from datetime import datetime, timezone
from hdrhistogram import Histogram
from pymongo import MongoClient

# Cấu hình kết nối (có thể đổi qua biến môi trường)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "benchmark_db"
COLLECTION = "test_collection"

def run_benchmark(num_ops=1000):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    col = db[COLLECTION]
    
    # Dọn dẹp dữ liệu cũ
    col.drop()
    
    # Khởi tạo Histogram: đo từ 1ms đến 60.000ms (60s)
    h_write = Histogram(1, 60000, 3)
    h_read = Histogram(1, 60000, 3)

    print(f"Bắt đầu benchmark {num_ops} operations...")

    for i in range(num_ops):
        # 1. Đo Write (Insert)
        t0 = time.perf_counter()
        col.insert_one({"key": f"user_{i}", "value": i})
        write_latency = (time.perf_counter() - t0) * 1000 # ms
        h_write.record(write_latency)

        # 2. Đo Read (Find)
        t0 = time.perf_counter()
        col.find_one({"key": f"user_{i}"})
        read_latency = (time.perf_counter() - t0) * 1000 # ms
        h_read.record(read_latency)

    # In kết quả
    print("\n--- KẾT QUẢ WRITE ---")
    print(f"P50: {h_write.percentile(50):.2f} ms")
    print(f"P95: {h_write.percentile(95):.2f} ms")
    print(f"P99: {h_write.percentile(99):.2f} ms")
    print(f"Max: {h_write.max:.2f} ms")

    print("\n--- KẾT QUẢ READ ---")
    print(f"P50: {h_read.percentile(50):.2f} ms")
    print(f"P95: {h_read.percentile(95):.2f} ms")
    print(f"P99: {h_read.percentile(99):.2f} ms")
    print(f"Max: {h_read.max:.2f} ms")

if __name__ == "__main__":
    run_benchmark(num_ops=500) # Chạy thử 500 lần