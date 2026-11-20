"""Unit tests for Floor 2 and Elevator routing logic in hospital environment."""

import math
import numpy as np
import pytest
from src.training.hospital_env import (
    DESTINATION_POSITIONS,
    FLOOR1_DIRECT_SLOTS,
    FLOOR2_DIRECT_SLOTS,
    HospitalShiftEnv,
    TaskPhase,
    resolve_destination_key,
    resolve_final_target,
)


class TestFloor2ElevatorRouting:
    def test_resolve_final_target_floor2(self):
        assert resolve_final_target("guide", "205", dest_floor=2) == "205"
        assert resolve_final_target("guide", "201", dest_floor=2) == "201"
        assert resolve_final_target("guide", "204", dest_floor=2) == "204"
        assert resolve_final_target("guide", "210", dest_floor=2) == "210"
        assert resolve_final_target("guide", "220", dest_floor=2) == "220"
        assert resolve_final_target("guide", "wc_t2", dest_floor=2) == "wc_t2"
        assert resolve_final_target("guide", "sanh_t2", dest_floor=2) == "sanh_t2"
        # Unmapped 2xx should map to default Floor 2 clinic 205
        assert resolve_final_target("guide", "230", dest_floor=2) == "205"

    def test_resolve_final_target_floor1(self):
        assert resolve_final_target("guide", "101", dest_floor=1) == "101"
        assert resolve_final_target("guide", "nha_thuoc", dest_floor=1) == "nha_thuoc"
        assert resolve_final_target("guide", "bhyt", dest_floor=1) == "tiep_don"
        assert resolve_final_target("call_staff", "", dest_floor=1) == "staff"

    def test_stage1_cross_floor_elevator_routing(self):
        # Patient on Floor 1 wants Floor 2 clinic (205) -> stage 1 goal must be Floor 1 elevator
        assert resolve_destination_key("guide", "205", dest_floor=2, current_floor=1) == "thang_may"
        assert resolve_destination_key("guide", "210", dest_floor=2, current_floor=1) == "thang_may"
        assert resolve_destination_key("guide", "201", dest_floor=2, current_floor=1) == "thang_may"

        # Backwards compatible with floor_num keyword
        assert resolve_destination_key("guide", "205", floor_num=2) == "thang_may"

        # Patient on Floor 1 wants Floor 1 clinic (101) -> direct to 101
        assert resolve_destination_key("guide", "101", dest_floor=1, current_floor=1) == "101"

        # Patient on Floor 2 wants Floor 1 clinic (nha_thuoc) -> stage 1 goal must be Floor 2 elevator
        assert resolve_destination_key("guide", "nha_thuoc", dest_floor=1, current_floor=2) == "thang_may_t2"

        # Patient on Floor 2 wants Floor 2 clinic (210) -> direct to 210
        assert resolve_destination_key("guide", "210", dest_floor=2, current_floor=2) == "210"

    def test_floor2_anchors_side_by_side(self):
        # Floor 2 anchors must have X >= 35.0 (side-by-side offset at X = +50.0m)
        f2_keys = ["201", "204", "205", "210", "220", "sanh_t2", "wc_t2", "thang_may_t2"]
        for k in f2_keys:
            assert k in DESTINATION_POSITIONS, f"{k} not in DESTINATION_POSITIONS"
            x, z = DESTINATION_POSITIONS[k]
            assert x >= 35.0, f"Floor 2 room {k} must have X >= 35.0 (got {x})"

    def test_env_floor2_scenario_execution(self):
        env = HospitalShiftEnv(env_mode="solo", seed=42)
        obs = env.reset(seed=42)
        env.scenario_action = "guide"
        env.scenario_slot = "205"
        env.scenario_floor = 2

        # Step towards patient to engage
        for _ in range(100):
            if env.task_phase == TaskPhase.GUIDE_ESCORT:
                break
            env.robot_x = env.patient_x + 0.5
            env.robot_z = env.patient_z
            action = np.array([0.1, 0.0], dtype=np.float32)
            obs, reward, done, info = env.step(action)
            if done:
                break

        assert env.task_phase == TaskPhase.GUIDE_ESCORT
        assert env.goal_key == "thang_may"
        assert not np.isnan(obs).any(), "Observation must not contain NaNs"

    def test_env_complete_cross_floor_elevator_transit(self):
        """Test full transition: Floor 1 -> Elevator -> Teleport to Floor 2 -> Destination Room 205."""
        env = HospitalShiftEnv(env_mode="solo", seed=100)
        obs = env.reset(seed=100)
        env.scenario_action = "guide"
        env.scenario_slot = "205"
        env.scenario_floor = 2

        # 1. Engage patient
        env.robot_x = env.patient_x + 0.5
        env.robot_z = env.patient_z
        obs, reward, done, info = env.step(np.array([0.0, 0.0], dtype=np.float32))
        assert env.task_phase == TaskPhase.GUIDE_ESCORT
        assert env.goal_key == "thang_may"

        # 2. Escort to Floor 1 Elevator (10.5, 0.0)
        elev_f1_x, elev_f1_z = DESTINATION_POSITIONS["thang_may"]
        env.robot_x = elev_f1_x
        env.robot_z = elev_f1_z
        env.patient_x = elev_f1_x + 0.5
        env.patient_z = elev_f1_z

        obs, reward, done, info = env.step(np.array([0.0, 0.0], dtype=np.float32))

        # Check elevator transit triggered: robot teleported to Floor 2!
        assert env.goal_key == "205", f"Expected goal_key '205', got {env.goal_key}"
        assert env.robot_x >= 35.0, f"Robot should be on Floor 2 (X >= 35), got {env.robot_x}"
        assert env.patient_x >= 35.0, f"Patient should be on Floor 2 (X >= 35), got {env.patient_x}"
        assert info.get("r_team", 0.0) == 10.0, "Elevator transit bonus should be 10.0"

        # 3. Escort to final Floor 2 Clinic (205)
        dest_x, dest_z = DESTINATION_POSITIONS["205"]
        env.robot_x = dest_x
        env.robot_z = dest_z
        env.patient_x = dest_x + 0.5
        env.patient_z = dest_z

        obs, reward, done, info = env.step(np.array([0.0, 0.0], dtype=np.float32))

        # Check task completion on Floor 2!
        assert info.get("r_team", 0.0) == 30.0, "Guide arrived reward should be 30.0"
        assert env.patients_helped == 1
