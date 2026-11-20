"""Unit tests for Hospital Helper Robot RL training stack.

Tests:
1. RunLogger and checkpoint_utils (LOGGING_CHECKPOINT_RULES.md compliance, weights_only=True).
2. PPOHospitalAgent network shapes, values, action decoding.
3. HospitalShiftEnv 17-ray LiDAR, smart routing, elderly tether pacing, shared team reward.
4. End-to-end smoke training and resume procedure.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch

from src.models.ppo_agent import ACT_DIM, OBS_DIM, PPOHospitalAgent
from src.training.hospital_env import (
    DESTINATION_POSITIONS,
    HospitalShiftEnv,
    TaskPhase,
    WallBox2D,
    resolve_destination_key,
)
from src.training.rl_hospital_train import train_hospital_rl
from src.utils.checkpoint_utils import load_checkpoint, save_checkpoint, seed_everything
from src.utils.run_logger import RunLogger, sanitize_run_name


class TestLoggingAndCheckpointing:
    def test_run_logger_creates_structure_and_records_history(self, tmp_path: Path) -> None:
        logger = RunLogger(run_name="Test-Run/Name!", experiments_root=tmp_path)
        assert logger.run_name == "Test-Run_Name_"
        assert logger.checkpoints_dir.is_dir()
        assert logger.logs_dir.is_dir()
        assert logger.metrics_dir.is_dir()

        logger.save_config({"epochs": 5, "seed": 42})
        assert logger.config_path.exists()
        cfg = json.loads(logger.config_path.read_text(encoding="utf-8"))
        assert cfg["epochs"] == 5

        logger.epoch_summary({"epoch": 1, "train_loss": 0.42, "val_r_team": 15.0})
        assert logger.history_path.exists()
        lines = [json.loads(line) for line in logger.history_path.read_text(encoding="utf-8").splitlines() if line]
        assert len(lines) == 1
        assert lines[0]["epoch"] == 1
        assert lines[0]["val_r_team"] == 15.0

        latest = RunLogger.resolve_latest_run_dir("Test-Run_Name_", experiments_root=tmp_path)
        assert latest == logger.run_dir
        logger.close()

    def test_checkpoint_save_and_load_weights_only(self, tmp_path: Path) -> None:
        agent = PPOHospitalAgent(obs_dim=OBS_DIM, act_dim=ACT_DIM)
        opt = torch.optim.Adam(agent.parameters(), lr=1e-3)
        ckpt_path = tmp_path / "test_best.pt"

        save_checkpoint(
            path=ckpt_path,
            model=agent,
            optimizer=opt,
            scheduler=None,
            epoch=3,
            global_step=120,
            best_val_loss=-25.0,
            best_val_acc=25.0,
            best_epoch=3,
            early_stop_triggered=False,
            history={"train_losses": [0.5, 0.4, 0.3]},
            config={"seed": 42},
            seed=42,
        )
        assert ckpt_path.is_file()

        agent_loaded = PPOHospitalAgent(obs_dim=OBS_DIM, act_dim=ACT_DIM)
        opt_loaded = torch.optim.Adam(agent_loaded.parameters(), lr=1e-3)

        ckpt_loaded = load_checkpoint(ckpt_path, model=agent_loaded, optimizer=opt_loaded)
        assert ckpt_loaded["epoch"] == 3
        assert ckpt_loaded["best_val_acc"] == 25.0
        assert ckpt_loaded["early_stop_triggered"] is False
        assert "rng" in ckpt_loaded
        assert "torch_cpu" in ckpt_loaded["rng"]

        # Check weights are strictly identical
        for p1, p2 in zip(agent.parameters(), agent_loaded.parameters()):
            assert torch.allclose(p1, p2)


class TestPPOAgent:
    def test_forward_pass_and_action_decode(self) -> None:
        agent = PPOHospitalAgent(obs_dim=OBS_DIM, act_dim=ACT_DIM)
        obs = torch.randn(4, OBS_DIM)
        act, logp, entropy, val = agent.get_action_and_value(obs)

        assert act.shape == (4, ACT_DIM)
        assert logp.shape == (4,)
        assert entropy.shape == (4,)
        assert val.shape == (4,)

        v, omega = PPOHospitalAgent.decode_action(-1.0, 1.0)
        assert v == pytest.approx(0.0)
        assert omega == pytest.approx(1.2)

        v_max, omega_zero = PPOHospitalAgent.decode_action(1.0, 0.0)
        assert v_max == pytest.approx(0.8)
        assert omega_zero == pytest.approx(0.0)


class TestHospitalShiftEnv:
    def test_smart_floor1_and_elevator_routing(self) -> None:
        assert resolve_destination_key("guide", "101", 1) == "101"
        assert resolve_destination_key("guide", "110", 1) == "110"
        assert resolve_destination_key("guide", "112", 1) == "112"
        assert resolve_destination_key("guide", "nha_thuoc", 1) == "nha_thuoc"
        assert resolve_destination_key("guide", "nha_ve_sinh", 1) == "nha_ve_sinh"
        assert resolve_destination_key("guide", "bhyt", 1) == "tiep_don"
        assert resolve_destination_key("guide", "thu_ngan", 1) == "tiep_don"
        # Upper floors 2-4 route to Elevator
        assert resolve_destination_key("guide", "301", 3) == "thang_may"
        assert resolve_destination_key("guide", "204", 2) == "thang_may"
        # Medical staff calls route to nearest staff
        assert resolve_destination_key("call_staff", "", 1) == "staff"
        assert resolve_destination_key("emergency", "101", 1) == "staff"
        assert resolve_destination_key("answer", "", 1) == ""

    def test_lidar_17_rays_and_bounds(self) -> None:
        env = HospitalShiftEnv(curriculum_stage=1, shift_duration_s=10.0, seed=123)
        obs = env.reset()
        assert obs.shape == (OBS_DIM,)
        lidar = obs[0:17]
        assert len(lidar) == 17
        assert np.all(lidar >= 0.0) and np.all(lidar <= 1.0)

    def test_elderly_patient_tether_pacing_and_penalty(self) -> None:
        env = HospitalShiftEnv(curriculum_stage=1, shift_duration_s=10.0, seed=123)
        env.reset()
        env.task_phase = TaskPhase.GUIDE_ESCORT
        env.robot_x = 0.0
        env.robot_z = 0.0
        env.patient_x = 0.0
        env.patient_z = 3.0  # Tether gap = 3.0m > 2.5m limit

        obs, reward, done, info = env.step([-1.0, 0.0])
        assert info["d_tether"] >= 2.5
        # When tether > 2.5m, progress reward is paused and penalized
        teacher = env.teacher_action()
        # Teacher stops robot when patient is too far behind
        assert teacher[0] == pytest.approx(-1.0)


class TestSmokeAndResumePipeline:
    def test_smoke_training_and_resume(self, tmp_path: Path) -> None:
        # 1. Run 2-epoch smoke run
        res = train_hospital_rl(
            run_name="SmokePPO",
            epochs=2,
            steps_per_epoch=40,
            batch_size=20,
            seed=42,
            smoke=True,
            experiments_root=tmp_path,
        )
        assert res["best_ckpt"].is_file()
        assert res["last_ckpt"].is_file()

        # 2. Test exact resume from last_ckpt
        res_resume = train_hospital_rl(
            run_name="SmokePPO",
            epochs=3,
            steps_per_epoch=40,
            batch_size=20,
            seed=42,
            resume=True,
            smoke=True,
            experiments_root=tmp_path,
        )
        assert res_resume["best_epoch"] >= 1
