"""Unified simulation launcher for Robo-helper-in-Hospital.

Launches all backend Python servers (YOLO, STT/NLU, optional TTS) and Godot
in a single command, waits for WebSocket servers to be ready, and cleanly shuts down
all child processes when Godot exits or Ctrl+C is pressed.
"""

from __future__ import annotations

import argparse
import atexit
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parent
PYTHON_DIR = REPO_ROOT / "sim_vision" / "python"
GODOT_DIR = REPO_ROOT / "sim_vision" / "godot"

CHILD_PROCESSES: List[subprocess.Popen] = []


def log(msg: str) -> None:
    """Print immediately with flush."""
    print(msg, flush=True)


def cleanup() -> None:
    """Terminate all spawned server subprocesses."""
    if not CHILD_PROCESSES:
        return
    log("\n[Launcher] Shutting down background servers...")
    for p in CHILD_PROCESSES:
        if p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass
    time.sleep(0.5)
    for p in CHILD_PROCESSES:
        if p.poll() is None:
            try:
                p.kill()
            except Exception:
                pass
    CHILD_PROCESSES.clear()
    log("[Launcher] All servers stopped.")


def handle_signal(sig, frame) -> None:
    cleanup()
    sys.exit(0)


def find_python() -> Path:
    """Find the preferred Python executable with project dependencies."""
    candidates = [
        REPO_ROOT / ".venv" / "Scripts" / "python.exe",
        REPO_ROOT / ".venv" / "bin" / "python",
        PYTHON_DIR / ".venv" / "Scripts" / "python.exe",
        PYTHON_DIR / ".venv" / "bin" / "python",
        Path(sys.executable),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return Path(sys.executable)


def find_tts_python(default: Path) -> Path:
    """TTS cần venv riêng .venv-tts (gói vieneu); không có thì dùng Python chính."""
    for c in [
        PYTHON_DIR / ".venv-tts" / "Scripts" / "python.exe",
        PYTHON_DIR / ".venv-tts" / "bin" / "python",
        REPO_ROOT / ".venv-tts" / "Scripts" / "python.exe",
        REPO_ROOT / ".venv-tts" / "bin" / "python",
    ]:
        if c.is_file():
            return c
    return default


def find_godot(explicit_path: Optional[str] = None) -> Optional[Path]:
    """Find the Godot binary across Windows, macOS, and Linux."""
    if explicit_path and Path(explicit_path).is_file():
        return Path(explicit_path)

    env_path = os.environ.get("GODOT_BIN")
    if env_path and Path(env_path).is_file():
        return Path(env_path)

    import shutil

    # 1. System PATH lookup (works on Linux, macOS with brew, Windows)
    for name in ["godot", "godot4", "godot-bin", "godot.exe", "godot4.exe"]:
        found = shutil.which(name)
        if found:
            return Path(found)

    # 2. macOS common application bundles and paths
    if sys.platform == "darwin":
        mac_candidates = [
            Path("/Applications/Godot.app/Contents/MacOS/Godot"),
            Path("/Applications/Godot_4.app/Contents/MacOS/Godot"),
            Path.home() / "Applications" / "Godot.app" / "Contents" / "MacOS" / "Godot",
            Path("/opt/homebrew/bin/godot"),
            Path("/usr/local/bin/godot"),
        ]
        for c in mac_candidates:
            if c.is_file():
                return c

    # 3. Windows Downloads folder search
    if sys.platform == "win32":
        downloads_dir = Path.home() / "Downloads"
        download_candidates = list(downloads_dir.glob("**/Godot*.exe"))
        # Prefer console executable if available (outputs logs to terminal)
        for c in sorted(download_candidates, key=lambda x: "console" not in x.name.lower()):
            if c.is_file():
                return c

    # 4. Linux common user paths & Flatpak
    if sys.platform.startswith("linux"):
        linux_candidates = [
            Path.home() / ".local" / "bin" / "godot",
            Path.home() / ".local" / "bin" / "godot4",
            Path.home() / "bin" / "godot",
            Path("/usr/bin/godot"),
            Path("/usr/local/bin/godot"),
            Path("/var/lib/flatpak/exports/bin/org.godotengine.Godot"),
            Path.home() / ".local" / "share" / "flatpak" / "exports" / "bin" / "org.godotengine.Godot",
        ]
        for c in linux_candidates:
            if c.is_file():
                return c

    return None


def wait_for_ws(
    port: int,
    host: str = "127.0.0.1",
    timeout: float = 180.0,
    desc: str = "",
    proc: Optional[subprocess.Popen] = None,
) -> bool:
    """Wait until WebSocket server is ready and responds to handshake."""
    start = time.time()
    url = f"ws://{host}:{port}"
    log(f"[Launcher] Waiting for {desc} on {url} (timeout={int(timeout)}s)...")
    while time.time() - start < timeout:
        if proc is not None and proc.poll() is not None:
            log(f"[Launcher] -> {desc} exited unexpectedly with code {proc.returncode}!")
            return False
        try:
            from websockets.sync.client import connect
            with connect(url, open_timeout=1.0, close_timeout=1.0) as ws:
                elapsed = time.time() - start
                log(f"[Launcher] -> {desc} is ready! ({elapsed:.1f}s)")
                return True
        except Exception:
            time.sleep(0.5)
    log(f"[Launcher] -> {desc} timed out after {timeout}s!")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified Simulation Launcher")
    parser.add_argument(
        "--nlu",
        choices=["rule", "phobert"],
        default="rule",
        help="NLU engine to use ('rule' or 'phobert', default: rule)",
    )
    parser.add_argument(
        "--with-tts",
        action="store_true",
        default=None,
        help="Force launch TTS server (port 8767). Default: auto-detect if VieNeu model is present",
    )
    parser.add_argument(
        "--no-tts",
        action="store_true",
        help="Disable TTS server even if models are present (runs in subtitle fallback mode)",
    )
    parser.add_argument(
        "--godot",
        type=str,
        default=None,
        help="Path to Godot executable",
    )
    parser.add_argument(
        "--no-godot",
        action="store_true",
        help="Only launch backend servers without starting Godot",
    )
    parser.add_argument(
        "--scene",
        type=str,
        default=None,
        help="Optional Godot scene to launch (e.g. res://tools/dialogue_batch.tscn)",
    )
    parser.add_argument(
        "--controller",
        choices=["fsm", "rl"],
        default="fsm",
        help="Robot navigation controller mode ('fsm' rule-based or 'rl' RLController + RLEnvBridge)",
    )
    parser.add_argument(
        "--rl-checkpoint",
        type=str,
        default=None,
        help="PPO checkpoint (.pt) served by rl_policy_server.py on port 8768 (default: experiments/checkpoints/PPOHospital-full_strongest.pt)",
    )
    parser.add_argument(
        "--solo-patient",
        "--solo_patient",
        "--solo",
        dest="solo_patient",
        action="store_true",
        help="Run simulation with exactly 1 active patient and robot spawning nearby (no doctor/crowd)",
    )
    parser.add_argument(
        "--escort-only",
        "--escort_only",
        "--escort",
        dest="escort_only",
        action="store_true",
        help="Patients strictly request escort to hospital clinic rooms across Floors 1, 2, and 3",
    )

    # Sanitize sys.argv against accidental quotes, trailing spaces, or Unicode dashes
    clean_argv: List[str] = []
    dash_chars = str.maketrans({
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2212": "-",
        "\ufe58": "-",
        "\uff0d": "-",
    })
    for a in sys.argv[1:]:
        s = a.translate(dash_chars).strip()
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            s = s[1:-1].strip()
        if s:
            clean_argv.append(s)

    args = parser.parse_args(clean_argv)

    # Register exit hooks
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    py_exe = find_python()
    log(f"[Launcher] Python executable: {py_exe}")

    sub_env = {**os.environ, "PYTHONUNBUFFERED": "1"}

    # 1. Start YOLO server (Port 8765)
    log("[Launcher] Starting YOLO server on port 8765...")
    yolo_model_path = REPO_ROOT / "models" / "yolov8n" / "yolov8n.pt"
    yolo_proc = subprocess.Popen(
        [str(py_exe), "yolo_server.py", "--model", str(yolo_model_path.resolve())],
        cwd=PYTHON_DIR,
        env=sub_env,
    )
    CHILD_PROCESSES.append(yolo_proc)

    # 2. Start STT + NLU server (Port 8766)
    log(f"[Launcher] Starting STT + NLU server on port 8766 (NLU mode: {args.nlu})...")
    stt_proc = subprocess.Popen(
        [str(py_exe), "-m", "voice.stt_server", "--nlu", args.nlu],
        cwd=PYTHON_DIR,
        env=sub_env,
    )
    CHILD_PROCESSES.append(stt_proc)

    # 3. TTS server (Port 8767) — auto-detected or explicitly enabled
    tts_onnx = REPO_ROOT / "models" / "Vie-neu-v3-turbo" / "onnx_update" / "vieneu_prefill.onnx"
    should_run_tts = (args.with_tts or (tts_onnx.is_file() and not args.no_tts)) and not args.no_tts

    if should_run_tts:
        tts_py = find_tts_python(py_exe)
        log(f"[Launcher] Starting TTS server on port 8767 (VieNeu-TTS v3 Turbo) via {tts_py}...")
        tts_proc = subprocess.Popen(
            [str(tts_py), "-m", "tts.tts_server"],
            cwd=PYTHON_DIR,
            env=sub_env,
        )
        CHILD_PROCESSES.append(tts_proc)
    else:
        log("[Launcher] TTS server disabled/skipped. Simulation will run in subtitle fallback mode.")

    # 4. RL policy server (Port 8768) — PPO checkpoint lái robot trong Godot (--controller rl)
    rl_proc = None
    if args.controller == "rl":
        rl_cmd = [str(py_exe), "rl_policy_server.py", "--trace"]
        if args.rl_checkpoint:
            rl_cmd += ["--checkpoint", str(Path(args.rl_checkpoint).resolve())]
        log(f"[Launcher] Starting RL policy server on port 8768 ({args.rl_checkpoint or 'default checkpoint'})...")
        rl_proc = subprocess.Popen(rl_cmd, cwd=PYTHON_DIR, env=sub_env)
        CHILD_PROCESSES.append(rl_proc)

    # Wait for WebSocket servers to be healthy
    ok_yolo = wait_for_ws(8765, desc="YOLO Server", proc=yolo_proc)
    ok_stt = wait_for_ws(8766, desc="STT Server", proc=stt_proc)
    if should_run_tts:
        wait_for_ws(8767, desc="TTS Server", proc=tts_proc)
    if rl_proc is not None and not wait_for_ws(8768, desc="RL Policy Server", proc=rl_proc):
        log("[Launcher] WARNING: RL policy server not ready; Godot falls back to the rule-based RL controller.")

    if not ok_yolo or not ok_stt:
        log("[Launcher] ERROR: One or more backend servers failed to start.")
        cleanup()
        sys.exit(1)

    log("[Launcher] All required backend servers are online.")

    if args.no_godot:
        log("[Launcher] Running in server-only mode. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return

    # Find and launch Godot
    godot_exe = find_godot(args.godot)
    if not godot_exe:
        log("[Launcher] ERROR: Could not find Godot executable.")
        log("          Please specify it using --godot <path_to_godot_exe>")
        log("          or set the GODOT_BIN environment variable.")
        cleanup()
        sys.exit(1)

    log(f"[Launcher] Launching Godot: {godot_exe} (controller={args.controller})")
    godot_cmd = [str(godot_exe), "--path", str(GODOT_DIR)]
    if args.scene:
        godot_cmd.append(args.scene)
    extra_godot_args: List[str] = []
    if args.controller == "rl":
        extra_godot_args.append("--controller=rl")
    if args.solo_patient:
        extra_godot_args.append("--solo-patient")
        log("[Launcher] Solo Patient Mode active: 1 patient only, robot nearby spawn, no extra crowd.")
    if args.escort_only:
        extra_godot_args.append("--escort-only")
        log("[Launcher] Escort Only Mode active: Patients strictly request escort to clinic rooms across Floors 1-3.")
    if extra_godot_args:
        godot_cmd.append("--")
        godot_cmd.extend(extra_godot_args)

    godot_proc = subprocess.Popen(godot_cmd)
    CHILD_PROCESSES.append(godot_proc)

    try:
        godot_proc.wait()
        log(f"[Launcher] Godot exited with code {godot_proc.returncode}.")
    except KeyboardInterrupt:
        log("\n[Launcher] Interrupted by user.")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
