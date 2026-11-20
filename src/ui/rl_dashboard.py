"""Interactive Gradio Web Dashboard for Hospital Helper Robot RL Training.

Features:
1. Start new runs or resume/force-resume from previous runs with full tick-box flags.
2. Real-time live telemetry: streaming reward curves, losses, patients helped, and logs.
3. Historical inspection: instantly load and plot previous runs from experiments/runs/.
4. One-click shortcut to launch the interactive Godot 3D simulation with trained checkpoints.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXPERIMENTS_ROOT = REPO_ROOT / "experiments"
RUNS_DIR = EXPERIMENTS_ROOT / "runs"
PYTHON_EXE = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
if not PYTHON_EXE.is_file():
    PYTHON_EXE = Path(sys.executable)

# Global process tracking
CURRENT_PROCESS: Optional[subprocess.Popen] = None
CURRENT_RUN_DIR: Optional[Path] = None
CURRENT_RUN_NAME: str = ""
CURRENT_LOG_PATH: Optional[Path] = None
CURRENT_METRICS_PATH: Optional[Path] = None
LOG_STREAM_BUFFER: collections.deque[str] = collections.deque(maxlen=300)


def _drain_stdout(proc: subprocess.Popen) -> None:
    """Continuously drain process stdout lines to prevent OS pipe buffer deadlocks."""
    if proc.stdout is None:
        return
    try:
        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            LOG_STREAM_BUFFER.append(line.rstrip())
    except Exception:
        pass
    finally:
        try:
            proc.stdout.close()
        except Exception:
            pass


def find_existing_runs() -> List[Tuple[str, str]]:
    """Scan experiments/runs/ for completed and ongoing runs.

    Returns a list of (label, run_dir_path) sorted newest first.
    """
    if not RUNS_DIR.is_dir():
        return []

    runs: List[Tuple[float, str, str]] = []
    for entry in RUNS_DIR.iterdir():
        if not entry.is_dir():
            continue
        # Look for history file
        metrics_dir = entry / "metrics"
        hist_files = list(metrics_dir.glob("*_history.jsonl")) if metrics_dir.is_dir() else []
        mtime = entry.stat().st_mtime

        label = entry.name
        if hist_files:
            try:
                lines = hist_files[0].read_text(encoding="utf-8").strip().splitlines()
                if lines:
                    records = [json.loads(l) for l in lines if l.strip()]
                    if records:
                        ep = records[-1].get("epoch", len(records))
                        peak_r = max(float(r.get("val_r_team", 0.0)) for r in records)
                        helped = float(records[-1].get("val_patients_helped", 0.0))
                        label = f"{entry.name} (Ep {ep} | Peak R: {peak_r:.1f} | Help: {helped:.1f})"
            except Exception:
                pass
        runs.append((mtime, label, str(entry.resolve())))

    runs.sort(key=lambda x: x[0], reverse=True)
    return [(r[1], r[2]) for r in runs]


def load_history_records(run_dir_str: str) -> List[Dict[str, Any]]:
    """Read metrics history records from a given run directory."""
    if not run_dir_str:
        return []
    p = Path(run_dir_str)
    metrics_dir = p / "metrics"
    if not metrics_dir.is_dir():
        return []
    hist_files = list(metrics_dir.glob("*_history.jsonl"))
    if not hist_files:
        return []

    records: List[Dict[str, Any]] = []
    try:
        for line in hist_files[0].read_text(encoding="utf-8").strip().splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
    except Exception:
        pass
    return records


def _style_dark_ax(fig: plt.Figure, ax: plt.Axes, title: str, xlabel: str = "Epoch", ylabel: str = "") -> None:
    """Apply high-contrast dark theme styling to a matplotlib axes."""
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")
    ax.set_title(title, fontsize=11, fontweight="bold", color="#f8fafc", pad=8)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color="#cbd5e1", fontweight="bold")
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color="#cbd5e1", fontweight="bold")
    ax.tick_params(colors="#cbd5e1", labelsize=8.5)
    for spine in ax.spines.values():
        spine.set_edgecolor("#475569")
        spine.set_linewidth(1.0)
    ax.grid(True, linestyle="--", alpha=0.35, color="#475569")


def generate_metric_plots(records: List[Dict[str, Any]]) -> Tuple[plt.Figure, plt.Figure, plt.Figure, plt.Figure]:
    """Generate 4 high-contrast matplotlib figures for Reward, Loss, Productivity, and Safety."""
    if not records:
        # Return empty placeholder figures
        figs = []
        for title in ["Reward Curve (R_team)", "Optimization Losses", "Patients Helped / Shift", "Safety & Collisions"]:
            fig, ax = plt.subplots(figsize=(6, 3.2), facecolor="#0f172a")
            _style_dark_ax(fig, ax, title, "", "")
            ax.text(0.5, 0.5, "No data available yet\n(Start training or select a run)", ha="center", va="center", color="#94a3b8", fontsize=11, fontweight="semibold")
            ax.set_xticks([])
            ax.set_yticks([])
            fig.tight_layout()
            figs.append(fig)
        return figs[0], figs[1], figs[2], figs[3]

    epochs = [r.get("epoch", idx + 1) for idx, r in enumerate(records)]
    train_r = [r.get("train_r_team", 0.0) for r in records]
    val_r = [r.get("val_r_team", 0.0) for r in records]
    train_loss = [r.get("train_loss", 0.0) for r in records]
    val_loss = [r.get("val_loss", 0.0) for r in records]
    helped = [r.get("val_patients_helped", 0.0) for r in records]
    collisions = [r.get("val_collisions", 0.0) for r in records]

    # 1. Reward plot
    fig_r, ax_r = plt.subplots(figsize=(6, 3.2), facecolor="#0f172a")
    _style_dark_ax(fig_r, ax_r, "Shared Team Reward (R_team)", "Epoch", "R_team")
    ax_r.plot(epochs, train_r, label="Train R_team", color="#60a5fa", alpha=0.6, linestyle="--", linewidth=1.5)
    ax_r.plot(epochs, val_r, label="Val R_team", color="#38bdf8", linewidth=2.4, marker="o", markersize=4)
    if val_r:
        best_idx = int(np.argmax(val_r))
        ax_r.scatter([epochs[best_idx]], [val_r[best_idx]], color="#f43f5e", s=70, zorder=5, label=f"Peak: {val_r[best_idx]:.1f} (Ep {epochs[best_idx]})")
    ax_r.legend(loc="upper left", facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc", fontsize=8)
    fig_r.tight_layout()

    # 2. Loss plot
    fig_l, ax_l = plt.subplots(figsize=(6, 3.2), facecolor="#0f172a")
    _style_dark_ax(fig_l, ax_l, "PPO Optimization Loss", "Epoch", "Loss")
    ax_l.plot(epochs, train_loss, label="Train Loss", color="#fb923c", linewidth=2.0)
    ax_l.set_yscale("log" if any(v > 10.0 for v in train_loss) else "linear")
    ax_l.legend(loc="upper right", facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc", fontsize=8)
    fig_l.tight_layout()

    # 3. Productivity plot (Patients Helped)
    fig_p, ax_p = plt.subplots(figsize=(6, 3.2), facecolor="#0f172a")
    _style_dark_ax(fig_p, ax_p, "Shift Productivity (Patients Helped)", "Epoch", "Patients / Shift")
    ax_p.plot(epochs, helped, label="Patients Helped / Shift", color="#34d399", linewidth=2.2, marker="s", markersize=4)
    ax_p.legend(loc="upper left", facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc", fontsize=8)
    fig_p.tight_layout()

    # 4. Safety plot (Collisions)
    fig_s, ax_s = plt.subplots(figsize=(6, 3.2), facecolor="#0f172a")
    _style_dark_ax(fig_s, ax_s, "Safety: Wall/Obstacle Grazes", "Epoch", "Collisions / Shift")
    ax_s.plot(epochs, collisions, label="Mean Collisions", color="#f87171", linewidth=2.0)
    ax_s.legend(loc="upper right", facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc", fontsize=8)
    fig_s.tight_layout()

    return fig_r, fig_l, fig_p, fig_s


def find_checkpoints_for_run(run_dir_str: str) -> List[Tuple[str, str]]:
    """Scan checkpoints/ in run directory and return (label, path) pairs."""
    if not run_dir_str or not Path(run_dir_str).is_dir():
        return []
    ckpts_dir = Path(run_dir_str) / "checkpoints"
    if not ckpts_dir.is_dir():
        return []
    pt_files = sorted(list(ckpts_dir.glob("*.pt")), key=lambda p: p.stat().st_mtime, reverse=True)
    choices: List[Tuple[str, str]] = []
    for f in pt_files:
        name_lower = f.name.lower()
        if "best" in name_lower:
            lbl = f"⭐ {f.name} (Best Validation Performance)"
        elif "last" in name_lower:
            lbl = f"🏁 {f.name} (Latest Epoch Save)"
        else:
            lbl = f"💾 {f.name}"
        choices.append((lbl, str(f.resolve())))
    return choices


def inspect_run(run_dir_str: str) -> Tuple[Any, Any, Any, Any, str, str, str, str, str, Any]:
    """Inspect and load all metrics, figures, and status for a selected run directory."""
    if not run_dir_str or not Path(run_dir_str).is_dir():
        fig1, fig2, fig3, fig4 = generate_metric_plots([])
        return fig1, fig2, fig3, fig4, "-", "-", "-", "-", "Select a run to view details.", gr.update(choices=[], value="")

    p = Path(run_dir_str)
    records = load_history_records(run_dir_str)
    fig1, fig2, fig3, fig4 = generate_metric_plots(records)

    total_eps = len(records)
    best_r = 0.0
    best_ep = 0
    latest_helped = 0.0

    if records:
        for r in records:
            vr = float(r.get("val_r_team", 0.0))
            if vr > best_r:
                best_r = vr
                best_ep = r.get("epoch", 0)
        latest_helped = float(records[-1].get("val_patients_helped", 0.0))

    # Check for available checkpoints
    ckpts = find_checkpoints_for_run(run_dir_str)
    default_ckpt = ckpts[0][1] if ckpts else ""
    ckpt_update = gr.update(choices=[(l, p) for l, p in ckpts], value=default_ckpt)

    best_ckpt_str = Path(default_ckpt).name if default_ckpt else "None found"
    status_txt = f"Loaded {p.name}\nTotal Epochs Logged: {total_eps} | Best R_team: {best_r:.2f} (Epoch {best_ep})\nDefault Checkpoint: {best_ckpt_str}"
    ep_card = f"**{total_eps}**"
    r_card = f"**{best_r:.1f}** (Ep {best_ep})" if best_r > 0 else "**0.0**"
    help_card = f"**{latest_helped:.1f}**"
    eta_card = "**COMPLETED / IDLE**"

    return fig1, fig2, fig3, fig4, ep_card, r_card, help_card, eta_card, status_txt, ckpt_update


def start_training(
    mode: str,
    selected_prev_run: str,
    run_name: str,
    epochs: int,
    steps_per_epoch: int,
    patience: int,
    val_episodes: int,
    seed: int,
    stage_choice: str,
    env_mode_choice: str,
    use_cuda: bool,
    force_resume: bool,
    enable_tb: bool,
    smoke: bool,
) -> Tuple[str, bool, str]:
    """Launch the background training subprocess."""
    global CURRENT_PROCESS, CURRENT_RUN_DIR, CURRENT_RUN_NAME, CURRENT_LOG_PATH, CURRENT_METRICS_PATH

    if CURRENT_PROCESS is not None and CURRENT_PROCESS.poll() is None:
        return "⚠️ A training run is already in progress! Stop it first before starting a new one.", True, ""

    cmd = [
        str(PYTHON_EXE),
        "-m",
        "src.training.rl_hospital_train",
        "--epochs", str(epochs),
        "--steps-per-epoch", str(steps_per_epoch),
        "--patience", str(patience),
        "--val-episodes", str(val_episodes),
        "--seed", str(seed),
        "--device", "cuda" if use_cuda else "cpu",
    ]

    if enable_tb:
        cmd.append("--tb")
    if smoke:
        cmd.append("--smoke")

    if stage_choice == "Stage 1 only":
        cmd.extend(["--stage", "1"])
    elif stage_choice == "Stage 2 only":
        cmd.extend(["--stage", "2"])

    env_mode_val = "solo" if "solo" in str(env_mode_choice).lower() else "full"
    cmd.extend(["--env-mode", env_mode_val])

    if mode == "Continue from Previous Run":
        if not selected_prev_run:
            return "❌ Please select a previous run to continue from!", False, ""
        prev_p = Path(selected_prev_run)
        run_tag = prev_p.name.split("_", 2)[-1]
        cmd.extend(["--run-name", run_tag, "--resume-from", str(prev_p.resolve())])
        if force_resume:
            cmd.append("--force-resume")
        else:
            cmd.append("--resume")
        CURRENT_RUN_DIR = prev_p
        CURRENT_RUN_NAME = run_tag
    else:
        name_clean = run_name.strip() or "PPOHospital-ui"
        cmd.extend(["--run-name", name_clean])
        CURRENT_RUN_NAME = name_clean
        CURRENT_RUN_DIR = None

    # Launch subprocess with pipe draining thread to prevent deadlocks
    LOG_STREAM_BUFFER.clear()
    try:
        CURRENT_PROCESS = subprocess.Popen(
            cmd,
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        drain_t = threading.Thread(target=_drain_stdout, args=(CURRENT_PROCESS,), daemon=True)
        drain_t.start()
    except Exception as e:
        return f"❌ Failed to launch training process: {e}", False, ""

    msg = f"🚀 Training started successfully (PID: {CURRENT_PROCESS.pid})\nCommand: {' '.join(cmd)}"
    return msg, True, f"Running: {' '.join(cmd)}"


def stop_training() -> str:
    """Terminate the running training subprocess gracefully."""
    global CURRENT_PROCESS
    if CURRENT_PROCESS is None or CURRENT_PROCESS.poll() is not None:
        return "ℹ️ No training process is currently active."

    try:
        CURRENT_PROCESS.terminate()
        try:
            CURRENT_PROCESS.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            CURRENT_PROCESS.kill()
        return "⏹️ Training process stopped successfully. Checkpoints preserved."
    except Exception as e:
        return f"⚠️ Error stopping process: {e}"


def poll_status_and_metrics(selected_prev_run: str) -> Tuple[Any, Any, Any, Any, str, str, str, str, str, bool]:
    """Poll callback executed periodically when training is active."""
    global CURRENT_PROCESS, CURRENT_RUN_DIR, CURRENT_RUN_NAME

    is_running = CURRENT_PROCESS is not None and CURRENT_PROCESS.poll() is None

    # Locate the active run directory if not yet set
    target_dir = CURRENT_RUN_DIR
    if target_dir is None and CURRENT_RUN_NAME:
        latest = RUNS_DIR.glob(f"*_{CURRENT_RUN_NAME}")
        matches = sorted(list(latest), key=lambda p: p.stat().st_mtime, reverse=True)
        if matches:
            target_dir = matches[0]
            CURRENT_RUN_DIR = target_dir

    if target_dir is None:
        target_dir = Path(selected_prev_run) if selected_prev_run else None

    if target_dir is None or not target_dir.is_dir():
        fig1, fig2, fig3, fig4 = generate_metric_plots([])
        status = "RUNNING..." if is_running else "IDLE"
        return fig1, fig2, fig3, fig4, "**0**", "**0.0**", "**0.0**", f"**{status}**", status, is_running

    records = load_history_records(str(target_dir))
    fig1, fig2, fig3, fig4 = generate_metric_plots(records)

    total_eps = len(records)
    best_r = 0.0
    best_ep = 0
    latest_helped = 0.0

    if records:
        for r in records:
            vr = float(r.get("val_r_team", 0.0))
            if vr > best_r:
                best_r = vr
                best_ep = r.get("epoch", 0)
        latest_helped = float(records[-1].get("val_patients_helped", 0.0))

    # Read latest lines from memory stream buffer or fall back to log file
    if LOG_STREAM_BUFFER:
        log_tail = "\n".join(list(LOG_STREAM_BUFFER)[-35:])
    else:
        log_tail = ""
        logs_dir = target_dir / "logs"
        if logs_dir.is_dir():
            log_files = list(logs_dir.glob("*.log"))
            if log_files:
                try:
                    lines = log_files[0].read_text(encoding="utf-8").splitlines()
                    log_tail = "\n".join(lines[-35:])
                except Exception:
                    pass

    ep_card = f"**{total_eps}**"
    r_card = f"**{best_r:.1f}** (Ep {best_ep})" if best_r > 0 else "**0.0**"
    help_card = f"**{latest_helped:.1f}**"
    eta_card = "**ACTIVE**" if is_running else "**FINISHED / IDLE**"

    return fig1, fig2, fig3, fig4, ep_card, r_card, help_card, eta_card, log_tail, is_running


def launch_simulation(selected_ckpt: str, selected_prev_run: str, env_mode_choice: str = "solo") -> str:
    """Launch the interactive Godot 3D simulation with the chosen checkpoint."""
    ckpt_path: Optional[Path] = None
    if selected_ckpt and Path(selected_ckpt).is_file():
        ckpt_path = Path(selected_ckpt)
    else:
        target_dir = CURRENT_RUN_DIR
        if target_dir is None and selected_prev_run:
            target_dir = Path(selected_prev_run)
        if target_dir is not None and target_dir.is_dir():
            ckpts = find_checkpoints_for_run(str(target_dir))
            if ckpts:
                ckpt_path = Path(ckpts[0][1])

    if ckpt_path is None or not ckpt_path.is_file():
        return "❌ Please select a valid checkpoint (.pt) file to launch."

    launcher_py = REPO_ROOT / "run_simulation.py"
    cmd = [
        str(PYTHON_EXE),
        str(launcher_py),
        "--controller", "rl",
        "--rl-checkpoint", str(ckpt_path),
    ]
    if "solo" in str(env_mode_choice).lower():
        cmd.append("--solo-patient")

    try:
        subprocess.Popen(cmd, cwd=str(REPO_ROOT))
        return f"🎮 Launching Godot 3D Simulation with save:\n{ckpt_path.name}\nPath: {ckpt_path}"
    except Exception as e:
        return f"❌ Failed to launch simulation: {e}"


DASHBOARD_CSS = """
/* High-Contrast Modern Dashboard Styles */
.kpi-box {
    text-align: center !important;
    background: #0f172a !important;
    border-radius: 12px !important;
    padding: 14px 10px !important;
    border: 1px solid #334155 !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4) !important;
}

