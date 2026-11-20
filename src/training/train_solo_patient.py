"""Dedicated PPO Training Script for Solo Patient Hospital Environment.

Trains robot to explore hospital corridors, find patients, engage them,
and escort them to destinations with early stagnation cutoff and strict
collision penalties. Supports training from scratch or warm-started weights.

Usage:
    python -m src.training.train_solo_patient --episodes 30000 --no-warmstart
    python -m src.training.train_solo_patient --episodes 100000 --no-warmstart --device cuda   # NVIDIA
    python -m src.training.train_solo_patient --episodes 100000 --no-warmstart --device cpu    # Apple Silicon
    python -m src.training.train_solo_patient --episodes 5000
    python -m src.training.train_solo_patient --resume-from experiments/runs/<run_dir> --episodes 30000
    python -m src.training.train_solo_patient --warmstart <old_run>/checkpoints/PPOHospital-solo_last.pt \
        --episodes 15000 --no-bc --eval-every 500 --patience 8 --device cpu
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn

from src.models.ppo_agent import ACT_DIM, OBS_DIM, PPOHospitalAgent
from src.training.hospital_env import HospitalShiftEnv
from src.utils.checkpoint_utils import capture_rng_state, get_git_commit, seed_everything


DEFAULT_WARMSTART_PATH = (
    "experiments/runs/20261023_162628_PPOHospital-converged-80ep-full/checkpoints/PPOHospital-converged-80ep-full_best.pt"
)


def format_eta(seconds: float) -> str:
    """Format seconds into human-readable MM:SS or HH:MM:SS."""
    if seconds < 0 or not np.isfinite(seconds):
        return "--:--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h{m:02d}m"
    return f"{m:02d}m{s:02d}s"


def resolve_device(device_name: str) -> torch.device:
    """Resolve --device into a torch.device.

    auto picks cuda if available, else cpu. MPS is opt-in only: for this small MLP it
    benchmarked ~1.8x slower than CPU on an M4.
    """
    mps_ok = torch.backends.mps.is_available()
    if device_name == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("--device cuda requested but no CUDA device is available.")
        return torch.device("cuda")
    if device_name == "mps":
        if not mps_ok:
            raise RuntimeError("--device mps requested but Apple MPS is not available.")
        return torch.device("mps")
    if device_name == "cpu":
        return torch.device("cpu")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def describe_device(device: torch.device) -> str:
    if device.type == "cuda":
        return torch.cuda.get_device_name(0)
    if device.type == "mps":
        return "Apple Silicon GPU (MPS)"
    return "CPU"


EVAL_SEED_BASE = 900_000_000  # held-out seeds, never used by training episodes (seed + ep * 79)
EVAL_COLLISION_WEIGHT = 1.0   # eval score = mean R_team - weight * mean collisions


def evaluate_policy(
    agent: PPOHospitalAgent,
    n_episodes: int,
    stagnation_timeout_s: float,
    stagnation_penalty: float,
    shift_duration_s: float,
    env_mode: str = "solo",
) -> dict[str, float]:
    """Deterministic (mean action) rollouts on fixed held-out seeds; same seeds every call."""
    r_team, tasks, cols, stag = [], [], [], 0
    for i in range(n_episodes):
        env = HospitalShiftEnv(
            curriculum_stage=1,
            shift_duration_s=shift_duration_s,
            dt=0.2,
            seed=EVAL_SEED_BASE + i * 7919,
            env_mode=env_mode,
            stagnation_timeout_s=stagnation_timeout_s,
            stagnation_penalty=stagnation_penalty,
        )
        obs = env.reset()
        done = False
        info: dict[str, Any] = {}
        while not done:
            with torch.no_grad():
                action, _, _, _ = agent.get_action_and_value(
                    torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0), deterministic=True
                )
            obs, _, done, info = env.step(action.squeeze(0).numpy())
        r_team.append(float(info.get("cumulative_team_reward", 0.0)))
        tasks.append(int(info.get("patients_helped", 0)))
        cols.append(int(info.get("collisions", 0)))
        stag += info.get("exit_reason") == "STAGNATION_TIMEOUT"
    mean_r, mean_col = float(np.mean(r_team)), float(np.mean(cols))
    return {
        "score": mean_r - EVAL_COLLISION_WEIGHT * mean_col,
        "r_team": mean_r,
        "tasks": float(np.mean(tasks)),
        "collisions": mean_col,
        "stagnation_rate": stag / max(1, n_episodes),
    }


def run_train_solo_patient(
    episodes: int = 30000,
    warmstart_path: str | Path | None = None,
    resume_from: str | Path | None = None,
    stagnation_timeout_s: float = 45.0,
    stagnation_penalty: float = -10.0,
    shift_duration_s: float = 180.0,
    update_freq_episodes: int = 5,
    ppo_epochs: int = 4,
    batch_size: int = 256,
    lr_init: float = 1e-4,
    lr_min: float = 3e-5,
    gamma: float = 0.99,
    gae_lambda: float = 0.95,
    clip_coef: float = 0.2,
    ent_coef: float = 0.01,
    vf_coef: float = 0.5,
    seed: int = 42,
    device_name: str = "auto",
    experiments_root: str | Path = "experiments",
    eval_every: int = 500,
    eval_episodes: int = 20,
    patience: int = 0,
    bc_enabled: bool = True,
    env_mode: str = "solo",
) -> Path:
    seed_everything(seed)

    device = resolve_device(device_name)

    agent = PPOHospitalAgent(obs_dim=OBS_DIM, act_dim=ACT_DIM).to(device)
    # Per-step rollout inference (batch=1) is much faster on CPU than on cuda/mps because
    # every step syncs device->host; the PPO update still runs on `device`.
    rollout_agent = PPOHospitalAgent(obs_dim=OBS_DIM, act_dim=ACT_DIM)
    rollout_agent.eval()

    total_updates = max(1, episodes // update_freq_episodes)
    optimizer = torch.optim.AdamW(agent.parameters(), lr=lr_init, eps=1e-5, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=total_updates, eta_min=lr_min
    )

    rolling_20 = collections.deque(maxlen=20)
    best_roll20 = -float("inf")
    peak_r_team = -float("inf")
    start_ep = 1
    warmstart_loaded = False
    best_eval = -float("inf")
    evals_without_improve = 0
    ckpt_prefix = f"PPOHospital-{env_mode}"

    if resume_from:
        r_path = Path(resume_from)
        if r_path.is_file():
            ckpt_file = r_path
            run_dir = r_path.parent.parent
        else:
            run_dir = r_path
            candidates = [f"PPOHospital-{env_mode}_last.pt", "PPOHospital-solo_last.pt", "PPOHospital-solo-1000ep_last.pt",
                          f"PPOHospital-{env_mode}_best.pt", "PPOHospital-solo_best.pt", "PPOHospital-solo-1000ep_best.pt"]
            ckpt_file = next(
                (run_dir / "checkpoints" / c for c in candidates if (run_dir / "checkpoints" / c).exists()),
                run_dir / "checkpoints" / candidates[0],
            )

        ckpt = torch.load(ckpt_file, map_location=device, weights_only=True)
        agent.load_state_dict(ckpt["model_state_dict"])
        if "optimizer_state_dict" in ckpt:
            try:
                optimizer.load_state_dict(ckpt["optimizer_state_dict"])
            except Exception:
                pass

        start_ep = int(ckpt.get("episode", 0)) + 1
        best_roll20 = float(ckpt.get("best_roll20", -float("inf")))
        best_eval = float(ckpt.get("best_eval_score", -float("inf")))
        peak_r_team = float(ckpt.get("peak_r_team", -float("inf")))
        ckpt_dir = run_dir / "checkpoints"
        metrics_file = run_dir / "metrics.jsonl"

        remaining_updates = max(1, (episodes - start_ep + 1) // update_freq_episodes)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=remaining_updates, eta_min=lr_min
        )

        if metrics_file.exists():
            with metrics_file.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if "r_team" in data:
                            rolling_20.append(float(data["r_team"]))
                    except Exception:
                        pass
        print(f" Resumed Training    : Continuing from Ep {start_ep} (Best Roll20: {best_roll20:+.1f}, Peak: {peak_r_team:+.1f}) in {run_dir.name}", flush=True)
    else:
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(experiments_root) / "runs" / f"{timestamp}_PPOHospital-{env_mode}-patient"
        ckpt_dir = run_dir / "checkpoints"
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        metrics_file = run_dir / "metrics.jsonl"

        if warmstart_path:
            w_path = Path(warmstart_path)
            if w_path.exists():
                checkpoint = torch.load(w_path, map_location=device, weights_only=True)
                if "model_state_dict" in checkpoint:
                    agent.load_state_dict(checkpoint["model_state_dict"])
                else:
                    agent.load_state_dict(checkpoint)
                warmstart_loaded = True
                print(f" Warm-start Weights  : Loaded successfully from {w_path.name} (Val R_team: {checkpoint.get('best_val_acc', 'N/A')})", flush=True)
            else:
                print(f" Warm-start Warning  : File not found at {w_path}. Starting from scratch.", flush=True)
        else:
            print(" Training Mode       : From Scratch (Random initialization)", flush=True)

    print("=" * 86, flush=True)
    print(f" PPO SOLO PATIENT TRAINING -- {episodes} EPISODES (Start Ep: {start_ep})", flush=True)
    print(f" Output Directory    : {run_dir}", flush=True)
    print(f" Compute Device      : {device} ({describe_device(device)}) | Rollout: cpu", flush=True)
    print(f" Stagnation Timeout  : {stagnation_timeout_s:.1f}s ({int(stagnation_timeout_s / 0.2)} steps) | Penalty: {stagnation_penalty:+.1f}", flush=True)
    print(f" PPO Batch Update    : Every {update_freq_episodes} episodes | PPO Epochs: {ppo_epochs} | Batch: {batch_size}", flush=True)
    print(f" Learning Rate       : {lr_init:.1e} -> {lr_min:.1e} (Cosine Annealing)", flush=True)
    print(f" Env Mode            : {env_mode} ({'scene NPCs as live obstacles' if env_mode == 'full' else 'single patient, no crowd'})", flush=True)

    # Buffers across update_freq_episodes
    batch_obs: list[np.ndarray] = []
    batch_act: list[np.ndarray] = []
    batch_teacher: list[np.ndarray] = []
    batch_logp: list[float] = []
    batch_adv: list[np.ndarray] = []
    batch_ret: list[np.ndarray] = []

    total_helped = 0
    total_collisions = 0
    stagnation_timeouts = 0
    completed_shifts = 0

    run_config = {
        "episodes": episodes,
        "warmstart_path": str(warmstart_path) if warmstart_path else None,
        "warmstart_loaded": warmstart_loaded,
        "stagnation_timeout_s": stagnation_timeout_s,
        "stagnation_penalty": stagnation_penalty,
        "shift_duration_s": shift_duration_s,
        "update_freq_episodes": update_freq_episodes,
        "ppo_epochs": ppo_epochs,
        "batch_size": batch_size,
        "lr_init": lr_init,
        "lr_min": lr_min,
        "gamma": gamma,
        "gae_lambda": gae_lambda,
        "clip_coef": clip_coef,
        "seed": seed,
        "device": str(device),
        "eval_every": eval_every,
        "eval_episodes": eval_episodes,
        "eval_collision_weight": EVAL_COLLISION_WEIGHT,
        "patience": patience,
        "bc_enabled": bc_enabled,
        "env_mode": env_mode,
    }

    print("-" * 86, flush=True)
    print("EPISODE LOGS (Real-time single-line flush):", flush=True)
    print("-" * 86, flush=True)

    rollout_agent.load_state_dict(agent.state_dict())
    ep_width = len(str(episodes))

    t_start = time.time()
    completed_in_run = 0

    for ep in range(start_ep, episodes + 1):
        # Teacher guidance weight: if warm-start decaying over 200 eps; if scratch decaying over 500 eps
        max_bc_eps = 200.0 if warmstart_loaded else 500.0
        bc_weight = max(0.0, 0.15 * (1.0 - (ep - 1) / max_bc_eps)) if bc_enabled else 0.0

        env = HospitalShiftEnv(
            curriculum_stage=1,
            shift_duration_s=shift_duration_s,
            dt=0.2,
            seed=seed + ep * 79,
            env_mode=env_mode,
            stagnation_timeout_s=stagnation_timeout_s,
            stagnation_penalty=stagnation_penalty,
        )
        obs = env.reset()

        ep_obs: list[np.ndarray] = []
        ep_act: list[np.ndarray] = []
        ep_teacher: list[np.ndarray] = []
        ep_logp: list[float] = []
        ep_val: list[float] = []
        ep_rew: list[float] = []

        done = False
        info: dict[str, Any] = {}

        while not done:
            teacher_act = env.teacher_action()
            obs_t = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                action_t, logp_t, _, val_t = rollout_agent.get_action_and_value(obs_t)

            policy_act = action_t.squeeze(0).numpy()
            exec_act = np.clip((1.0 - bc_weight) * policy_act + bc_weight * teacher_act, -1.0, 1.0)

            ep_obs.append(obs)
            ep_act.append(policy_act)
            ep_teacher.append(teacher_act)
            ep_logp.append(float(logp_t.item()))
            ep_val.append(float(val_t.item()))

            next_obs, reward, done, info = env.step(exec_act)
            ep_rew.append(float(reward))
            obs = next_obs

        # Calculate exact GAE for finished episode
        ep_len = len(ep_rew)
        ep_adv = np.zeros(ep_len, dtype=np.float32)
        lastgaelam = 0.0
        for t in reversed(range(ep_len)):
            nextnonterminal = 0.0 if t == ep_len - 1 else 1.0
            nextval = 0.0 if t == ep_len - 1 else ep_val[t + 1]
            delta = ep_rew[t] + gamma * nextval * nextnonterminal - ep_val[t]
            lastgaelam = delta + gamma * gae_lambda * nextnonterminal * lastgaelam
            ep_adv[t] = lastgaelam
        ep_ret = ep_adv + np.asarray(ep_val, dtype=np.float32)

        batch_obs.extend(ep_obs)
        batch_act.extend(ep_act)
        batch_teacher.extend(ep_teacher)
        batch_logp.extend(ep_logp)
        batch_adv.append(ep_adv)
        batch_ret.append(ep_ret)

        # Episode Metrics
        r_team = float(info.get("cumulative_team_reward", 0.0))
        tasks = int(info.get("patients_helped", 0))
        collisions = int(info.get("collisions", 0))
        exit_reason = str(info.get("exit_reason", "UNKNOWN"))
        steps = int(env.step_count)
        duration_s = steps * 0.2

        rolling_20.append(r_team)
        roll20_mean = float(np.mean(rolling_20))
        if r_team > peak_r_team:
            peak_r_team = r_team

        total_helped += tasks
        total_collisions += collisions
        if exit_reason == "STAGNATION_TIMEOUT":
            stagnation_timeouts += 1
        elif exit_reason == "COMPLETED":
            completed_shifts += 1

        completed_in_run += 1
        elapsed = time.time() - t_start
        rate_eps = completed_in_run / max(1e-5, elapsed)
        eta_s = (episodes - ep) / max(1e-5, rate_eps)
        eta_str = format_eta(eta_s)

        # Real-time single line flush to terminal
        print(
            f"[EP {ep:0{ep_width}d}/{episodes}] Tasks: {tasks:2d} | "
            f"R_team: {r_team:+6.1f} | "
            f"Dur: {duration_s:5.1f}s ({steps:3d} stp) | "
            f"Exit: {exit_reason:<18} | "
            f"Col: {collisions:2d} | "
            f"Roll20: {roll20_mean:+6.1f} | "
            f"Peak: {peak_r_team:+6.1f} | "
            f"ETA: {eta_str}",
            flush=True,
        )

        # Append to metrics.jsonl
        log_entry = {
            "episode": ep,
            "r_team": r_team,
            "tasks_helped": tasks,
            "duration_s": round(duration_s, 2),
            "steps": steps,
            "exit_reason": exit_reason,
            "collisions": collisions,
            "roll20_r_team": round(roll20_mean, 2),
            "peak_r_team": round(peak_r_team, 2),
            "lr": float(optimizer.param_groups[0]["lr"]),
            "elapsed_s": round(elapsed, 2),
            "timestamp": dt.datetime.now().isoformat(),
        }
        with metrics_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        # PPO Batch Update Every update_freq_episodes
        if (ep % update_freq_episodes == 0) or (ep == episodes):
            b_obs_arr = np.asarray(batch_obs, dtype=np.float32)
            b_act_arr = np.asarray(batch_act, dtype=np.float32)
            b_teach_arr = np.asarray(batch_teacher, dtype=np.float32)
            b_logp_arr = np.asarray(batch_logp, dtype=np.float32)
            b_adv_arr = np.concatenate(batch_adv).astype(np.float32)
            b_ret_arr = np.concatenate(batch_ret).astype(np.float32)

            t_obs = torch.as_tensor(b_obs_arr, dtype=torch.float32, device=device)
            t_act = torch.as_tensor(b_act_arr, dtype=torch.float32, device=device)
            t_teach = torch.as_tensor(b_teach_arr, dtype=torch.float32, device=device)
            t_logp = torch.as_tensor(b_logp_arr, dtype=torch.float32, device=device)
            t_adv = torch.as_tensor(b_adv_arr, dtype=torch.float32, device=device)
            t_ret = torch.as_tensor(b_ret_arr, dtype=torch.float32, device=device)

            # Safely normalize advantages across whole batch
            adv_std = t_adv.std(unbiased=False)
            if adv_std > 1e-6:
                t_adv = (t_adv - t_adv.mean()) / (adv_std + 1e-8)

            n_samples = len(b_obs_arr)
            b_inds = np.arange(n_samples)

            for _ in range(ppo_epochs):
                np.random.shuffle(b_inds)
                for start in range(0, n_samples, batch_size):
                    end = min(start + batch_size, n_samples)
                    if end - start < 8:
                        continue
                    mb_idx = b_inds[start:end]

                    _, newlogprob, entropy, newval = agent.get_action_and_value(
                        t_obs[mb_idx], t_act[mb_idx]
                    )
                    ratio = (newlogprob - t_logp[mb_idx]).exp()

                    mb_adv = t_adv[mb_idx]

                    pg_loss1 = -mb_adv * ratio
                    pg_loss2 = -mb_adv * torch.clamp(ratio, 1.0 - clip_coef, 1.0 + clip_coef)
                    pg_loss = torch.max(pg_loss1, pg_loss2).mean()

                    v_loss = 0.5 * ((newval - t_ret[mb_idx]) ** 2).mean()
                    ent_loss = entropy.mean()

                    # Auxiliary teacher imitation loss
                    pred_mean = torch.tanh(agent.actor_mean(agent.actor_backbone(t_obs[mb_idx])))
                    bc_loss = ((pred_mean - t_teach[mb_idx]) ** 2).mean()

                    loss = pg_loss - ent_coef * ent_loss + vf_coef * v_loss + 0.2 * bc_weight * bc_loss

                    optimizer.zero_grad()
                    if not torch.isnan(loss) and not torch.isinf(loss):
                        loss.backward()
                        nn.utils.clip_grad_norm_(agent.parameters(), 0.5)
                        has_nan_grad = any(
                            p.grad is not None and (torch.isnan(p.grad).any() or torch.isinf(p.grad).any())
                            for p in agent.parameters()
                        )
                        if not has_nan_grad:
                            optimizer.step()
                        else:
                            optimizer.zero_grad()

            scheduler.step()
            rollout_agent.load_state_dict(agent.state_dict())

            # Clear rollout buffer
            batch_obs.clear()
            batch_act.clear()
            batch_teacher.clear()
            batch_logp.clear()
            batch_adv.clear()
            batch_ret.clear()

        if len(rolling_20) >= min(20, episodes):
            best_roll20 = max(best_roll20, roll20_mean)

        def checkpoint_payload() -> dict[str, Any]:
            return {
                "model_state_dict": agent.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "episode": ep,
                "best_roll20": best_roll20,
                "best_eval_score": best_eval,
                "peak_r_team": peak_r_team,
                "config": run_config,
                "rng": capture_rng_state(seed),
                "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                "commit": get_git_commit(),
            }

        # Periodic deterministic evaluation on held-out seeds -> best checkpoint + early stopping
        stop_early = False
        if eval_every > 0 and (ep % eval_every == 0 or ep == episodes):
            ev = evaluate_policy(
                rollout_agent, eval_episodes, stagnation_timeout_s, stagnation_penalty, shift_duration_s, env_mode
            )
            improved = ev["score"] > best_eval
            if improved:
                best_eval = ev["score"]
                evals_without_improve = 0
                torch.save(checkpoint_payload(), ckpt_dir / f"{ckpt_prefix}_best.pt")
            else:
                evals_without_improve += 1
            print(
                f"[EVAL @ {ep}] score {ev['score']:+7.1f} | R_team {ev['r_team']:+7.1f} | tasks {ev['tasks']:.2f} | "
                f"col {ev['collisions']:5.1f} | stag {ev['stagnation_rate']:.0%} | "
                f"{'NEW BEST' if improved else f'no improve x{evals_without_improve}'}",
                flush=True,
            )
            with (run_dir / "eval.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"episode": ep, **ev, "best_score": best_eval}) + "\n")
            stop_early = patience > 0 and evals_without_improve >= patience

        # Periodic Last Checkpoint (every 50-100 episodes or end)
        save_freq = 50 if episodes <= 1000 else 100
        if (ep % save_freq == 0) or (ep == episodes) or stop_early:
            torch.save(checkpoint_payload(), ckpt_dir / f"{ckpt_prefix}_last.pt")

        if stop_early:
            print(f" Early stop          : no eval improvement in {patience} evals (best score {best_eval:+.1f})", flush=True)
            break

    t_total = time.time() - t_start
    print("-" * 86, flush=True)
    print("TRAINING RUN COMPLETE SUMMARY:", flush=True)
    print(f" Total Episodes Run   : {completed_in_run} (Final Ep: {episodes})", flush=True)
    print(f" Total Elapsed Time   : {format_eta(t_total)} ({t_total:.1f}s)", flush=True)
    print(f" Total Patients Helped: {total_helped}", flush=True)
    print(f" Total Collisions     : {total_collisions}", flush=True)
    print(f" Completed Shifts     : {completed_shifts}", flush=True)
    print(f" Stagnation Timeouts  : {stagnation_timeouts}", flush=True)
    print(f" Best Rolling-20      : {best_roll20:+.2f}", flush=True)
    print(f" Best Eval Score      : {best_eval:+.2f} (R_team - {EVAL_COLLISION_WEIGHT:g} x collisions, deterministic)", flush=True)
    print(f" Peak R_team Achieved : {peak_r_team:+.2f}", flush=True)
    print(f" Best Checkpoint Saved: {ckpt_dir / f'{ckpt_prefix}_best.pt'}", flush=True)
    print("=" * 86, flush=True)

    # Write summary README.md
    readme_content = f"""# Run Summary: Solo Patient PPO Training

