"""Data Contract v2 - module ghi log chuan cho moi thi nghiem.

Contract v2 (dong bo voi analysis pipeline cua Uyen):

  access_log.csv:
      ts, request_id, op, category_id, product_id, latency_ms,
      success, error, run_id, op_detail
      - ts           : int64 Unix epoch milliseconds (UTC).
      - op           : "READ" | "WRITE" (UPPERCASE - bat buoc de
                       top_partitions cua Uyen dem dung).
      - op_detail    : nhan phu tuy chon, vd "LWT_BUY", "COUNTER_INC".
                       De trong voi READ/WRITE thong thuong.
      - success      : "true" | "false" (lowercase).
      - error        : chuoi rong neu success=true.

  consistency_log.csv:
      ts, event, key, version, consistency_level, node,
      network_state, success, error, run_id
      - ts           : int64 Unix epoch ms (dung duoc voi pandas.merge_asof).
      - event        : "READ" | "WRITE" (su kien du lieu that).
      - version      : int monotonic per key - bat buoc de tinh stale read.
      - network_state: "NORMAL" | "PARTITIONED" (trang thai tai thoi diem op).

  chaos_events.csv (tach rieng khoi consistency_log):
      ts, run_id, event, target, detail
      - event: "partition_start" | "partition_end" | "failover_start" |
               "failover_end" | ... (chaos lifecycle markers).

  manifest.json (moi run mot file, provenance):
      contract_version, origin="observed", run_id, experiment_id,
      experiment_type, git_sha, created_at (UTC ISO), started_at_ms,
      ended_at_ms, op_count, config, extra.
"""
import csv
import json
import os
import subprocess
import time
import uuid
from datetime import datetime, timezone

CONTRACT_VERSION = "v2"

ACCESS_FIELDS = ["ts", "request_id", "op", "category_id", "product_id",
                 "latency_ms", "success", "error", "run_id", "op_detail"]
CONSISTENCY_FIELDS = ["ts", "event", "key", "version", "consistency_level",
                      "node", "network_state", "success", "error", "run_id"]
CHAOS_FIELDS = ["ts", "run_id", "event", "target", "detail"]

# Canonical ops cho analysis; op khac map sang canonical + giu nhan goc.
_OP_CANON = {"READ", "WRITE"}
_OP_ALIAS = {
    "read": "READ", "write": "WRITE",
    "insert": "WRITE", "update": "WRITE", "delete": "WRITE",
    "select": "READ", "get": "READ",
}


def now_ms():
    """Unix epoch milliseconds (UTC) - dung cho moi ts trong contract."""
    return int(time.time() * 1000)


def get_run_id():
    return (datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            + "_" + str(uuid.uuid4())[:8])


def get_output_dir(exp_name, run_id):
    path = os.path.join("experiments", exp_name, run_id)
    os.makedirs(path, exist_ok=True)
    return path


def _init_csv(dir_path, filename, fields):
    filepath = os.path.join(dir_path, filename)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(fields)
    return filepath


def init_access_log(dir_path):
    return _init_csv(dir_path, "access_log.csv", ACCESS_FIELDS)


def init_consistency_log(dir_path):
    return _init_csv(dir_path, "consistency_log.csv", CONSISTENCY_FIELDS)


def init_chaos_log(dir_path):
    """File rieng cho chaos lifecycle markers - KHONG ghi vao consistency_log."""
    return _init_csv(dir_path, "chaos_events.csv", CHAOS_FIELDS)


def normalize_op(op):
    """Tra ve (canonical_op, op_detail_goc_neu_khac_canonical)."""
    o = str(op).strip().upper()
    if o in _OP_CANON:
        return o, ""
    canon = _OP_ALIAS.get(o, o)
    if canon in _OP_CANON:
        return canon, o
    # Op dac biet (vd LWT_BUY) -> de nguyen nhung caller nen truyen op_detail.
    return o, ""


def write_access_log(filepath, run_id, op, latency_ms, success,
                     category_id="", product_id="", error="", op_detail="",
                     ts_ms=None, request_id=None):
    canon, implicit_detail = normalize_op(op)
    row = [ts_ms if ts_ms is not None else now_ms(),
           request_id or str(uuid.uuid4()),
           canon,
           str(category_id), str(product_id),
           round(float(latency_ms), 3),
           "true" if success else "false",
           "" if success and not error else str(error),
           run_id,
           op_detail or implicit_detail]
    with open(filepath, mode="a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


def write_consistency_log(filepath, run_id, event, key, version,
                          consistency_level, node, network_state, success,
                          error="", ts_ms=None):
    """Ghi su kien READ/WRITE that. event bat buoc READ|WRITE (uppercase)."""
    ev = str(event).strip().upper()
    row = [ts_ms if ts_ms is not None else now_ms(),
           ev,
           str(key), str(version),
           str(consistency_level), str(node), str(network_state),
           "true" if success else "false",
           "" if success and not error else str(error),
           run_id]
    with open(filepath, mode="a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


def write_chaos_event(filepath, run_id, event, target="", detail="", ts_ms=None):
    row = [ts_ms if ts_ms is not None else now_ms(),
           run_id, str(event), str(target), str(detail)]
    with open(filepath, mode="a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


def _git_sha():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)), timeout=5)
        if out.returncode == 0:
            return out.stdout.strip() or None
    except Exception:
        pass
    return None


def new_manifest(run_id, experiment_id, experiment_type, config=None):
    """Tao manifest dict luc BAT DAU run; goi finalize_manifest khi ket thuc."""
    return {
        "contract_version": CONTRACT_VERSION,
        "origin": "observed",
        "run_id": run_id,
        "experiment_id": experiment_id,
        "experiment_type": experiment_type,
        "git_sha": _git_sha(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "started_at_ms": now_ms(),
        "ended_at_ms": None,
        "op_count": None,
        "config": config or {},
        "extra": {},
    }


def finalize_manifest(dir_path, manifest, op_count=None, extra=None):
    manifest["ended_at_ms"] = now_ms()
    if op_count is not None:
        manifest["op_count"] = op_count
    if extra:
        manifest["extra"].update(extra)
    path = os.path.join(dir_path, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return path
