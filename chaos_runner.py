#!/usr/bin/env python3
"""
chaos_runner.py — chạy KỊCH BẢN TIÊM LỖI theo mốc thời gian (Chaos automation).

Một "run" = 1 kịch bản JSON + (tuỳ chọn) 1 lệnh harness của Duy chạy song song.
Runner lấy T0 làm gốc, thực thi từng sự kiện đúng mốc `at_s`, ghi lại 3 dấu thời gian
cho mỗi sự kiện (epoch ms, UTC):
    ts_planned_ms  — mốc theo kịch bản (T0 + at_s)
    ts_start_ms    — lúc bắt đầu thực thi lệnh
    ts_done_ms     — lúc lệnh trả về  → LỖI CÓ HIỆU LỰC TỪ THỜI ĐIỂM NÀY
Kết quả nằm trong runs/<run_id>/:
    meta.json  events.jsonl  events.csv  summary.json  harness.log  snapshots/  chaos_ops.jsonl

Ví dụ:
    ./chaos_runner.py scenarios/00_smoke_runner.json
    ./chaos_runner.py ../tuan3_tiem-loi-cap/scenarios/s1_az3_isolation_peers.json \
        --run-id E3_QQ_r1 --param write_cl=QUORUM --param read_cl=QUORUM \
        --harness-cmd "python3 ~/duy/harness.py --wcl {write_cl} --rcl {read_cl} --duration {duration_s} --out {run_dir}/harness"
    ./chaos_runner.py <kịch_bản> --dry-run --time-scale 0.05     # thử nhanh, không đụng docker

Định dạng kịch bản (JSON):
{
  "name": "s1_az3_isolation_peers", "description": "...", "duration_s": 300,
  "events": [
    {"at_s": 0,   "action": "marker",    "label": "Baseline"},
    {"at_s": 60,  "action": "partition", "target": "scylla-node3", "mode": "peers", "label": "AZ3 bị cô lập"},
    {"at_s": 85,  "action": "snapshot",  "label": "sau failure detector"},
    {"at_s": 180, "action": "heal",      "target": "scylla-node3", "label": "Khôi phục"},
    {"at_s": 200, "action": "exec", "cmd": "echo {run_id}", "background": true}
  ]
}
action: marker | partition(mode, from[]) | heal | netem(delay_ms, jitter_ms, loss_pct, to[]) |
        clear_netem | pause | unpause | snapshot | exec(cmd, background, timeout_s) | reset
target có thể là alias "@mongo-primary" (giải tại thời điểm sự kiện, giữ nguyên cho cả run).
Trường tuỳ chọn "phase": "fault_start" | "fault_end" đánh dấu ranh giới 3 pha
(bình thường → có lỗi → phục hồi) cho cap_metrics_export.py; ghi vào summary.json → phase_marks.
Dấu ngoặc nhọn thật trong "cmd" phải viết {{ và }}.
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import platform
import re
import signal
import string
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB_ROOT / "lib"))
import labctl  # noqa: E402

ACTIONS = {"marker", "partition", "heal", "netem", "clear_netem", "pause", "unpause",
           "snapshot", "exec", "reset"}
NEEDS_TARGET = {"partition", "heal", "netem", "clear_netem", "pause", "unpause"}
INJECT_TO_CLEAR = {"partition": "heal", "netem": "clear_netem", "pause": "unpause"}
CLEAR_TO_INJECT = {v: k for k, v in INJECT_TO_CLEAR.items()}
CSV_FIELDS = ["run_id", "seq", "at_s", "action", "target", "label", "phase", "ok", "rc",
              "ts_planned_ms", "ts_start_ms", "ts_done_ms", "offset_done_s",
              "drift_start_ms", "apply_ms", "iso_done", "detail"]


def now_ms() -> int:
    return time.time_ns() // 1_000_000


def iso(ms: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms / 1000)) + f".{ms % 1000:03d}Z"


class SafeDict(dict):
    """format_map giữ nguyên {khóa} nếu chưa có giá trị (để báo lỗi rõ ràng sau)."""

    def __missing__(self, key):
        return "{" + key + "}"


def placeholders(s: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(s) if f}


# ---------------------------------------------------------------------------
def load_scenario(path: Path) -> dict:
    sc = json.loads(path.read_text(encoding="utf-8"))
    for k in ("name", "duration_s", "events"):
        if k not in sc:
            raise ValueError(f"Kịch bản thiếu khóa '{k}'")
    dur = float(sc["duration_s"])
    for i, ev in enumerate(sc["events"]):
        a = ev.get("action")
        if a not in ACTIONS:
            raise ValueError(f"Sự kiện #{i}: action '{a}' không hợp lệ (hợp lệ: {sorted(ACTIONS)})")
        if "at_s" not in ev:
            raise ValueError(f"Sự kiện #{i} ({a}) thiếu at_s")
        if not 0 <= float(ev["at_s"]) <= dur:
            raise ValueError(f"Sự kiện #{i} ({a}) có at_s={ev['at_s']} nằm ngoài [0, {dur}]")
        if a in NEEDS_TARGET and not ev.get("target"):
            raise ValueError(f"Sự kiện #{i} ({a}) thiếu target")
        if a == "netem" and not (ev.get("delay_ms") or ev.get("loss_pct")):
            raise ValueError(f"Sự kiện #{i} (netem) cần delay_ms hoặc loss_pct")
        if a == "exec" and not ev.get("cmd"):
            raise ValueError(f"Sự kiện #{i} (exec) thiếu cmd")
    sc["events"] = sorted(sc["events"], key=lambda e: float(e["at_s"]))
    # cảnh báo lỗi tiêm mà không gỡ (runner vẫn auto-reset ở cuối)
    open_ = set()
    for ev in sc["events"]:
        a, t = ev["action"], ev.get("target")
        if a in INJECT_TO_CLEAR:
            open_.add((a, t))
        elif a in CLEAR_TO_INJECT:
            open_.discard((CLEAR_TO_INJECT[a], t))
    for a, t in open_:
        print(f"[WARN] {a} trên {t} không có sự kiện gỡ tương ứng — sẽ được auto-reset ở cuối run", file=sys.stderr)
    return sc


# ---------------------------------------------------------------------------
class Grafana:
    def __init__(self, url: str | None):
        self.url = url.rstrip("/") if url else None
        self.user = os.environ.get("GRAFANA_USER", "admin")
        self.password = os.environ.get("GRAFANA_PASSWORD", "admin")
        self.warned = False

    def post(self, ts_ms: int, text: str, tags: list[str], end_ms: int | None = None) -> None:
        if not self.url:
            return
        body = {"time": ts_ms, "text": text, "tags": tags}
        if end_ms:
            body["timeEnd"] = end_ms
        data = json.dumps(body).encode()
        for auth in (False, True):  # thử anonymous trước (mặc định scylla-monitoring cho phép)
            req = urllib.request.Request(f"{self.url}/api/annotations", data=data, method="POST",
                                         headers={"Content-Type": "application/json"})
            if auth:
                tok = base64.b64encode(f"{self.user}:{self.password}".encode()).decode()
                req.add_header("Authorization", f"Basic {tok}")
            try:
                with urllib.request.urlopen(req, timeout=3):
                    return
            except urllib.error.HTTPError as e:
                if e.code in (401, 403) and not auth:
                    continue
                break
            except Exception:  # noqa: BLE001
                break
        if not self.warned:
            print("[WARN] Không đẩy được annotation lên Grafana (bỏ qua, không ảnh hưởng run)", file=sys.stderr)
            self.warned = True


# ---------------------------------------------------------------------------
class Runner:
    def __init__(self, args, scenario: dict, params: dict):
        self.args = args
        self.sc = scenario
        self.params = params
        self.dry = args.dry_run
        self.scale = args.time_scale if self.dry else 1.0
        self.duration_s = float(scenario["duration_s"])
        stamp = time.strftime("%Y%m%d_%H%M%S")
        self.run_id = args.run_id or f"{scenario['name']}_{stamp}"
        self.run_dir = Path(args.runs_dir).expanduser().resolve() / self.run_id
        self.grafana = Grafana(None if (args.no_annotate or self.dry) else args.grafana)
        self.aliases: dict[str, str] = {}
        self.open_faults: dict[tuple[str, str], tuple[int, str]] = {}
        self.lock = threading.Lock()
        self.bg: list[threading.Thread] = []
        self.harness: subprocess.Popen | None = None
        self.harness_log = None
        self.stop = threading.Event()
        self.records: list[dict] = []
        self.meta: dict = {}
        self.aborted = False
        self.t0_ms = 0
        self.t0_mono = 0.0
        self.child_env = dict(os.environ)
        self.child_env.update({"CHAOS_LOG": str(self.run_dir / "chaos_ops.jsonl"), "CHAOS_ANNOTATE": "0"})

    # ---------------- tiện ích ----------------
    def ctx(self) -> SafeDict:
        d = SafeDict(self.params)
        d.update({"run_id": self.run_id, "run_dir": str(self.run_dir), "lab_root": str(LAB_ROOT),
                  "t0_ms": str(self.t0_ms), "duration_s": f"{self.duration_s:g}",
                  "scenario": self.sc["name"]})
        return d

    def fmt(self, s: str) -> str:
        return s.format_map(self.ctx())

    def check_placeholders(self) -> None:
        known = set(self.ctx().keys())
        texts = [ev["cmd"] for ev in self.sc["events"] if ev["action"] == "exec"]
        if self.args.harness_cmd:
            texts.append(self.args.harness_cmd)
        missing = set()
        for t in texts:
            missing |= placeholders(t) - known
        if missing:
            raise SystemExit(f"Thiếu tham số cho placeholder: {sorted(missing)} → thêm --param tên=giá_trị")

    def log(self, rec: dict) -> None:
        with self.lock:
            self.records.append(rec)
            with open(self.run_dir / "events.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            new = not (self.run_dir / "events.csv").exists()
            with open(self.run_dir / "events.csv", "a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
                if new:
                    w.writeheader()
                w.writerow(rec)

    def sh(self, cmd: list[str], timeout: float) -> tuple[int, str]:
        if self.dry:
            return 0, "(dry-run) " + " ".join(cmd)
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=self.child_env)
            return p.returncode, (p.stdout + p.stderr).strip()
        except subprocess.TimeoutExpired:
            return 124, f"timeout sau {timeout}s"

    def resolve_target(self, t: str | None) -> str | None:
        if not t:
            return None
        t = self.fmt(t)
        if not t.startswith("@"):
            return t
        if t in self.aliases:
            return self.aliases[t]
        if t == "@mongo-primary":
            rc, out = self.sh([str(labctl.CHAOS_SH), "mongo-primary"], 60)
            name = out.strip().splitlines()[-1] if (rc == 0 and out.strip()) else ""
            if self.dry:
                name = "mongo1"
            if not name:
                raise RuntimeError(f"Không xác định được @mongo-primary: {out}")
            self.aliases[t] = name
            return name
        raise ValueError(f"Alias không hỗ trợ: {t}")

    def build_cmd(self, ev: dict, target: str | None) -> list[str] | None:
        a = ev["action"]
        c = str(labctl.CHAOS_SH)
        if a == "marker":
            return None
        if a == "partition":
            cmd = [c, "partition", target, "--mode", ev.get("mode", "peers")]
            if ev.get("from"):
                cmd += ["--from", ",".join(self.fmt(x) for x in ev["from"])]
            return cmd
        if a == "heal":
            return [c, "heal", target]
        if a == "netem":
            cmd = [c, "netem", target]
            if ev.get("delay_ms"):
                cmd += ["--delay", str(ev["delay_ms"])]
            if ev.get("jitter_ms"):
                cmd += ["--jitter", str(ev["jitter_ms"])]
            if ev.get("loss_pct"):
                cmd += ["--loss", str(ev["loss_pct"])]
            if ev.get("to"):
                cmd += ["--to", ",".join(self.fmt(x) for x in ev["to"])]
            return cmd
        if a == "clear_netem":
            return [c, "clear-netem", target]
        if a in ("pause", "unpause"):
            return [c, a, target]
        if a == "reset":
            return [c, "reset"]
        if a == "snapshot":
            return [str(labctl.SNAPSHOT_SH), str(self.run_dir), ev.get("label") or "snapshot"]
        if a == "exec":
            return ["bash", "-c", self.fmt(ev["cmd"])]
        raise ValueError(a)

    # ---------------- thực thi 1 sự kiện ----------------
    def execute(self, seq: int, ev: dict, planned_ms: int) -> dict:
        start = now_ms()
        try:
            target = self.resolve_target(ev.get("target"))
            cmd = self.build_cmd(ev, target)
        except Exception as e:  # noqa: BLE001
            target, cmd = ev.get("target"), None
            rec = self.make_record(seq, ev, target, planned_ms, start, now_ms(), False, 1, f"lỗi chuẩn bị: {e}")
            self.log(rec)
            return rec
        if cmd and ev.get("background"):
            th = threading.Thread(target=self._bg, args=(seq, ev, target, cmd), daemon=True)
            th.start()
            self.bg.append(th)
            rc, out = 0, "(chạy nền) " + " ".join(cmd[-1:] if cmd[0] == "bash" else cmd)
        elif cmd:
            rc, out = self.sh(cmd, float(ev.get("timeout_s", 90)))
        else:
            rc, out = 0, ""
        done = now_ms()
        rec = self.make_record(seq, ev, target, planned_ms, start, done, rc == 0, rc, out)
        self.log(rec)
        self.annotate(ev, rec)
        return rec

    def _bg(self, seq, ev, target, cmd):
        t1 = now_ms()
        rc, out = self.sh(cmd, float(ev.get("timeout_s", 600)))
        rec = self.make_record(f"{seq}b", {**ev, "action": ev["action"] + "_done"}, target, t1, t1, now_ms(),
                               rc == 0, rc, out)
        self.log(rec)

    def make_record(self, seq, ev, target, planned, start, done, ok, rc, out) -> dict:
        return {
            "run_id": self.run_id, "seq": seq, "at_s": ev.get("at_s"), "action": ev["action"],
            "target": target or "", "label": ev.get("label", ""), "phase": ev.get("phase", ""), "ok": ok, "rc": rc,
            "ts_planned_ms": planned, "ts_start_ms": start, "ts_done_ms": done,
            "offset_done_s": round((done - self.t0_ms) / 1000.0, 3),
            "drift_start_ms": start - planned, "apply_ms": done - start,
            "iso_done": iso(done), "detail": (out or "")[-1500:],
        }

    def annotate(self, ev: dict, rec: dict) -> None:
        a, t = ev["action"], rec["target"]
        if a in ("snapshot", "exec") and not ev.get("annotate"):
            return
        text = f"[{self.run_id}] {ev.get('label') or a} {t}".strip()
        tags = ["chaos", self.run_id, a] + ([t] if t else [])
        self.grafana.post(rec["ts_done_ms"], text + ("" if rec["ok"] else " (THẤT BẠI)"), tags)
        if a in INJECT_TO_CLEAR and rec["ok"]:
            self.open_faults[(a, t)] = (rec["ts_done_ms"], ev.get("label") or a)
        elif a in CLEAR_TO_INJECT:
            key = (CLEAR_TO_INJECT[a], t)
            if key in self.open_faults:
                start, label = self.open_faults.pop(key)
                self.grafana.post(start, f"[{self.run_id}] CỬA SỔ LỖI: {label} {t}",
                                  ["chaos", "fault-window", self.run_id], end_ms=rec["ts_done_ms"])

    # ---------------- harness ----------------
    def start_harness(self) -> None:
        if not self.args.harness_cmd:
            return
        cmd = self.fmt(self.args.harness_cmd)
        env = dict(self.child_env)
        env.update({"RUN_ID": self.run_id, "RUN_DIR": str(self.run_dir), "T0_EPOCH_MS": str(self.t0_ms),
                    "SCENARIO": self.sc["name"], "DURATION_S": f"{self.duration_s:g}"})
        env.update({f"PARAM_{k.upper()}": v for k, v in self.params.items()})
        self.harness_log = open(self.run_dir / "harness.log", "w", encoding="utf-8")
        start = now_ms()
        if self.dry:
            self.harness_log.write(f"(dry-run) {cmd}\n")
            self.harness_log.close()
            rec = self.make_record("H", {"action": "harness_start", "at_s": 0}, "", start, start, start, True, 0, cmd)
        else:
            self.harness = subprocess.Popen(["bash", "-c", cmd], stdout=self.harness_log, stderr=subprocess.STDOUT,
                                            env=env, start_new_session=True)
            rec = self.make_record("H", {"action": "harness_start", "at_s": 0}, "", start, start, now_ms(), True, 0,
                                   f"pid={self.harness.pid} {cmd}")
        self.log(rec)

    def _signal_harness(self, sig) -> None:
        try:
            os.killpg(self.harness.pid, sig)
        except (ProcessLookupError, PermissionError):
            pass

    def stop_harness(self, interrupted: bool = False) -> None:
        if not self.harness:
            return
        grace = 0.5 if interrupted else self.args.harness_grace_s
        try:
            rc = self.harness.wait(timeout=grace)
            how = "tự kết thúc"
        except subprocess.TimeoutExpired:
            self._signal_harness(signal.SIGINT)
            try:
                rc = self.harness.wait(timeout=15)
                how = f"bị dừng (SIGINT) sau {grace}s chờ"
            except subprocess.TimeoutExpired:
                self._signal_harness(signal.SIGKILL)
                rc = self.harness.wait()
                how = "bị KILL"
        t = now_ms()
        self.log(self.make_record("H", {"action": "harness_exit", "at_s": None}, "", t, t, t, rc == 0, rc, how))
        if self.harness_log:
            self.harness_log.close()

    # ---------------- chạy ----------------
    def wait_until(self, offset_s: float) -> bool:
        """Ngủ tới T0 + offset_s (đồng hồ monotonic). Trả False nếu bị yêu cầu dừng."""
        target = self.t0_mono + offset_s * self.scale
        while True:
            if self.stop.is_set():
                return False
            rem = target - time.monotonic()
            if rem <= 0:
                return True
            time.sleep(min(rem - 0.002, 0.25) if rem > 0.004 else 0)

    def collect_meta(self) -> None:
        """Thu thập thông tin môi trường (chậm vì gọi docker) — làm TRƯỚC khi chốt T0."""
        meta = {
            "run_id": self.run_id, "scenario": self.sc, "params": self.params,
            "harness_cmd": self.args.harness_cmd, "dry_run": self.dry, "time_scale": self.scale,
            "host": platform.node(), "kernel": platform.release(), "python": platform.python_version(),
            "lab_env": labctl.LAB_ENV,
        }
        if not self.dry:
            rc, out = self.sh(["docker", "exec", "scylla-node1", "scylla", "--version"], 30)
            meta["scylla_version"] = out if rc == 0 else None
            rc, out = self.sh(["docker", "version", "--format", "{{.Server.Version}}"], 30)
            meta["docker_server"] = out if rc == 0 else None
            meta["scylla_nodes"] = labctl.scylla_nodes()
            meta["mongo_nodes"] = labctl.mongo_nodes()
        self.meta = meta

    def write_meta(self) -> None:
        self.meta.update({"t0_ms": self.t0_ms, "t0_iso": iso(self.t0_ms),
                          "t_planned_end_ms": self.t0_ms + int(self.duration_s * self.scale * 1000)})
        (self.run_dir / "meta.json").write_text(json.dumps(self.meta, ensure_ascii=False, indent=2),
                                                encoding="utf-8")

    def precheck(self) -> None:
        if self.dry or self.args.skip_precheck:
            return
        uses_scylla = any(str(ev.get("target", "")).startswith("scylla") for ev in self.sc["events"])
        if uses_scylla or self.args.require_un:
            ok, msg = labctl.all_un()
            if not ok:
                raise SystemExit(f"Precheck thất bại: {msg}  (dùng --skip-precheck nếu cố ý)")
            print(f"[OK] Precheck: {msg}")
        rc, out = self.sh([str(labctl.CHAOS_SH), "reset"], 120)
        if rc != 0:
            raise SystemExit(f"Không reset được lỗi cũ: {out}")
        targets = sorted({self.fmt(ev["target"]) for ev in self.sc["events"]
                          if ev.get("target") and ev["action"] in ("partition", "heal", "netem", "clear_netem")
                          and not str(ev["target"]).startswith("@")})
        if any(str(ev.get("target", "")).startswith("@mongo") for ev in self.sc["events"]):
            targets += labctl.mongo_nodes()
        if targets:
            rc, out = self.sh([str(labctl.CHAOS_SH), "prepare", *targets], 180)
            if rc != 0:
                raise SystemExit(f"Không tạo được sidecar: {out}")

    def run(self) -> int:
        if self.run_dir.exists() and any(self.run_dir.iterdir()):
            if not self.args.force:
                raise SystemExit(f"{self.run_dir} đã tồn tại (dùng --force hoặc --run-id khác)")
            for f in ("events.jsonl", "events.csv", "summary.json"):
                (self.run_dir / f).unlink(missing_ok=True)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.check_placeholders()
        self.precheck()
        self.collect_meta()

        lead = max(0.0, self.args.lead_s)
        if self.args.t0_ms:
            self.t0_ms = int(self.args.t0_ms)
        else:
            self.t0_ms = now_ms() + int(lead * 1000)
        # ánh xạ T0 (đồng hồ thực) sang đồng hồ monotonic để lập lịch không bị ảnh hưởng khi chỉnh giờ
        self.t0_mono = time.monotonic() + (self.t0_ms - now_ms()) / 1000.0
        self.write_meta()
        print(f"\n== RUN {self.run_id} | kịch bản {self.sc['name']} | {self.duration_s:g}s | "
              f"T0 = {iso(self.t0_ms)} ({self.t0_ms}) | thư mục {self.run_dir}")

        def on_signal(signum, _frame):
            print(f"\n[WARN] Nhận tín hiệu {signum} → dừng kịch bản và dọn lỗi...", file=sys.stderr)
            self.stop.set()
        signal.signal(signal.SIGINT, on_signal)
        signal.signal(signal.SIGTERM, on_signal)

        interrupted = False
        try:
            if not self.wait_until(0):
                interrupted = True
            else:
                t0rec = self.make_record("T0", {"action": "t0", "at_s": 0, "label": "T0"}, "",
                                         self.t0_ms, now_ms(), now_ms(), True, 0, "")
                self.log(t0rec)
                self.grafana.post(self.t0_ms, f"[{self.run_id}] T0 — bắt đầu {self.sc['name']}",
                                  ["chaos", self.run_id, "t0"])
                self.start_harness()
                for seq, ev in enumerate(self.sc["events"], start=1):
                    at = float(ev["at_s"])
                    if not self.wait_until(at):
                        interrupted = True
                        break
                    planned = self.t0_ms + int(at * self.scale * 1000)
                    rec = self.execute(seq, ev, planned)
                    flag = "OK " if rec["ok"] else "LỖI"
                    print(f"  [{flag}] T+{rec['offset_done_s']:8.3f}s  #{seq:<2} {ev['action']:<11} "
                          f"{rec['target']:<14} drift={rec['drift_start_ms']:>4}ms apply={rec['apply_ms']:>5}ms  "
                          f"{ev.get('label', '')}")
                    if not rec["ok"]:
                        print(f"        ↳ {rec['detail'][-300:]}")
                        if ev.get("critical", ev["action"] in INJECT_TO_CLEAR) and not self.args.continue_on_error:
                            print("[FAIL] Sự kiện tiêm lỗi thất bại → dừng run (dùng --continue-on-error để bỏ qua)")
                            self.aborted = True
                            break
                if not interrupted and not self.aborted and not self.wait_until(self.duration_s):
                    interrupted = True
        finally:
            t_end = now_ms()
            self.stop_harness(interrupted or self.aborted or self.stop.is_set())
            for th in self.bg:
                th.join(timeout=60)
            if not self.args.no_auto_reset:
                rc, out = self.sh([str(labctl.CHAOS_SH), "reset"], 120)
                t = now_ms()
                self.log(self.make_record("R", {"action": "auto_reset", "at_s": None}, "*", t, t, t, rc == 0, rc, out))
            self.write_summary(t_end, interrupted)
        if interrupted:
            return 130
        if self.aborted:
            return 1
        failed = [r for r in self.records if isinstance(r["seq"], int) and not r["ok"]]
        return 1 if failed else 0

    def write_summary(self, t_end: int, interrupted: bool) -> None:
        evs = [r for r in self.records if isinstance(r["seq"], int)]
        faults = [r for r in evs if r["action"] in INJECT_TO_CLEAR or r["action"] in CLEAR_TO_INJECT]
        summary = {
            "run_id": self.run_id, "scenario": self.sc["name"], "params": self.params,
            "t0_ms": self.t0_ms, "t0_iso": iso(self.t0_ms),
            "t_end_ms": t_end, "t_end_iso": iso(t_end),
            "t_planned_end_ms": self.t0_ms + int(self.duration_s * self.scale * 1000),
            "interrupted": interrupted, "aborted_on_error": self.aborted,
            "n_events": len(evs), "n_failed": sum(1 for r in evs if not r["ok"]),
            "max_drift_start_ms": max((abs(r["drift_start_ms"]) for r in evs), default=0),
            "max_apply_ms_faults": max((r["apply_ms"] for r in faults), default=0),
            "fault_events": [{k: r[k] for k in ("seq", "action", "target", "label", "phase", "at_s",
                                                 "offset_done_s", "ts_done_ms", "apply_ms", "ok")} for r in faults],
            "phase_marks": {r["phase"]: r["ts_done_ms"] for r in evs if r.get("phase")},
        }
        (self.run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                                   encoding="utf-8")
        print(f"\n== KẾT THÚC {self.run_id}: {summary['n_events']} sự kiện, {summary['n_failed']} lỗi, "
              f"độ lệch khởi động tối đa {summary['max_drift_start_ms']}ms, "
              f"thời gian áp lỗi tối đa {summary['max_apply_ms_faults']}ms"
              f"{' (BỊ NGẮT)' if interrupted else ''}{' (DỪNG VÌ LỖI)' if self.aborted else ''}")
        print(f"   → {self.run_dir}/events.csv")


# ---------------------------------------------------------------------------
def parse_params(items: list[str]) -> dict:
    out = {}
    for it in items or []:
        if "=" not in it:
            raise SystemExit(f"--param phải có dạng tên=giá_trị: {it}")
        k, v = it.split("=", 1)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k):
            raise SystemExit(f"Tên tham số không hợp lệ: {k}")
        out[k] = v
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Chạy kịch bản tiêm lỗi theo mốc thời gian",
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("scenario", type=Path)
    ap.add_argument("--run-id")
    ap.add_argument("--runs-dir", default=str(labctl.RUNS_DIR))
    ap.add_argument("--param", action="append", default=[], help="tên=giá_trị (dùng trong {tên} của cmd/harness)")
    ap.add_argument("--harness-cmd", help="lệnh harness chạy song song từ T0 (có thể dùng {run_dir}, {duration_s}...)")
    ap.add_argument("--harness-grace-s", type=float, default=60, help="chờ harness tự thoát sau khi hết kịch bản")
    ap.add_argument("--lead-s", type=float, default=3, help="T0 = bây giờ + lead (để chuẩn bị xong trước T0)")
    ap.add_argument("--t0-ms", type=int, help="ép T0 tuyệt đối (epoch ms) để khớp với harness chạy riêng")
    ap.add_argument("--grafana", default=labctl.LAB_ENV.get("GRAFANA_URL", "http://localhost:3000"))
    ap.add_argument("--no-annotate", action="store_true")
    ap.add_argument("--no-auto-reset", action="store_true", help="không gỡ lỗi khi kết thúc (KHÔNG khuyến nghị)")
    ap.add_argument("--skip-precheck", action="store_true")
    ap.add_argument("--require-un", action="store_true", help="bắt buộc cụm UN kể cả khi kịch bản không đụng Scylla")
    ap.add_argument("--continue-on-error", action="store_true")
    ap.add_argument("--force", action="store_true", help="ghi đè thư mục run đã có")
    ap.add_argument("--dry-run", action="store_true", help="không gọi docker, chỉ chạy lịch")
    ap.add_argument("--time-scale", type=float, default=1.0, help="(chỉ dry-run) nén thời gian, vd 0.05")
    args = ap.parse_args(argv)
    scenario = load_scenario(args.scenario)
    runner = Runner(args, scenario, parse_params(args.param))
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())