- **Run Directory**: `{run_dir}`
- **Date**: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Warm-start**: {warmstart_path if warmstart_path else 'None (From Scratch)'}
- **Episodes**: {episodes}
- **Stagnation Timeout**: {stagnation_timeout_s}s ({int(stagnation_timeout_s / 0.2)} steps)
- **Stagnation Penalty**: {stagnation_penalty:+.1f}
- **Best Rolling-20 $R_{{team}}$**: {best_roll20:+.2f}
- **Best Eval Score** (deterministic, {eval_episodes} held-out seeds, R_team - {EVAL_COLLISION_WEIGHT:g} x collisions): {best_eval:+.2f}
- **Peak Episode $R_{{team}}$**: {peak_r_team:+.2f}
- **Best Checkpoint**: `checkpoints/{ckpt_prefix}_best.pt`
"""
    (run_dir / "README.md").write_text(readme_content, encoding="utf-8")
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="PPO Solo Patient Training")
    parser.add_argument("--episodes", type=int, default=30000, help="Number of episodes to train (default: 30000)")
    parser.add_argument("--warmstart", type=str, default=None, help="Path to warm-start checkpoint (default: None)")
    parser.add_argument("--no-warmstart", action="store_true", help="Explicitly train from scratch without warm-start")
    parser.add_argument("--resume-from", type=str, default=None, help="Path to checkpoint or run directory to resume")
    parser.add_argument("--stagnation-timeout", type=float, default=45.0, help="Stagnation timeout in seconds (default: 45.0)")
    parser.add_argument("--stagnation-penalty", type=float, default=-10.0, help="Stagnation terminal penalty (default: -10.0)")
    parser.add_argument("--shift-duration", type=float, default=180.0, help="Max shift duration in seconds (default: 180.0)")
    parser.add_argument("--update-freq", type=int, default=5, help="PPO update frequency in episodes (default: 5)")
    parser.add_argument("--ppo-epochs", type=int, default=4, help="PPO epochs per update (default: 4)")
    parser.add_argument("--batch-size", type=int, default=256, help="Minibatch size for PPO update (default: 256)")
    parser.add_argument("--lr", type=float, default=1e-4, help="Initial learning rate (default: 1e-4)")
    parser.add_argument("--min-lr", type=float, default=3e-5, help="Min learning rate for cosine schedule (default: 3e-5)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cuda", "mps", "cpu"], help="Device for PPO updates (auto: cuda, else cpu); rollout always on CPU")
    parser.add_argument("--eval-every", type=int, default=500, help="Deterministic eval every N episodes; picks best.pt (0 = off)")
    parser.add_argument("--eval-episodes", type=int, default=20, help="Held-out episodes per eval (default: 20)")
    parser.add_argument("--patience", type=int, default=0, help="Stop after N evals without improvement (0 = never)")
    parser.add_argument("--no-bc", action="store_true", help="Disable early teacher imitation (useful when warm-starting)")
    parser.add_argument("--env-mode", choices=["solo", "full"], default="solo",
                        help="solo: 1 patient only; full: + scene NPCs (seated patients, nurse, patrolling doctor)")
    parser.add_argument("--smoke", action="store_true", help="Smoke test (10 episodes, update freq 2)")

    args = parser.parse_args()

    warmstart = None if args.no_warmstart else args.warmstart
    episodes = 10 if args.smoke else args.episodes
    update_freq = 2 if args.smoke else args.update_freq

    run_train_solo_patient(
        episodes=episodes,
        warmstart_path=warmstart,
        resume_from=args.resume_from,
        stagnation_timeout_s=args.stagnation_timeout,
        stagnation_penalty=args.stagnation_penalty,
        shift_duration_s=args.shift_duration,
        update_freq_episodes=update_freq,
        ppo_epochs=args.ppo_epochs,
        batch_size=args.batch_size,
        lr_init=args.lr,
        lr_min=args.min_lr,
        seed=args.seed,
        device_name=args.device,
        eval_every=5 if args.smoke else args.eval_every,
        eval_episodes=2 if args.smoke else args.eval_episodes,
        patience=args.patience,
        bc_enabled=not args.no_bc,
        env_mode=args.env_mode,
    )


if __name__ == "__main__":
    main()
