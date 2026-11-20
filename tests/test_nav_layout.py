"""Godot-exported nav layout, grid path planning, elevator rides, NPC side-steps and escort following in HospitalShiftEnv."""

from __future__ import annotations

import copy
import math
import re
from pathlib import Path

import numpy as np

from src.training.hospital_env import (
    _DOORS,
    _near_doorway,
    DESTINATION_POSITIONS,
    ELEVATOR_POSITIONS,
    ROBOT_DOCK,
    HospitalShiftEnv,
    TaskPhase,
    floor_of,
    is_blocked,
    nav_grid,
)

RL_CONTROLLER_GD = Path(__file__).resolve().parents[1] / "sim_vision" / "godot" / "scripts" / "rl_controller.gd"


def test_godot_routing_doors_match_layout():
    """rl_controller.gd DOORS must equal the doors derived from hospital_layout.json."""
    text = RL_CONTROLLER_GD.read_text(encoding="utf-8")
    for (floor, side), (centres, dividers) in _DOORS.items():
        m = re.search(rf'"{floor}_{side}": \[\[([^\]]+)\], \[([^\]]+)\]\]', text)
        assert m, f"missing {floor}_{side} in rl_controller.gd"
        gd_centres = [float(v) for v in m.group(1).split(",")]
        gd_dividers = [float(v) for v in m.group(2).split(",")]
        assert np.allclose(gd_centres, centres, atol=1e-3)
        assert np.allclose(gd_dividers, dividers, atol=1e-3)


def test_destinations_are_reachable_free_space():
    for key, (x, z) in DESTINATION_POSITIONS.items():
        assert not is_blocked(x, z, 0.32), key


def test_robot_slides_along_wall_instead_of_freezing():
    env = HospitalShiftEnv(env_mode="solo")
    env.reset(seed=1)
    # Corridor, just below the north corridor wall (z = -2), heading diagonally into it
    env.robot_x, env.robot_z = -2.5, -1.4
    assert not is_blocked(env.robot_x, env.robot_z, 0.32)
    env.robot_yaw = math.radians(-45.0)  # forward = (-sin, -cos) -> (+x, -z) diagonal into the wall
    x0 = env.robot_x
    for _ in range(5):
        env.step(np.array([1.0, 0.0], dtype=np.float32))
    assert env.robot_x > x0 + 0.2
    assert not is_blocked(env.robot_x, env.robot_z, 0.32)


def test_search_takes_elevator_back_to_patient_floor():
    env = HospitalShiftEnv(env_mode="solo")
    env.reset(seed=2)
    env.task_phase = TaskPhase.SEARCH_PATIENT
    env.patient_x, env.patient_z = 0.0, 0.0  # floor 1
    env.robot_x, env.robot_z = ELEVATOR_POSITIONS[2]  # robot left on floor 2
    _, _, _, info = env.step(np.array([-1.0, 0.0], dtype=np.float32))
    assert info["event"] == "elevator_ride"
    assert floor_of(env.robot_x) == 1


def test_escorted_patient_follows_trail_through_door_without_clipping():
    env = HospitalShiftEnv(env_mode="solo")
    env.reset(seed=3)
    env.task_phase = TaskPhase.GUIDE_ESCORT
    env.goal_key = "110"
    # Robot walks from the corridor through the north door at x=0 into room 110
    env.robot_x, env.robot_z, env.robot_yaw = 2.5, 0.0, math.pi / 2  # facing -x
    env.patient_x, env.patient_z = 3.5, 0.0
    path = [(1.5, 0.0), (0.5, 0.0), (0.0, -0.5), (0.0, -1.5), (0.0, -2.5), (0.0, -3.5), (0.0, -4.0)]
    for tx, tz in path:
        for _ in range(15):
            env.robot_x += float(np.clip(tx - env.robot_x, -0.08, 0.08))
            env.robot_z += float(np.clip(tz - env.robot_z, -0.08, 0.08))
            env._step_escorted_patient()
            assert not is_blocked(env.patient_x, env.patient_z, 0.0), (env.patient_x, env.patient_z)
    for _ in range(60):
        env._step_escorted_patient()
    assert env.patient_z < -2.1, "patient followed the robot through the doorway into the room"
    assert math.hypot(env.robot_x - env.patient_x, env.robot_z - env.patient_z) <= 1.0


