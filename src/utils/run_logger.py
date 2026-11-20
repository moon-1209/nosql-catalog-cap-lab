"""Zero-dependency RunLogger implementing agents/rules/LOGGING_CHECKPOINT_RULES.md.

Creates and manages:
  experiments/runs/<YYYYmmdd_HHMMSS>_<run_name>/
    ├── checkpoints/
    │   ├── <run_name>_best.pt
    │   └── <run_name>_last.pt
    ├── logs/
    │   └── <run_name>.log          (auto-rotates at 20 MB to .<n>.log.gz, keeps 3)
    ├── metrics/
    │   ├── <run_name>_config.json
    │   └── <run_name>_history.jsonl
    └── tensorboard/                (optional when --tb is enabled)
  experiments/runs/registry.json    (maps run_name -> latest run dir)
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

MAX_LOG_BYTES = 20 * 1024 * 1024  # 20 MB rotation threshold
MAX_LOG_ARCHIVES = 3


def sanitize_run_name(name: str) -> str:
    """Enforce filesystem-safe [A-Za-z0-9_-] naming rule (§4)."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", name.strip())
    return cleaned or "unnamed_run"


class RunLogger:
    """Manages run directory, timestamped logs, config persistence, and JSONL history."""

    def __init__(
        self,
        run_name: str,
        experiments_root: Path | str = "experiments",
        run_dir: Path | str | None = None,
        enable_tb: bool = False,
    ) -> None:
        self.run_name = sanitize_run_name(run_name)
        self.experiments_root = Path(experiments_root).resolve()
        self.runs_root = self.experiments_root / "runs"
        self.results_root = self.experiments_root / "results"
        self.runs_root.mkdir(parents=True, exist_ok=True)
        self.results_root.mkdir(parents=True, exist_ok=True)

        if run_dir is not None:
            self.run_dir = Path(run_dir).resolve()
        else:
            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.run_dir = self.runs_root / f"{ts}_{self.run_name}"

        self.checkpoints_dir = self.run_dir / "checkpoints"
        self.logs_dir = self.run_dir / "logs"
        self.metrics_dir = self.run_dir / "metrics"
        self.tb_dir = self.run_dir / "tensorboard"

        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        self.best_ckpt_path = self.checkpoints_dir / f"{self.run_name}_best.pt"
        self.last_ckpt_path = self.checkpoints_dir / f"{self.run_name}_last.pt"
        self.log_path = self.logs_dir / f"{self.run_name}.log"
        self.config_path = self.metrics_dir / f"{self.run_name}_config.json"
        self.history_path = self.metrics_dir / f"{self.run_name}_history.jsonl"
        self.registry_path = self.runs_root / "registry.json"

        self._tb_writer: Any = None
        if enable_tb:
            self.tb_dir.mkdir(parents=True, exist_ok=True)
            try:
                from torch.utils.tensorboard import SummaryWriter

                self._tb_writer = SummaryWriter(log_dir=str(self.tb_dir))
            except Exception as exc:
                self.log("WARN", f"TensorBoard unavailable ({exc}); continuing with standard logging.")

        self._update_registry()

    def _update_registry(self) -> None:
        registry: dict[str, str] = {}
        if self.registry_path.exists():
            try:
                registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
            except Exception:
                registry = {}
        registry[self.run_name] = str(self.run_dir)
        self.registry_path.write_text(
            json.dumps(registry, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def resolve_latest_run_dir(
        cls,
        run_name: str,
        experiments_root: Path | str = "experiments",
    ) -> Path | None:
        safe_name = sanitize_run_name(run_name)
        runs_root = Path(experiments_root).resolve() / "runs"
        reg_path = runs_root / "registry.json"
        if reg_path.exists():
            try:
                reg = json.loads(reg_path.read_text(encoding="utf-8"))
                if safe_name in reg and Path(reg[safe_name]).exists():
                    return Path(reg[safe_name]).resolve()
            except Exception:
                pass
        if not runs_root.exists():
            return None
        candidates = sorted(
            [p for p in runs_root.iterdir() if p.is_dir() and p.name.endswith(f"_{safe_name}")],
            key=lambda p: p.name,
        )
        return candidates[-1].resolve() if candidates else None

    def _rotate_log_if_needed(self) -> None:
        if not self.log_path.exists() or self.log_path.stat().st_size < MAX_LOG_BYTES:
            return
        for idx in range(MAX_LOG_ARCHIVES - 1, 0, -1):
            src = self.logs_dir / f"{self.run_name}.{idx}.log.gz"
            dst = self.logs_dir / f"{self.run_name}.{idx + 1}.log.gz"
            if src.exists():
                shutil.move(str(src), str(dst))
        archive_1 = self.logs_dir / f"{self.run_name}.1.log.gz"
        with self.log_path.open("rb") as f_in, gzip.open(archive_1, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        self.log_path.write_text("", encoding="utf-8")

    def log(self, level: str, message: str, console: bool = True) -> None:
        """Write timestamped [HH:MM:SS] [LEVEL] message to log file and console (§7)."""
        self._rotate_log_if_needed()
        ts = dt.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] [{level.upper()}] {message}"
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        if console:
            print(line, flush=True)

    def info(self, message: str) -> None:
        self.log("INFO", message)

    def warn(self, message: str) -> None:
        self.log("WARN", message)

    def error(self, message: str) -> None:
        self.log("ERROR", message)

    def progress(
        self,
        epoch: int,
        total_epochs: int,
        step: int,
        total_steps: int,
        loss: float,
        reward: float,
        lr: float,
        eta_s: float,
    ) -> None:
        msg = (
            f"Epoch {epoch}/{total_epochs} | Step {step}/{total_steps} | "
            f"loss={loss:.4f} | R_team={reward:.2f} | lr={lr:.2e} | ETA={eta_s:.1f}s"
        )
        self.log("INFO", msg, console=True)

    def save_config(self, config: dict[str, Any]) -> None:
        self.config_path.write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def epoch_summary(self, epoch_row: dict[str, Any]) -> None:
        """Append one JSON line to <run_name>_history.jsonl and log [TRAIN] summary."""
        with self.history_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(epoch_row, ensure_ascii=False) + "\n")

        epoch = epoch_row.get("epoch", 0)
        r_team = epoch_row.get("val_r_team", epoch_row.get("train_r_team", 0.0))
        helped = epoch_row.get("val_patients_helped", 0.0)
        loss = epoch_row.get("train_loss", 0.0)
        self.log(
            "TRAIN",
            f"Epoch {epoch:03d} summary | loss={loss:.4f} | "
            f"train_R_team={epoch_row.get('train_r_team', 0.0):.2f} | "
            f"val_R_team={r_team:.2f} | val_patients_helped={helped:.2f} | "
            f"stage={epoch_row.get('curriculum_stage', 1)}",
        )
        if self._tb_writer is not None:
            for k, v in epoch_row.items():
                if isinstance(v, (int, float)) and k != "epoch":
                    self._tb_writer.add_scalar(k, float(v), int(epoch))
            self._tb_writer.flush()

    def close(self) -> None:
        if self._tb_writer is not None:
            self._tb_writer.close()
            self._tb_writer = None
