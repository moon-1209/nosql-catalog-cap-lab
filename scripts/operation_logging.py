"""Operation logging — ghi log Read/Write có timestamp cho MongoDB."""
import json
import time
import os
from datetime import datetime, timezone

LOG_PATH = os.getenv("LOG_PATH", "experiments/logs/operations.jsonl")

def log_operation(op_type: str, key: str, latency_ms: float, success: bool, error: str = None):
    """Ghi 1 dòng log JSONL cho mỗi operation."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "op": op_type,
        "key": key,
        "latency_ms": round(latency_ms, 3),
        "success": success,
        "error": error,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def measure(func, *args, **kwargs):
    """Đo thời gian thực thi func, trả về (result, latency_ms, error)."""
    t0 = time.perf_counter()
    try:
        result = func(*args, **kwargs)
        latency = (time.perf_counter() - t0) * 1000
        return result, latency, None
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000
        return None, latency, str(e)

if __name__ == "__main__":
    log_operation("write", "key-001", 12.5, True)
    log_operation("read", "key-001", 3.2, True)
    log_operation("write", "key-002", 5000.0, False, "timeout")
    print(f"Log written to {LOG_PATH}")