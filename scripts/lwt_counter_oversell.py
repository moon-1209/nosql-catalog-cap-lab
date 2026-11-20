"""LWT & Counter: Ngăn chặn Oversell (bán lố) bằng Atomic Operations trên MongoDB."""
import time
import json
import csv
import os
import threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from pymongo import MongoClient

# Kiểm tra kết nối MongoDB
USE_MOCK = False
try:
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=1000)
    client.admin.command('ping')
    db = client["benchmark_db"]
    col = db["inventory"]
except Exception:
    print("[WARNING] Cannot connect to MongoDB. Switching to MOCK DATA.")
    USE_MOCK = True
    # Biến giả lập dùng lock để an toàn luồng
    mock_stock = 100
    mock_lock = threading.Lock()

INITIAL_STOCK = 100
NUM_THREADS = 20
REQ_PER_THREAD = 10 # Tổng cộng 200 request tranh mua 100 món

def run_oversell_test():
    out_dir = "experiments/lwt_oversell"
    os.makedirs(out_dir, exist_ok=True)
    log_path = os.path.join(out_dir, "raw_log.jsonl")
    
    # Khởi tạo dữ liệu ban đầu
    if not USE_MOCK:
        col.drop()
        col.insert_one({"item_id": "iphone_15", "stock": INITIAL_STOCK})
    
    print(f"Bat dau test: {NUM_THREADS} luong, moi luong mua {REQ_PER_THREAD} lan.")
    print(f"Ton kho ban dau: {INITIAL_STOCK}")
    
    successful_buys = 0
    failed_buys = 0
    lock = threading.Lock() # Lock để ghi log an toàn

    def buy_item(thread_id):
        nonlocal successful_buys, failed_buys
        global mock_stock
        
        for _ in range(REQ_PER_THREAD):
            t0 = time.perf_counter()
            is_success = False
            
            if USE_MOCK:
                time.sleep(0.001) # Gia lap I/O
                with mock_lock:
                    if mock_stock > 0:
                        mock_stock -= 1
                        is_success = True
            else:
                try:
                    # LWT/Counter tuong duong o MongoDB: Tim va update nguyen tu
                    result = col.find_one_and_update(
                        {"item_id": "iphone_15", "stock": {"$gt": 0}},
                        {"$inc": {"stock": -1}},
                        return_document=True
                    )
                    if result:
                        is_success = True
                except Exception as e:
                    pass
            
            latency = (time.perf_counter() - t0) * 1000
            
            with lock:
                if is_success: successful_buys += 1
                else: failed_buys += 1
                
                record = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "thread_id": thread_id,
                    "success": is_success,
                    "latency_ms": round(latency, 3)
                }
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record) + "\n")

    # Chạy đa luồng
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        for i in range(NUM_THREADS):
            executor.submit(buy_item, i)

    # Tổng kết
    final_stock = mock_stock if USE_MOCK else col.find_one({"item_id": "iphone_15"})["stock"]
    
    print("\n--- KET QUA ---")
    print(f"Mua thanh cong: {successful_buys}")
    print(f"Mua that bai (het hang): {failed_buys}")
    print(f"Ton kho con lai: {final_stock}")
    
    if successful_buys > INITIAL_STOCK:
        print("=> LOI: DA BI OVERSELL!")
    else:
        print("=> CHINH XAC: Khong bi oversell.")

    # Ghi summary
    summary_path = os.path.join(out_dir, "summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Initial_Stock", INITIAL_STOCK])
        writer.writerow(["Successful_Buys", successful_buys])
        writer.writerow(["Failed_Buys", failed_buys])
        writer.writerow(["Final_Stock", final_stock])
        writer.writerow(["Oversell_Occurred", "YES" if successful_buys > INITIAL_STOCK else "NO"])
        
    print(f"Done! Logs saved at {out_dir}/")

if __name__ == "__main__":
    run_oversell_test()