.kpi-title {
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: #94a3b8 !important;
    font-weight: 700 !important;
    margin-bottom: 6px !important;
}

.kpi-val, .kpi-val *, .kpi-val p, .kpi-val strong, .kpi-val span, .kpi-val div {
    font-size: 22px !important;
    font-weight: 800 !important;
    color: #38bdf8 !important;
    text-align: center !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}

/* Ensure inputs, sliders, and numbers are crystal clear in both dark & light themes */
input[type="number"], .gr-slider-input input, .dark input, .dark textarea, .dark select {
    color: #38bdf8 !important;
    background-color: #1e293b !important;
    border-color: #475569 !important;
    font-weight: 700 !important;
}

/* High contrast numbers for sliders */
.gr-slider-input input {
    color: #38bdf8 !important;
    font-size: 15px !important;
    font-weight: 800 !important;
}

/* Code console high contrast */
.dark code, .dark pre, .dark .code-wrap {
    color: #e2e8f0 !important;
    background-color: #0b0f19 !important;
}
"""


def build_dashboard() -> gr.Blocks:
    """Construct the Gradio Dashboard interface."""
    initial_runs = find_existing_runs()
    default_run = initial_runs[0][1] if initial_runs else ""
    initial_ckpts = find_checkpoints_for_run(default_run) if default_run else []
    default_ckpt = initial_ckpts[0][1] if initial_ckpts else ""

    with gr.Blocks(title="Hospital Robot RL Training Controller") as demo:
        gr.HTML(f"<style>{DASHBOARD_CSS}</style>")
        gr.Markdown(
            """
            # 🏥 Hospital Helper Robot — RL Training & Telemetry Dashboard
            **Interactive control, real-time telemetry streaming, run resumption, and Godot 3D visualization.**
            """
        )

        with gr.Row():
            # LEFT COLUMN: Configuration & Controls
            with gr.Column(scale=4):
                gr.Markdown("### ⚙️ Training Setup & Flags")

                mode_radio = gr.Radio(
                    choices=["Start New Run", "Continue from Previous Run"],
                    value="Start New Run",
                    label="Operation Mode",
                )

                run_dropdown = gr.Dropdown(
                    choices=[(label, path) for label, path in initial_runs],
                    value=default_run,
                    label="Select Previous Run",
                    visible=False,
                    interactive=True,
                )

                run_name_input = gr.Textbox(
                    value="PPOHospital-interactive",
                    label="Run Name / Identifier",
                    placeholder="e.g. PPOHospital-80ep",
                )

                with gr.Row():
                    epochs_slider = gr.Slider(minimum=5, maximum=150, value=60, step=5, label="Total Epochs")
                    steps_slider = gr.Slider(minimum=200, maximum=2000, value=800, step=50, label="Steps / Epoch")

                with gr.Row():
                    patience_slider = gr.Slider(minimum=5, maximum=50, value=25, step=1, label="Early Stop Patience")
                    val_ep_slider = gr.Slider(minimum=1, maximum=5, value=2, step=1, label="Val Shifts / Epoch")

                with gr.Row():
                    seed_input = gr.Number(value=42, label="Random Seed", precision=0)
                    stage_dropdown = gr.Dropdown(
                        choices=["Auto (Stage 1 -> Stage 2)", "Stage 1 only", "Stage 2 only"],
                        value="Auto (Stage 1 -> Stage 2)",
                        label="Curriculum Stage",
                    )
                    env_mode_dropdown = gr.Dropdown(
                        choices=[
                            "Solo Patient Focus (1 Patient, Nearby Spawn)",
                            "Full Hospital Shift (Multi-NPC, Patrolling Doctor)",
                        ],
                        value="Solo Patient Focus (1 Patient, Nearby Spawn)",
                        label="🏥 Environment Mode",
                    )

                gr.Markdown("#### 🚩 Operational Flags")
                with gr.Row():
                    use_cuda_cb = gr.Checkbox(value=True, label="CUDA GPU (--device cuda)")
                    force_resume_cb = gr.Checkbox(value=False, label="Rewind to Best Checkpoint (--force-resume)", visible=False)

                with gr.Row():
                    enable_tb_cb = gr.Checkbox(value=False, label="TensorBoard (--tb)")
                    smoke_cb = gr.Checkbox(value=False, label="Fast Smoke Test (--smoke)")

                with gr.Row():
                    start_btn = gr.Button("🚀 Start / Resume Training", variant="primary", scale=2)
                    stop_btn = gr.Button("⏹️ Stop Training", variant="stop", scale=1)

                with gr.Row():
                    refresh_runs_btn = gr.Button("🔄 Refresh Runs", variant="secondary")

                gr.Markdown("#### 🎮 Godot 3D Inference with Chosen Save")
                ckpt_dropdown = gr.Dropdown(
                    choices=[(l, p) for l, p in initial_ckpts],
                    value=default_ckpt,
                    label="🎯 Select Save / Checkpoint for Godot Inference",
                    interactive=True,
                )
                launch_sim_btn = gr.Button("🎮 Launch 3D Simulation with Selected Save", variant="secondary")

                action_output = gr.Textbox(label="Action & Process Status", interactive=False, max_lines=4)

            # RIGHT COLUMN: Live KPIs, Charts & Logs
            with gr.Column(scale=6):
                gr.Markdown("### 📊 Live Telemetry & Historical Metrics")

                with gr.Row():
                    with gr.Column(elem_classes=["kpi-box"], min_width=120):
                        gr.HTML("<div class='kpi-title'>Epochs Completed</div>")
                        kpi_epoch = gr.Markdown("**0**", elem_classes=["kpi-val"])
                    with gr.Column(elem_classes=["kpi-box"], min_width=120):
                        gr.HTML("<div class='kpi-title'>Best Val R_team</div>")
                        kpi_r = gr.Markdown("**0.0**", elem_classes=["kpi-val"])
                    with gr.Column(elem_classes=["kpi-box"], min_width=120):
                        gr.HTML("<div class='kpi-title'>Patients Helped / Shift</div>")
                        kpi_help = gr.Markdown("**0.0**", elem_classes=["kpi-val"])
                    with gr.Column(elem_classes=["kpi-box"], min_width=120):
                        gr.HTML("<div class='kpi-title'>Status / ETA</div>")
                        kpi_eta = gr.Markdown("**IDLE**", elem_classes=["kpi-val"])

                with gr.Row():
                    plot_reward = gr.Plot(label="Reward Dynamics")
                    plot_loss = gr.Plot(label="PPO Loss")

                with gr.Row():
                    plot_prod = gr.Plot(label="Patients Helped per Shift")
                    plot_safety = gr.Plot(label="Obstacle Collisions")

                gr.Markdown("#### 📜 Live Terminal Output Console")
                log_console = gr.Code(label="Console Log Stream", language="shell", interactive=False, lines=10)

        # Polling Timer: ticks every 2.0s
        timer = gr.Timer(value=2.0, active=True)

        # Mode toggle interactions
        def on_mode_change(m: str):
            is_continue = m == "Continue from Previous Run"
            if is_continue:
                runs = find_existing_runs()
                d_run = runs[0][1] if runs else ""
                fig1, fig2, fig3, fig4, ep, r, help_cnt, eta, status, ckpt_upd = inspect_run(d_run)
                return (
                    gr.update(choices=[(l, p) for l, p in runs], value=d_run, visible=True),
                    gr.update(visible=False),
                    gr.update(visible=True),
                    fig1, fig2, fig3, fig4, ep, r, help_cnt, eta, status, ckpt_upd,
                )
            else:
                return (
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(), gr.update(),
                )

        mode_radio.change(
            on_mode_change,
            inputs=[mode_radio],
            outputs=[
                run_dropdown, run_name_input, force_resume_cb,
                plot_reward, plot_loss, plot_prod, plot_safety,
                kpi_epoch, kpi_r, kpi_help, kpi_eta,
                action_output, ckpt_dropdown,
            ],
        )

        # Inspect selected run
        run_dropdown.change(
            inspect_run,
            inputs=[run_dropdown],
            outputs=[plot_reward, plot_loss, plot_prod, plot_safety, kpi_epoch, kpi_r, kpi_help, kpi_eta, action_output, ckpt_dropdown],
        )

        # Start button
        start_btn.click(
            start_training,
            inputs=[
                mode_radio, run_dropdown, run_name_input,
                epochs_slider, steps_slider, patience_slider, val_ep_slider,
                seed_input, stage_dropdown, env_mode_dropdown, use_cuda_cb, force_resume_cb,
                enable_tb_cb, smoke_cb,
            ],
            outputs=[action_output, timer, log_console],
        )

        # Stop button
        stop_btn.click(
            stop_training,
            inputs=[],
            outputs=[action_output],
        )

        # Launch simulation button
        launch_sim_btn.click(
            launch_simulation,
            inputs=[ckpt_dropdown, run_dropdown, env_mode_dropdown],
            outputs=[action_output],
        )

        # Refresh runs list button
        def on_refresh_runs():
            runs = find_existing_runs()
            val = runs[0][1] if runs else ""
            ckpts = find_checkpoints_for_run(val) if val else []
            d_ckpt = ckpts[0][1] if ckpts else ""
            return gr.update(choices=[(l, p) for l, p in runs], value=val), gr.update(choices=[(l, p) for l, p in ckpts], value=d_ckpt)

        refresh_runs_btn.click(
            on_refresh_runs,
            inputs=[],
            outputs=[run_dropdown, ckpt_dropdown],
        )

        # Periodic timer poll
        timer.tick(
            poll_status_and_metrics,
            inputs=[run_dropdown],
            outputs=[
                plot_reward, plot_loss, plot_prod, plot_safety,
                kpi_epoch, kpi_r, kpi_help, kpi_eta,
                log_console, timer,
            ],
        )

    return demo


def main():
    parser = argparse.ArgumentParser(description="Launch Hospital Helper Robot RL Training Dashboard.")
    parser.add_argument("--port", type=int, default=7860, help="Web server port")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface")
    parser.add_argument("--share", action="store_true", help="Create a public Gradio share link")
    args = parser.parse_args()

    demo = build_dashboard()
    print(f"Starting Hospital RL Dashboard at http://{args.host}:{args.port}")
    demo.launch(server_name=args.host, server_port=args.port, share=args.share, css=DASHBOARD_CSS)


if __name__ == "__main__":
    main()
