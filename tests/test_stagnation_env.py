"""Unit tests for stagnation timeout mechanism in HospitalShiftEnv."""

from __future__ import annotations
import numpy as np
import pytest

from src.training.hospital_env import HospitalShiftEnv, TaskPhase


def test_stagnation_disabled_by_default():
    env = HospitalShiftEnv(env_mode="solo", stagnation_timeout_s=0.0)
    env.reset(seed=42)
    assert env.max_stagnation_steps == 0
    assert env.steps_since_task == 0

    # Step without moving for 10 steps
    for _ in range(10):
        _, _, done, info = env.step(np.array([-1.0, 0.0], dtype=np.float32))
    assert not done
    assert env.steps_since_task == 10
    assert info["exit_reason"] == "RUNNING"


def test_stagnation_terminates_at_limit():
    env = HospitalShiftEnv(
        env_mode="solo",
        stagnation_timeout_s=5.0,  # 5.0s / 0.2s = 25 steps
        stagnation_penalty=-10.0,
    )
    env.reset(seed=123)
    assert env.max_stagnation_steps == 25

    done = False
    info = {}
    # Take stationary action
    for _ in range(25):
        _, _, done, info = env.step(np.array([-1.0, 0.0], dtype=np.float32))

    assert done is True
    assert info["exit_reason"] == "STAGNATION_TIMEOUT"
    assert info["r_team"] == -10.0
    assert info["cumulative_team_reward"] == -10.0
    assert env.steps_since_task == 25


def test_stagnation_resets_on_task_completion():
    env = HospitalShiftEnv(
        env_mode="solo",
        stagnation_timeout_s=10.0,  # 50 steps
        stagnation_penalty=-10.0,
    )
    env.reset(seed=777)
    # Simulate verbal answer scenario
    env.scenario_action = "answer"
    env.task_phase = TaskPhase.SEARCH_PATIENT
    # Position robot near patient
    env.robot_x = env.patient_x
    env.robot_z = env.patient_z

    # Take step
    _, r, done, info = env.step(np.array([0.0, 0.0], dtype=np.float32))
    assert info["event"] == "answer"
    assert env.steps_since_task == 0
    assert env.patients_helped == 1
    assert not done
