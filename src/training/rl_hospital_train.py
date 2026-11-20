"""Deliverable PPO RL training script for the Hospital Helper Robot.

Usage:
  python -m src.training.rl_hospital_train --smoke
  python -m src.training.rl_hospital_train --epochs 30 --seed 42
  python -m src.training.rl_hospital_train --resume
  python -m src.training.rl_hospital_train --force-resume

Complies strictly with `agents/rules/LOGGING_CHECKPOINT_RULES.md`.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn

from src.models.ppo_agent import ACT_DIM, OBS_DIM, PPOHospitalAgent
from src.training.hospital_env import HospitalShiftEnv
from src.utils.checkpoint_utils import load_checkpoint, save_checkpoint, seed_everything
from src.utils.run_logger import RunLogger, sanitize_run_name


def evaluate_policy(
    agent: PPOHospitalAgent,
    stage: int,
    n_episodes: int,
    shift_duration_s: float,
    seed: int,
    device: torch.device,
    env_mode: str = "solo",
) -> dict[str, float]:
    """Evaluate policy deterministically over `n_episodes` hospital shifts."""
    agent.eval()
    r_teams: list[float] = []
    returns: list[float] = []
    helped_counts: list[int] = []
    collision_counts: list[int] = []

    for ep in range(n_episodes):
        env = HospitalShiftEnv(
            curriculum_stage=stage,
            shift_duration_s=shift_duration_s,
            seed=seed + 1000 + ep,
            env_mode=env_mode,
        )
        obs = env.reset()
        done = False
        ep_ret = 0.0
        while not done:
            obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
            with torch.no_grad():
                action_t, _, _, _ = agent.get_action_and_value(obs_t, deterministic=True)
            act_np = action_t.squeeze(0).cpu().numpy()
            obs, r, done, info = env.step(act_np)
            ep_ret += r
        r_teams.append(float(info["cumulative_team_reward"]))
        returns.append(float(ep_ret))
        helped_counts.append(int(info["patients_helped"]))
        collision_counts.append(int(info["collisions"]))

    agent.train()
    return {
        "val_r_team": float(np.mean(r_teams)),
        "val_return": float(np.mean(returns)),
        "val_patients_helped": float(np.mean(helped_counts)),
        "val_collisions": float(np.mean(collision_counts)),
    }


def update_results_readme(
    results_root: Path,
    run_name: str,
    run_dir: Path,
    best_epoch: int,
    best_r_team: float,
    best_helped: float,
) -> None:
    """Update `experiments/results/README.md` with 5W1H context per §2 & §8."""
    readme_path = results_root / "README.md"
    content = f"""# Experiment Results Index (5W1H)

## `rl_hospital/` — Hospital Helper Robot PPO Curriculum Training

