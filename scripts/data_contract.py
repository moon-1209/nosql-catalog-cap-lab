"""Data Contract v2 - Fix P0 issues (op, ts, version, manifest)."""
import csv
import os
import uuid
import json
import time
from datetime import datetime, timezone

def get_current_time_ms():
    return int(time.time() * 1000)

def get_run_id():
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + "_" + str(uuid.uuid4())[:8]

def get_output_dir(exp_name, run_id):
    path = os.path.join("experiments", exp_name, run_id)
    os.makedirs(path, exist_ok=True)
    return path

def write_manifest(dir_path, run_id, exp_name, config_info):
    manifest = {
        "run_id": run_id,
        "experiment_id": exp_name,
        "schema_version": "v2",
        "data_contract_version": "v2",
        "start_time_ms": get_current_time_ms(),
        "config": config_info
    }
    with open(os.path.join(dir_path, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)

def init_access_log(dir_path):
    filepath = os.path.join(dir_path, "access_log.csv")
    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ts", "request_id", "op", "category_id", "product_id", "latency_ms", "success", "error", "run_id"])
    return filepath

def write_access_log(filepath, run_id, op, latency_ms, success, category_id="", product_id="", error=""):
    # Chuan hoa op thanh chu hoa
    op_upper = op.upper()
    if op_upper == "LWT_BUY": op_upper = "WRITE"
    if op_upper == "COUNTER_INC": op_upper = "WRITE"
    
    with open(filepath, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            get_current_time_ms(), # ts thanh epoch ms
            str(uuid.uuid4()), op_upper, category_id, product_id, round(latency_ms, 3),
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
            get_current_time_ms(), event, key, version, consistency_level, node, network_state,
            str(success).lower(), error, run_id
        ])
