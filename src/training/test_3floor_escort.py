"""Interactive/CLI Policy Test Script for 3-Floor Patient Escort.

Runs deterministic or stochastic evaluation shifts focusing 100% on patient escort
across Floors 1, 2, and 3. Prints detailed real-time event logs for every encounter,
elevator transit, tether status, and destination arrival.

Usage:
    python -m src.training.test_3floor_escort --episodes 5
    python -m src.training.test_3floor_escort --episodes 3 --verbose
    python -m src.training.test_3floor_escort --checkpoint path/to/PPOHospital-3floor-escort_best.pt
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import torch

from src.models.ppo_agent import ACT_DIM, OBS_DIM, PPOHospitalAgent
from src.training.hospital_env import HospitalShiftEnv, TaskPhase, floor_of


DEFAULT_CHECKPOINT = (
    "experiments/runs/20261027_183421_PPOHospital-3floor-escort-2k/checkpoints/PPOHospital-3floor-escort_best.pt"
)


def run_test_escort(
    checkpoint_path: str | Path = DEFAULT_CHECKPOINT,
    episodes: int = 5,
    shift_duration_s: float = 240.0,
    stagnation_timeout_s: float = 60.0,
    stagnation_penalty: float = -10.0,
    deterministic: bool = True,
    seed_base: int = 42,
    verbose: bool = True,
) -> dict[str, Any]:
    ckpt_p = Path(checkpoint_path)
    if not ckpt_p.is_file():
        raise FileNotFoundError(f"Checkpoint not found at: {ckpt_p}")

    device = torch.device("cpu")
    agent = PPOHospitalAgent(obs_dim=OBS_DIM, act_dim=ACT_DIM).to(device)
    ckpt = torch.load(ckpt_p, map_location=device, weights_only=True)
    state_dict = ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt
    agent.load_state_dict(state_dict)
    agent.eval()

    print("=" * 86)
    print(" 3-FLOOR PATIENT ESCORT POLICY INFERENCE TEST")
    print(f" Checkpoint  : {ckpt_p.name} (Trained: {ckpt.get('timestamp', 'N/A')})")
    print(f" Episodes    : {episodes} Shifts (Max {shift_duration_s:.0f}s per shift)")
    print(f" Mode        : 100% Escort Focus across Floors 1, 2, and 3")
    print("=" * 86)

    shift_results: list[dict[str, Any]] = []
    total_helped = 0
    total_collisions = 0
    total_elevator_transits = 0

    for ep in range(1, episodes + 1):
        env = HospitalShiftEnv(
            curriculum_stage=1,
            shift_duration_s=shift_duration_s,
            dt=0.2,
            seed=seed_base + ep * 31,
            env_mode="solo",
            stagnation_timeout_s=stagnation_timeout_s,
            stagnation_penalty=stagnation_penalty,
            escort_only=True,
        )
        obs = env.reset()
        done = False
        prev_phase = int(env.task_phase)
        last_event = ""
        events: list[str] = []
        patient_encounters = 0

        print(f"\n--- [SHIFT {ep}/{episodes}] Starting Shift (Seed {seed_base + ep * 31}) ---")
        p_fl = floor_of(env.patient_x)
        r_fl = floor_of(env.robot_x)
        print(f"  Robot Spawn  : Floor {r_fl} (X={env.robot_x:.1f}, Z={env.robot_z:.1f})")
        print(f"  Patient Spawn: Floor {p_fl} (X={env.patient_x:.1f}, Z={env.patient_z:.1f})")
        print(f"  Target Goal  : Floor {env.scenario_floor} -> {env.scenario_slot} (Action: {env.scenario_action})")

        while not done:
            obs_t = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                action_t, _, _, _ = agent.get_action_and_value(obs_t, deterministic=deterministic)
            act = action_t.squeeze(0).numpy()
            obs, rew, done, info = env.step(act)

            curr_phase = info["task_phase"]
            ev = info.get("event", "")

            # Log phase transitions & major events
            if curr_phase != prev_phase:
                phase_name = TaskPhase(curr_phase).name
                if curr_phase == int(TaskPhase.GUIDE_ESCORT):
                    patient_encounters += 1
                    t_s = env.step_count * 0.2
                    print(f"  [{t_s:5.1f}s] Patient engaged! Escort began -> Goal: '{env.goal_key}' (Floor {env.scenario_floor})")
                prev_phase = curr_phase

            if ev and ev != last_event:
                t_s = env.step_count * 0.2
                if ev == "elevator_transit":
                    total_elevator_transits += 1
                    cur_fl = floor_of(env.robot_x)
                    print(f"  [{t_s:5.1f}s] ELEVATOR TRANSIT -> Now on Floor {cur_fl} (Continuing escort to {env.goal_key})")
                elif ev == "guide_completed":
                    print(f"  [{t_s:5.1f}s] ESCORT COMPLETED! Patient safely arrived at: '{env.scenario_slot}' (Floor {env.scenario_floor}) [R_team +30]")
                    print(f"          Next patient spawned -> Floor {env.scenario_floor} '{env.scenario_slot}'")
                last_event = ev
                events.append(ev)
            elif not ev:
                last_event = ""

        # Shift summary
        helped = int(info["patients_helped"])
        r_team = float(info["cumulative_team_reward"])
        cols = int(info["collisions"])
        reason = info.get("exit_reason", "UNKNOWN")
        total_helped += helped
        total_collisions += cols

        print(f"--- [SHIFT {ep} SUMMARY] Helped: {helped} | R_team: {r_team:+.1f} | Cols: {cols} | Exit: {reason} ---")
        shift_results.append({
            "episode": ep,
            "helped": helped,
            "r_team": r_team,
            "collisions": cols,
            "exit_reason": reason,
        })

    print("\n" + "=" * 86)
    print(" OVERALL TEST RESULTS:")
    print(f" Total Shifts Evaluated   : {episodes}")
    print(f" Total Patients Escorted  : {total_helped} (Avg {total_helped / max(1, episodes):.1f} per shift)")
    print(f" Total Elevator Transits  : {total_elevator_transits}")
    print(f" Total Collisions         : {total_collisions}")
    print(f" Mean Team Reward         : {np.mean([r['r_team'] for r in shift_results]):+.1f}")
    print("=" * 86)
    return {"shifts": shift_results, "total_helped": total_helped}


def main() -> None:
    parser = argparse.ArgumentParser(description="Test 3-Floor Patient Escort Policy")
    parser.add_argument("--checkpoint", type=str, default=DEFAULT_CHECKPOINT, help="Path to .pt checkpoint")
    parser.add_argument("--episodes", type=int, default=3, help="Number of test shifts to run (default: 3)")
    parser.add_argument("--duration", type=float, default=240.0, help="Shift duration in seconds (default: 240)")
    parser.add_argument("--stagnation-timeout", type=float, default=60.0, help="Stagnation timeout in seconds (default: 60)")
    parser.add_argument("--stochastic", action="store_true", help="Sample actions stochastically instead of greedy argmax")
    parser.add_argument("--seed", type=int, default=100, help="Base random seed (default: 100)")
    parser.add_argument("--quiet", action="store_true", help="Suppress detailed per-step logs")

    args = parser.parse_args()

    run_test_escort(
        checkpoint_path=args.checkpoint,
        episodes=args.episodes,
        shift_duration_s=args.duration,
        stagnation_timeout_s=args.stagnation_timeout,
        deterministic=not args.stochastic,
        seed_base=args.seed,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