def test_planner_routes_through_the_doorway_and_measures_path_length():
    env = HospitalShiftEnv(env_mode="solo")
    env.reset(seed=4)
    env.robot_x, env.robot_z = -6.0, 0.0  # corridor, west of room 110's door (x = 0, z = -2)
    tx, tz = DESTINATION_POSITIONS["110"]
    env.set_nav_target(tx, tz)
    assert env.nav_remaining > math.hypot(tx - env.robot_x, tz - env.robot_z) + 0.5  # detour via the door
    assert not is_blocked(env.goal_x, env.goal_z, 0.32)
    assert env.goal_z > -2.0, "sub-goal stays in the corridor until the robot lines up with the door"
    # Walking the sub-goals reaches the room without touching walls or furniture
    for _ in range(200):
        dx, dz = env.goal_x - env.robot_x, env.goal_z - env.robot_z
        d = math.hypot(dx, dz)
        if env.nav_remaining < 0.3:
            break
        env.robot_x += dx / d * min(0.2, d)
        env.robot_z += dz / d * min(0.2, d)
        assert not is_blocked(env.robot_x, env.robot_z, 0.32), (env.robot_x, env.robot_z)
        env.set_nav_target(tx, tz)
    assert math.hypot(tx - env.robot_x, tz - env.robot_z) < 0.5


def test_every_destination_reachable_from_the_dock():
    for key, (x, z) in DESTINATION_POSITIONS.items():
        grid = nav_grid(floor_of(x))
        start = ROBOT_DOCK[:2] if floor_of(x) == 1 else ELEVATOR_POSITIONS[2]
        assert math.isfinite(grid.distance(grid.field(x, z), *start)), key


def test_shift_usually_starts_at_the_dock_by_the_main_entrance():
    env = HospitalShiftEnv(env_mode="full")
    at_dock = 0
    for seed in range(60):
        env.reset(seed=seed)
        if (env.robot_x, env.robot_z) == ROBOT_DOCK[:2]:
            at_dock += 1
            assert env.robot_yaw == ROBOT_DOCK[2]
            assert math.hypot(env.patient_x - env.robot_x, env.patient_z - env.robot_z) >= 3.5
    assert 30 <= at_dock <= 58


def test_doctor_never_side_steps_into_the_robot_lane():
    """Doctor patrols near the north corridor wall; the wall side is blocked, so it must not cross in front of the robot."""
    env = HospitalShiftEnv(env_mode="full")
    env.reset(seed=5)
    doc = next(n for n in env.npcs if n["walks"])
    doc["x"], doc["z"] = -1.0, -1.35
    env.robot_x, env.robot_z, env.robot_yaw = 0.2, -0.75, math.pi / 2  # heading west, 0.6 m beside the doctor's line
    for _ in range(8):
        env.step(np.array([-0.3, 0.0], dtype=np.float32))
        assert doc["z"] <= -1.3, doc


def test_robot_can_back_out_of_an_npc_that_walked_into_it():
    env = HospitalShiftEnv(env_mode="full")
    env.reset(seed=6)
    doc = next(n for n in env.npcs if n["walks"])
    doc["x"], doc["z"] = 0.0, -1.35
    env.robot_x, env.robot_z, env.robot_yaw = 0.0, -0.85, math.pi  # facing +z, away from the doctor
    env.step(np.array([1.0, 0.0], dtype=np.float32))
    assert env.robot_z > -0.85 + 0.1


def test_step_observation_matches_a_fresh_observation_of_the_same_state():
    """Godot's policy server rebuilds observations from raw state; training must see exactly the same features."""
    env = HospitalShiftEnv(env_mode="full", stagnation_timeout_s=45.0)
    env.reset(seed=7)
    for k in range(120):
        obs, _, done, _ = env.step(env.teacher_action())
        if done:
            break
        if k % 20 == 19:
            probe = HospitalShiftEnv(env_mode="full")
            probe.reset(seed=0)
            for attr in ("robot_x", "robot_z", "robot_yaw", "robot_v", "robot_omega", "patient_x", "patient_z", "task_phase", "goal_key"):
                setattr(probe, attr, getattr(env, attr))
            probe.npcs = copy.deepcopy(env.npcs)
            probe.set_nav_target(*env._nav_final_target())
            assert np.allclose(probe._get_obs(), obs, atol=1e-5), k


def test_patrolling_doctor_waits_instead_of_walking_into_the_robot_then_turns_back():
    env = HospitalShiftEnv(env_mode="full")
    env.reset(seed=8)
    doc = next(n for n in env.npcs if n["walks"])
    doc["x"], doc["z"], doc["wp_index"], doc["pardon_enabled"] = -1.0, -1.35, 1, False  # walking east to (1.8, -1.35)
    env.robot_x, env.robot_z, env.robot_yaw, env.robot_v = -0.1, -1.35, 0.0, 0.0  # parked on its route
    for _ in range(int(1.5 / env.dt)):
        env._step_npcs()
        assert math.hypot(doc["x"] - env.robot_x, doc["z"] - env.robot_z) >= 0.9 - 1e-6
    for _ in range(int(3.0 / env.dt)):
        env._step_npcs()
    assert doc["x"] < -1.0 - 0.3, "kept waiting > 2 s -> turned back toward its other waypoint"


def test_pardon_spot_never_blocks_a_doorway():
    assert _near_doorway(0.0, -1.5, 1.2)  # right in front of room 110's door
    assert not _near_doorway(-2.0, -1.35, 1.2)
