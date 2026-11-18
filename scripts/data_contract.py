"""Data Contract v2 - Module ghi log chuan."""
import csv
import os
import uuid
from datetime import datetime, timezone

def get_run_id():
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + "_" + str(uuid.uuid4())[:8]

def get_output_dir(exp_name, run_id):
    path = os.path.join("experiments", exp_name, run_id)
    os.makedirs(path, exist_ok=True)
    return path

def init_access_log(dir_path):
    filepath = os.path.join(dir_path, "access_log.csv")
    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ts", "request_id", "op", "category_id", "product_id", "latency_ms", "success", "error", "run_id"])
    return filepath

def write_access_log(filepath, run_id, op, latency_ms, success, category_id="", product_id="", error=""):
    with open(filepath, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            str(uuid.uuid4()), op, category_id, product_id, round(latency_ms, 3),
            str(success).lower(), error, run_id
        ])

def init_consistency_log(dir_path):
    filepath = os.path.join(dir_path, "consistency_log.csv")
    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ts", "event", "key", "version", "consistency_level", "node", "network_state", "success", "error", "run_id"])
    return filepath

def write_consistency_log(filepath, run_id, event, key, version, consistency_level, node, network_state, success, error=""):
    with open(filepath, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            event, key, version, consistency_level, node, network_state,
            str(success).lower(), error, run_id
        ])
