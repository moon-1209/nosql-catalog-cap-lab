#!/usr/bin/env python3
"""
promlib.py — client tối giản cho Prometheus HTTP API (chỉ dùng thư viện chuẩn).

Dùng làm module:
    from promlib import Prom, parse_time, parse_duration
    p = Prom("http://localhost:9090")
    for labels, points in p.range('rate(x[30s])', start, end, 5): ...

Dùng từ dòng lệnh (cho script bash):
    python3 promlib.py ready
    python3 promlib.py instant 'sum by (instance) (scylla_column_family_tablet_count)'
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Iterable

DEFAULT_PROM = os.environ.get("PROM_URL", "http://localhost:9090")
MAX_POINTS = 10_000  # Prometheus từ chối query_range > 11000 điểm/series


class PromError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Thời gian
# ---------------------------------------------------------------------------
_DUR_RE = re.compile(r"^(\d+(?:\.\d+)?)(ms|s|m|h|d)$")


def parse_duration(s: str | float | int) -> float:
    """'30s' → 30.0, '5m' → 300.0, '250ms' → 0.25; số trần được hiểu là giây."""
    if isinstance(s, (int, float)):
        return float(s)
    s = s.strip()
    m = _DUR_RE.match(s)
    if not m:
        return float(s)
    v, unit = float(m.group(1)), m.group(2)
    return v * {"ms": 0.001, "s": 1, "m": 60, "h": 3600, "d": 86400}[unit]


def parse_time(s: str | float | int) -> float:
    """Trả về epoch GIÂY (float). Nhận: epoch giây/ms, ISO 8601, 'now', 'now-10m'."""
    if isinstance(s, (int, float)):
        v = float(s)
        return v / 1000.0 if v > 1e11 else v
    s = s.strip()
    if s == "now":
        return time.time()
    if s.startswith("now-"):
        return time.time() - parse_duration(s[4:])
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return parse_time(float(s))
    iso = s.replace("Z", "+00:00")
    t = dt.datetime.fromisoformat(iso)
    if t.tzinfo is None:  # không ghi múi giờ → coi là giờ máy
        t = t.astimezone()
    return t.timestamp()


def fmt_iso(ts: float) -> str:
    """epoch giây → ISO UTC có mili-giây."""
    return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
class Prom:
    def __init__(self, url: str = DEFAULT_PROM, timeout: float = 30.0):
        self.url = url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str, params: dict) -> dict:
        q = urllib.parse.urlencode(params)
        req = urllib.request.Request(f"{self.url}{path}?{q}", headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                body = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                body = json.loads(e.read().decode())
            except Exception:  # noqa: BLE001
                raise PromError(f"HTTP {e.code} từ Prometheus: {e.reason}") from e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            raise PromError(f"Không kết nối được Prometheus {self.url}: {e}") from e
        if body.get("status") != "success":
            raise PromError(f"{body.get('errorType')}: {body.get('error')}")
        return body["data"]

    def ready(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.url}/-/ready", timeout=5) as r:
                return r.status == 200
        except Exception:  # noqa: BLE001
            return False

    def instant(self, expr: str, at: float | None = None) -> list[tuple[dict, float]]:
        params = {"query": expr}
        if at is not None:
            params["time"] = f"{at:.3f}"
        data = self._get("/api/v1/query", params)
        out = []
        if data["resultType"] == "vector":
            for s in data["result"]:
                out.append((s["metric"], _num(s["value"][1])))
        elif data["resultType"] == "scalar":
            out.append(({}, _num(data["result"][1])))
        return out

    def range(self, expr: str, start: float, end: float, step: float) -> list[tuple[dict, list[tuple[float, float]]]]:
        """Trả về [(labels, [(ts, value), ...]), ...]; tự chia nhỏ nếu quá nhiều điểm."""
        if end <= start:
            raise PromError("end phải lớn hơn start")
        merged: dict[tuple, tuple[dict, list]] = {}
        chunk = step * MAX_POINTS
        t = start
        while t < end:
            t2 = min(end, t + chunk)
            data = self._get("/api/v1/query_range",
                             {"query": expr, "start": f"{t:.3f}", "end": f"{t2:.3f}", "step": f"{step}"})
            for s in data["result"]:
                key = tuple(sorted(s["metric"].items()))
                pts = [(float(ts), _num(v)) for ts, v in s["values"]]
                if key not in merged:
                    merged[key] = (s["metric"], [])
                merged[key][1].extend(pts)
            t = t2 + step
        result = []
        for labels, pts in merged.values():
            seen, uniq = set(), []
            for ts, v in sorted(pts):
                if ts not in seen:
                    seen.add(ts)
                    uniq.append((ts, v))
            result.append((labels, uniq))
        return result


def _num(v: str) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return math.nan
    return x


# ---------------------------------------------------------------------------
# Thống kê nhỏ (không cần numpy)
# ---------------------------------------------------------------------------
def finite(values: Iterable[float]) -> list[float]:
    return [v for v in values if v is not None and not math.isnan(v) and not math.isinf(v)]


def percentile(values: Iterable[float], q: float) -> float:
    xs = sorted(finite(values))
    if not xs:
        return math.nan
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q / 100.0
    lo, hi = math.floor(pos), math.ceil(pos)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def summarize(values: Iterable[float]) -> dict:
    xs = finite(values)
    if not xs:
        return {"n": 0, "mean": math.nan, "p50": math.nan, "p95": math.nan, "max": math.nan, "min": math.nan}
    return {
        "n": len(xs),
        "mean": sum(xs) / len(xs),
        "p50": percentile(xs, 50),
        "p95": percentile(xs, 95),
        "max": max(xs),
        "min": min(xs),
    }


def write_csv(path, header: list[str], rows: Iterable[Iterable]) -> int:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    n = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)
            n += 1
    return n


def jsonable(o):
    """Đổi NaN/Inf thành None để json.dump không sinh JSON sai chuẩn."""
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    if isinstance(o, dict):
        return {k: jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    return o


def load_run_window(run_dir: str) -> tuple[float, float]:
    """Đọc cửa sổ thời gian [t0, t_end] (epoch giây) của một run do chaos_runner.py tạo."""
    path = os.path.join(run_dir, "summary.json")
    if not os.path.exists(path):
        path = os.path.join(run_dir, "meta.json")
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    t0 = d.get("t0_ms")
    t_end = d.get("t_end_ms") or d.get("t_planned_end_ms")
    if t0 is None or t_end is None:
        raise ValueError(f"{path} thiếu t0_ms/t_end_ms")
    return t0 / 1000.0, t_end / 1000.0


def load_events(run_dir: str) -> list[dict]:
    path = os.path.join(run_dir, "events.jsonl")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------------------------------------------------------------------------
def _cli(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    p = Prom()
    if argv[0] == "ready":
        ok = p.ready()
        print("ready" if ok else "not ready")
        return 0 if ok else 1
    if argv[0] == "instant" and len(argv) >= 2:
        for labels, v in p.instant(argv[1]):
            lab = ",".join(f"{k}={labels[k]}" for k in sorted(labels) if k != "__name__")
            print(f"{lab or '-'}\t{v:g}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(_cli(sys.argv[1:]))
    except PromError as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        sys.exit(1)
