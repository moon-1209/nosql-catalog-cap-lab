#!/usr/bin/env python3
"""
labctl.py — hàm Python dùng chung để làm việc với lab (docker, nodetool, lab.env).
Các script Python của tuần 2–4 import module này.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[1]
CHAOS_SH = LAB_ROOT / "chaos" / "chaos.sh"
SNAPSHOT_SH = LAB_ROOT / "lib" / "lab_snapshot.sh"
RUNS_DIR = Path(os.environ.get("RUNS_DIR", LAB_ROOT / "runs"))
EVIDENCE_DIR = Path(os.environ.get("EVIDENCE_DIR", LAB_ROOT / "evidence"))

_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def load_lab_env() -> dict[str, str]:
    """Đọc lab.env (KEY=VALUE) và gộp với biến môi trường hiện tại (env thắng)."""
    env: dict[str, str] = {}
    path = LAB_ROOT / "lab.env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    for k in list(env):
        if k in os.environ:
            env[k] = os.environ[k]
    return env


LAB_ENV = load_lab_env()


def run(cmd: list[str], timeout: float = 60, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)


def docker_ps(label: str) -> list[str]:
    try:
        p = run(["docker", "ps", "--filter", f"label={label}", "--format", "{{.Names}}"], timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return sorted(x for x in p.stdout.split() if x)


def scylla_nodes() -> list[str]:
    return docker_ps("lab.group=scylla")


def mongo_nodes() -> list[str]:
    return docker_ps("lab.group=mongo")


def container_ip(name: str) -> str | None:
    net = LAB_ENV.get("LAB_NETWORK", "lab-net")
    fmt = "{{with index .NetworkSettings.Networks \"%s\"}}{{.IPAddress}}{{end}}" % net
    try:
        p = run(["docker", "inspect", "-f", fmt, name], timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    ip = p.stdout.strip()
    return ip or None


def ip_to_name_map() -> dict[str, str]:
    """IP trên lab-net → tên container (cho mọi container scylla/mongo đang chạy)."""
    out = {}
    for n in scylla_nodes() + mongo_nodes():
        ip = container_ip(n)
        if ip:
            out[ip] = n
    return out


def nodetool(node: str, *args: str, timeout: float = 60) -> str:
    p = run(["docker", "exec", node, "nodetool", *args], timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(f"nodetool {' '.join(args)} trên {node} lỗi: {p.stderr.strip() or p.stdout.strip()}")
    return p.stdout


def parse_nodetool_status(text: str) -> list[dict]:
    """
    Tách các dòng node của `nodetool status`. Cột Load có thể có khoảng trắng ("1.2 MB"),
    nên ta bắt theo mẫu: trạng thái, IP, ... phần trăm Owns (nếu có), Host ID (UUID), Rack.
    """
    rows = []
    for line in text.splitlines():
        m = re.match(r"^([UD])([NLJM])\s+(\d+\.\d+\.\d+\.\d+)\s+(.*)$", line.strip())
        if not m:
            continue
        rest = m.group(4)
        owns = re.search(r"\s(\d+(?:\.\d+)?)%\s", f" {rest} ")
        host = re.search(_UUID, rest)
        rack = rest.split()[-1] if rest.split() else None
        rows.append({
            "status": m.group(1), "state": m.group(2), "code": m.group(1) + m.group(2),
            "ip": m.group(3),
            "owns_pct": float(owns.group(1)) if owns else None,
            "host_id": host.group(0) if host else None,
            "rack": rack,
        })
    return rows


def all_un(observer: str | None = None, expected: list[str] | None = None) -> tuple[bool, str]:
    """(True, mô tả) nếu mọi node scylla đang chạy đều UN trong góc nhìn của observer."""
    nodes = expected or scylla_nodes()
    if not nodes:
        return False, "không có node scylla nào chạy"
    observer = observer or nodes[0]
    try:
        rows = parse_nodetool_status(nodetool(observer, "status", timeout=30))
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        return False, str(e)
    by_ip = {r["ip"]: r["code"] for r in rows}
    bad = []
    for n in nodes:
        ip = container_ip(n)
        if by_ip.get(ip) != "UN":
            bad.append(f"{n}({ip})={by_ip.get(ip, 'không thấy')}")
    if bad:
        return False, "chưa UN: " + ", ".join(bad)
    return True, f"{len(nodes)} node UN"


def ownership(ks: str, cf: str | None, observer: str | None = None) -> dict[str, float]:
    """% sở hữu hiệu dụng của từng node (tên container) cho keyspace/bảng (tablets cần cả bảng)."""
    observer = observer or (scylla_nodes() or [None])[0]
    if observer is None:
        return {}
    args = ["status", ks] + ([cf] if cf else [])
    rows = parse_nodetool_status(nodetool(observer, *args, timeout=60))
    names = ip_to_name_map()
    return {names.get(r["ip"], r["ip"]): r["owns_pct"] for r in rows if r["owns_pct"] is not None}
