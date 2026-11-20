"""Unit tests for the Solo Patient Focus Hospital RL Environment."""

import math
import numpy as np
import pytest

from src.training.hospital_env import HospitalShiftEnv, TaskPhase, OBS_DIM


def test_solo_env_initial_robot_spawn_independent():
    """Verify robot and patient spawn independently in public areas so robot learns to search."""
    for seed in range(42, 62):
        env = HospitalShiftEnv(env_mode="solo", seed=seed)
        obs = env.reset(seed=seed)
        assert obs.shape == (OBS_DIM,)

        # Distance check: spawned at separate locations across public corridors/lobby
        dist = math.hypot(env.patient_x - env.robot_x, env.patient_z - env.robot_z)
        assert dist >= 2.5, f"Expected independent spawn >= 2.5m, got {dist:.2f}m for seed {seed}"

        # Doctor must be disabled in solo mode
        assert env.doctor_active is False

        # Patient must be in non-medical area (Corridor: z in [-1.4, 1.4], Lobby: z in [2.1, 6.6], x in [-3.5, 3.5])
        assert env.patient_z >= -2.0, f"Patient spawned in north exam room: z={env.patient_z}"
        if env.patient_z > 2.0:
            assert abs(env.patient_x) <= 3.8, f"Patient spawned outside lobby: x={env.patient_x}, z={env.patient_z}"


def test_solo_env_continuous_robot_persistence():
    """Verify that when a patient is resolved, next patient appears at random corridor/lobby spot while robot persists."""
    env = HospitalShiftEnv(env_mode="solo", seed=123)
    env.reset(seed=123)

    # Record robot position
    rx_before = env.robot_x
    rz_before = env.robot_z

    # Trigger next patient spawn
    env._spawn_next_patient()

    # Robot position must be strictly preserved
    assert env.robot_x == rx_before
    assert env.robot_z == rz_before

    # New patient must be in public area and at least 3m from robot
    d_new = math.hypot(env.patient_x - env.robot_x, env.patient_z - env.robot_z)
    assert d_new >= 2.9, f"New patient too close to robot: {d_new:.2f}m"
    assert env.patient_z >= -2.0


def test_solo_scenario_task_distribution():
    """Verify that solo task sampling conforms to ~70% escort, ~15% answer, ~15% call staff."""
    env = HospitalShiftEnv(env_mode="solo", seed=999)
    env.reset()

    counts = {"guide": 0, "answer": 0, "call_staff": 0}
    n_samples = 1500
    for _ in range(n_samples):
        env._sample_solo_scenario()
        counts[env.scenario_action] += 1

    p_guide = counts["guide"] / n_samples
    p_answer = counts["answer"] / n_samples
    p_staff = counts["call_staff"] / n_samples

    assert 0.65 <= p_guide <= 0.75, f"Expected ~70% guide, got {p_guide:.2%}"
    assert 0.11 <= p_answer <= 0.19, f"Expected ~15% answer, got {p_answer:.2%}"
    assert 0.11 <= p_staff <= 0.19, f"Expected ~15% staff, got {p_staff:.2%}"


def test_solo_env_step_and_reward():
    """Verify execution of full steps in solo environment."""
    env = HospitalShiftEnv(env_mode="solo", shift_duration_s=36.0, seed=42)
    obs = env.reset(seed=42)

    total_r = 0.0
    for _ in range(50):
        # Step forward
        obs, r, done, info = env.step(np.array([0.5, 0.0], dtype=np.float32))
        assert obs.shape == (OBS_DIM,)
        assert isinstance(r, float)
        total_r += r
        if done:
            break

    assert info["collisions"] >= 0
    assert "r_team" in info