- **What**: Consolidated training history (`training_history.json`), compressed rollout metrics (`rollout_summary.npz`), and best policy metadata for the `PPOHospitalAgent` (`31-D -> 2-D`) controller.
- **Why**: Train a single hospital helper robot (with shared team reward `R_team` ready for multi-agent expansion) to search for patients, answer questions (`+10`), call medical staff (`+20`), and physically escort elderly patients (`+30`, `2.5 m` tether) to Floor-1 rooms or the Elevator (`thang_may`).
- **Who**: Generated automatically by `python -m src.training.rl_hospital_train` (run `{run_name}`).
- **Where**: Source run directory `{run_dir.name}` under `experiments/runs/`; consolidated artifacts in `experiments/results/rl_hospital/`.
- **When**: Best checkpoint achieved at Epoch `{best_epoch}` (`val_R_team = {best_r_team:.2f}`, `val_patients_helped = {best_helped:.2f}`).
- **How**: 2-Stage Curriculum PPO + LiDAR-aware behavior cloning warm-up over the 24 m × 18 m Floor-1 hospital layout with 17-ray 2D LiDAR fan (`200°` FOV, `6.0 m` range).
"""
    readme_path.write_text(content, encoding="utf-8")


def train_hospital_rl(
    run_name: str = "PPOHospital-curriculum",
    epochs: int = 20,
    steps_per_epoch: int = 900,
    batch_size: int = 150,
    ppo_epochs: int = 4,
    lr: float = 3e-4,
    gamma: float = 0.99,
    gae_lambda: float = 0.95,
    clip_coef: float = 0.2,
    ent_coef: float = 0.01,
    vf_coef: float = 0.5,
    bc_coef_init: float = 0.6,
    patience: int = 20,
    seed: int = 42,
    stage_override: int = 0,
    val_episodes_override: int = 0,
    resume: bool = False,
    force_resume: bool = False,
    resume_from: str | Path | None = None,
    env_mode: str = "solo",
    device_choice: str = "auto",
    enable_tb: bool = False,
    smoke: bool = False,
    experiments_root: str | Path = "experiments",
) -> dict[str, Any]:
    """Run PPO + 2-Stage Curriculum training with full-state checkpointing."""
    safe_name = sanitize_run_name(run_name)
    if smoke:
        epochs = min(epochs, 3)
        steps_per_epoch = 180
        batch_size = 60

    shift_duration_s = 36.0 if smoke else 180.0
    val_episodes = 2 if smoke else (val_episodes_override if val_episodes_override > 0 else 2)

    existing_run_dir: Path | None = None
    if resume_from is not None:
        p = Path(resume_from).resolve()
        existing_run_dir = p if p.is_dir() else p.parent.parent
    elif resume or force_resume:
        existing_run_dir = RunLogger.resolve_latest_run_dir(safe_name, experiments_root=experiments_root)

    logger = RunLogger(
        run_name=safe_name,
        experiments_root=experiments_root,
        run_dir=existing_run_dir,
        enable_tb=enable_tb,
    )

    if device_choice == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is strictly required (--device cuda) but no CUDA device is available.")
        device = torch.device("cuda")
    elif device_choice == "cpu":
        device = torch.device("cpu")
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'})")
    seed_everything(seed)

    agent = PPOHospitalAgent(obs_dim=OBS_DIM, act_dim=ACT_DIM).to(device)
    optimizer = torch.optim.Adam(agent.parameters(), lr=lr, eps=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(epochs, 1), eta_min=3e-5)

    results_dir = Path(experiments_root).resolve() / "results" / "rl_hospital"
    results_dir.mkdir(parents=True, exist_ok=True)
    declared_outputs = [
        str(logger.best_ckpt_path),
        str(logger.last_ckpt_path),
        str(logger.log_path),
        str(logger.config_path),
        str(logger.history_path),
        str(results_dir / "training_history.json"),
        str(results_dir / "rollout_summary.npz"),
    ]

    config: dict[str, Any] = {
        "run_name": safe_name,
        "epochs": epochs,
        "steps_per_epoch": steps_per_epoch,
        "batch_size": batch_size,
        "ppo_epochs": ppo_epochs,
        "lr": lr,
        "gamma": gamma,
        "gae_lambda": gae_lambda,
        "clip_coef": clip_coef,
        "ent_coef": ent_coef,
        "vf_coef": vf_coef,
        "bc_coef_init": bc_coef_init,
        "patience": patience,
        "seed": seed,
        "env_mode": env_mode,
        "smoke": smoke,
        "shift_duration_s": shift_duration_s,
        "5W1H": {
            "what": "PPO Actor-Critic (31-D -> 2-D) hospital helper robot controller",
            "why": "Maximize shared team reward R_team across 180s multi-patient hospital shifts",
            "who": "src.training.rl_hospital_train",
            "where": str(logger.run_dir),
            "when": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "how": "2-Stage Curriculum PPO + LiDAR/tether-aware teacher warm-up",
        },
        "outputs": declared_outputs,
    }
    logger.save_config(config)

    start_epoch = 1
    global_step = 0
    best_val_loss = float("inf")
    best_val_acc = float("-inf")  # Tracks best val_r_team
    best_epoch = 0
    early_stop_triggered = False
    no_improve_epochs = 0
    history: dict[str, list[Any]] = {
        "train_losses": [],
        "val_losses": [],
        "train_accs": [],
        "val_accs": [],
        "val_patients_helped": [],
        "val_collisions": [],
    }

    if (resume or force_resume or resume_from is not None) and existing_run_dir is not None:
        ckpt_to_load = logger.best_ckpt_path if force_resume else logger.last_ckpt_path
        if ckpt_to_load.exists():
            ckpt = load_checkpoint(
                ckpt_to_load,
                model=agent,
                optimizer=optimizer,
                scheduler=scheduler,
                restore_rng=True,
                map_location=device,
            )
            global_step = int(ckpt.get("global_step", 0))
            best_val_loss = float(ckpt.get("best_val_loss", float("inf")))
            best_val_acc = float(ckpt.get("best_val_acc", float("-inf")))
            best_epoch = int(ckpt.get("best_epoch", 0))
            history = ckpt.get("history", history)
            early_stop_triggered = bool(ckpt.get("early_stop_triggered", False))

            if early_stop_triggered and not force_resume:
                logger.info(
                    f"Run already halted via early stopping at epoch {ckpt.get('epoch')}. "
                    "Use --force-resume to rewind to best checkpoint."
                )
                logger.close()
                return ckpt

            if force_resume:
                early_stop_triggered = False
                no_improve_epochs = 0
                start_epoch = int(best_epoch) + 1
                logger.info(f"Force-resumed from BEST checkpoint (epoch {best_epoch}) -> continuing at epoch {start_epoch}.")
            else:
                start_epoch = int(ckpt.get("epoch", 0)) + 1
                logger.info(f"Resumed from LAST checkpoint (epoch {ckpt.get('epoch')}) -> continuing at epoch {start_epoch}.")

    env = HospitalShiftEnv(
        curriculum_stage=1,
        shift_duration_s=shift_duration_s,
        seed=seed,
        env_mode=env_mode,
    )

    t0 = time.time()
    prev_stage: int | None = None
    for epoch in range(start_epoch, epochs + 1):
        stage = stage_override if stage_override in (1, 2) else (1 if epoch <= max(1, int(0.4 * epochs)) else 2)
        if prev_stage is not None and stage != prev_stage:
            logger.info(f"Curriculum advanced from Stage {prev_stage} to Stage {stage}. Resetting patience counter.")
            no_improve_epochs = 0
            best_val_acc = -float("inf")
        prev_stage = stage
        env.set_stage(stage)
        obs = env.reset(seed=seed + epoch * 17)

        obs_buf = np.zeros((steps_per_epoch, OBS_DIM), dtype=np.float32)
        act_buf = np.zeros((steps_per_epoch, ACT_DIM), dtype=np.float32)
        teacher_buf = np.zeros((steps_per_epoch, ACT_DIM), dtype=np.float32)
        logp_buf = np.zeros(steps_per_epoch, dtype=np.float32)
        rew_buf = np.zeros(steps_per_epoch, dtype=np.float32)
        done_buf = np.zeros(steps_per_epoch, dtype=np.float32)
        val_buf = np.zeros(steps_per_epoch, dtype=np.float32)

        bc_weight = max(0.0, bc_coef_init * (1.0 - (epoch - 1) / max(1.0, float(epochs))))
        ep_team_rewards: list[float] = []

        for step_idx in range(steps_per_epoch):
            obs_buf[step_idx] = obs
            teacher_act = env.teacher_action()
            teacher_buf[step_idx] = teacher_act

            obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
            with torch.no_grad():
                action_t, logp_t, _, val_t = agent.get_action_and_value(obs_t)

            policy_act = action_t.squeeze(0).cpu().numpy()
            # Blend teacher guidance during early curriculum to accelerate safe corridor navigation
            exec_act = np.clip((1.0 - bc_weight) * policy_act + bc_weight * teacher_act, -1.0, 1.0)

            act_buf[step_idx] = policy_act
            logp_buf[step_idx] = float(logp_t.item())
            val_buf[step_idx] = float(val_t.item())

            next_obs, reward, done, info = env.step(exec_act)
            rew_buf[step_idx] = reward
            done_buf[step_idx] = 1.0 if done else 0.0

            if done:
                ep_team_rewards.append(float(info["cumulative_team_reward"]))
                obs = env.reset()
            else:
                obs = next_obs

        if not ep_team_rewards:
            ep_team_rewards.append(float(env.cumulative_team_reward))

        # Compute GAE advantages and returns
        with torch.no_grad():
            next_obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
            next_val = float(agent.get_value(next_obs_t).item())

        advantages = np.zeros(steps_per_epoch, dtype=np.float32)
        lastgaelam = 0.0
        for t in reversed(range(steps_per_epoch)):
            if t == steps_per_epoch - 1:
                nextnonterminal = 1.0 - done_buf[t]
                nextvalues = next_val
            else:
                nextnonterminal = 1.0 - done_buf[t]
                nextvalues = val_buf[t + 1]
            delta = rew_buf[t] + gamma * nextvalues * nextnonterminal - val_buf[t]
            lastgaelam = delta + gamma * gae_lambda * nextnonterminal * lastgaelam
            advantages[t] = lastgaelam
        returns = advantages + val_buf

        b_obs = torch.as_tensor(obs_buf, dtype=torch.float32, device=device)
        b_act = torch.as_tensor(act_buf, dtype=torch.float32, device=device)
        b_teacher = torch.as_tensor(teacher_buf, dtype=torch.float32, device=device)
        b_logp = torch.as_tensor(logp_buf, dtype=torch.float32, device=device)
        b_adv = torch.as_tensor(advantages, dtype=torch.float32, device=device)
        b_ret = torch.as_tensor(returns, dtype=torch.float32, device=device)

        b_inds = np.arange(steps_per_epoch)
        epoch_losses: list[float] = []

        for _ in range(ppo_epochs):
            np.random.shuffle(b_inds)
            for start in range(0, steps_per_epoch, batch_size):
                end = start + batch_size
                mb_inds = b_inds[start:end]

                _, newlogprob, entropy, newvalue = agent.get_action_and_value(
                    b_obs[mb_inds], b_act[mb_inds]
                )
                logratio = newlogprob - b_logp[mb_inds]
                ratio = logratio.exp()

                mb_adv = b_adv[mb_inds]
                mb_adv = (mb_adv - mb_adv.mean()) / (mb_adv.std() + 1e-8)

                pg_loss1 = -mb_adv * ratio
                pg_loss2 = -mb_adv * torch.clamp(ratio, 1.0 - clip_coef, 1.0 + clip_coef)
                pg_loss = torch.max(pg_loss1, pg_loss2).mean()

                v_loss = 0.5 * ((newvalue - b_ret[mb_inds]) ** 2).mean()
                entropy_loss = entropy.mean()

                # Auxiliary imitation loss toward LiDAR/tether-safe teacher
                pred_mean = torch.tanh(agent.actor_mean(agent.actor_backbone(b_obs[mb_inds])))
                bc_loss = ((pred_mean - b_teacher[mb_inds]) ** 2).mean()

                loss = pg_loss - ent_coef * entropy_loss + vf_coef * v_loss + 0.5 * bc_loss

                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(agent.parameters(), 0.5)
                optimizer.step()

                global_step += 1
                epoch_losses.append(float(loss.item()))

        scheduler.step()
        train_loss = float(np.mean(epoch_losses)) if epoch_losses else 0.0
        train_r_team = float(np.mean(ep_team_rewards))

        eval_metrics = evaluate_policy(
            agent=agent,
            stage=stage,
            n_episodes=val_episodes,
            shift_duration_s=shift_duration_s,
            seed=seed + epoch * 101,
            device=device,
            env_mode=env_mode,
        )
        val_r_team = eval_metrics["val_r_team"]
        val_loss = -val_r_team

        history["train_losses"].append(train_loss)
        history["val_losses"].append(val_loss)
        history["train_accs"].append(train_r_team)
        history["val_accs"].append(val_r_team)
        history["val_patients_helped"].append(eval_metrics["val_patients_helped"])
        history["val_collisions"].append(eval_metrics["val_collisions"])

        elapsed = time.time() - t0
        epochs_done = epoch - start_epoch + 1
        epochs_left = max(0, epochs - epoch)
        eta_s = (elapsed / max(1, epochs_done)) * epochs_left
        current_lr = float(optimizer.param_groups[0]["lr"])

        logger.progress(
            epoch=epoch,
            total_epochs=epochs,
            step=steps_per_epoch,
            total_steps=steps_per_epoch,
            loss=train_loss,
            reward=val_r_team,
            lr=current_lr,
            eta_s=eta_s,
        )

        epoch_row = {
            "epoch": epoch,
            "global_step": global_step,
            "curriculum_stage": stage,
            "train_loss": train_loss,
            "train_r_team": train_r_team,
            "val_r_team": val_r_team,
            "val_return": eval_metrics["val_return"],
            "val_patients_helped": eval_metrics["val_patients_helped"],
            "val_collisions": eval_metrics["val_collisions"],
            "lr": current_lr,
        }
        logger.epoch_summary(epoch_row)

        improved = val_r_team >= best_val_acc
        if improved:
            best_val_acc = val_r_team
            best_val_loss = val_loss
            best_epoch = epoch
            no_improve_epochs = 0
            save_checkpoint(
                path=logger.best_ckpt_path,
                model=agent,
                optimizer=optimizer,
                scheduler=scheduler,
                epoch=epoch,
                global_step=global_step,
                best_val_loss=best_val_loss,
                best_val_acc=best_val_acc,
                best_epoch=best_epoch,
                early_stop_triggered=False,
                history=history,
                config=config,
                seed=seed,
            )
        else:
            no_improve_epochs += 1
            if no_improve_epochs >= patience:
                early_stop_triggered = True

        # Always save _last.pt at the end of every epoch (§3, §5)
        save_checkpoint(
            path=logger.last_ckpt_path,
            model=agent,
            optimizer=optimizer,
            scheduler=scheduler,
            epoch=epoch,
            global_step=global_step,
            best_val_loss=best_val_loss,
            best_val_acc=best_val_acc,
            best_epoch=best_epoch,
            early_stop_triggered=early_stop_triggered,
            history=history,
            config=config,
            seed=seed,
        )

        if early_stop_triggered:
            logger.info(f"Early stopping triggered at epoch {epoch} (best_epoch={best_epoch}).")
            break

    # Consolidate cross-run artifacts into experiments/results/rl_hospital/ (§1, §6)
    consolidated_history_path = results_dir / "training_history.json"
    consolidated_history_path.write_text(
        json.dumps(
            {
                "run_name": safe_name,
                "run_dir": str(logger.run_dir),
                "best_epoch": best_epoch,
                "best_val_r_team": best_val_acc,
                "history": history,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    np.savez_compressed(
        results_dir / "rollout_summary.npz",
        train_losses=np.asarray(history["train_losses"], dtype=np.float32),
        val_r_team=np.asarray(history["val_accs"], dtype=np.float32),
        val_patients_helped=np.asarray(history["val_patients_helped"], dtype=np.float32),
        val_collisions=np.asarray(history["val_collisions"], dtype=np.float32),
    )
    best_helped = (
        float(max(history["val_patients_helped"])) if history["val_patients_helped"] else 0.0
    )
    update_results_readme(
        results_root=Path(experiments_root).resolve() / "results",
        run_name=safe_name,
        run_dir=logger.run_dir,
        best_epoch=best_epoch,
        best_r_team=best_val_acc,
        best_helped=best_helped,
    )

    logger.info(
        f"Training complete. Best epoch={best_epoch} | best_val_R_team={best_val_acc:.2f} | "
        f"checkpoints saved in {logger.checkpoints_dir}"
    )
    logger.close()
    return {
        "run_dir": logger.run_dir,
        "best_ckpt": logger.best_ckpt_path,
        "last_ckpt": logger.last_ckpt_path,
        "best_epoch": best_epoch,
        "best_val_r_team": best_val_acc,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the Hospital Helper Robot PPO policy (LOGGING_CHECKPOINT_RULES.md compliant)."
    )
    parser.add_argument("--run-name", type=str, default="PPOHospital-curriculum")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--steps-per-epoch", type=int, default=900)
    parser.add_argument("--patience", type=int, default=20, help="Early stopping patience")
    parser.add_argument("--val-episodes", type=int, default=2, help="Number of evaluation episodes per epoch")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--stage", type=int, default=0, choices=[0, 1, 2])
    parser.add_argument("--resume", action="store_true", help="Resume from latest <run_name>_last.pt")
    parser.add_argument(
        "--force-resume",
        action="store_true",
        help="Rewind to <run_name>_best.pt and continue with fresh early-stopping budget",
    )
    parser.add_argument(
        "--resume-from",
        type=str,
        default=None,
        help="Explicit directory path of previous run to resume from",
    )
    parser.add_argument(
        "--env-mode",
        type=str,
        default="solo",
        choices=["solo", "full"],
        help="Training environment mode: 'solo' (1 patient focus, nearby spawn) or 'full' (multi-NPC, patrolling doctor)",
    )
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cuda", "cpu"], help="Hardware device")
    parser.add_argument("--tb", action="store_true", help="Enable TensorBoard logging")
    parser.add_argument("--smoke", action="store_true", help="Fast smoke test run")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    train_hospital_rl(
        run_name=args.run_name,
        epochs=args.epochs,
        steps_per_epoch=args.steps_per_epoch,
        patience=args.patience,
        val_episodes_override=args.val_episodes,
        seed=args.seed,
        stage_override=args.stage,
        resume=args.resume,
        force_resume=args.force_resume,
        resume_from=args.resume_from,
        env_mode=args.env_mode,
        device_choice=args.device,
        enable_tb=args.tb,
        smoke=args.smoke,
    )


if __name__ == "__main__":
    main()
