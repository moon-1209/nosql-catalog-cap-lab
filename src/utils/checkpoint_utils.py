"""Full-state checkpointing utilities implementing LOGGING_CHECKPOINT_RULES.md (§3, §5).

Every checkpoint is a single `torch.save` dict loadable with `weights_only=True`:
- model_state_dict
- optimizer_state_dict
- scheduler_state_dict
- epoch
- global_step
- best_val_loss
- best_val_acc
- best_epoch
- early_stop_triggered
- history
- config
- rng (JSON-safe hex strings for torch CPU/GPU, numpy, python random)
- timestamp (ISO-8601)
- commit (git HEAD sha, best-effort)
"""

from __future__ import annotations

import datetime as dt
import pickle
import random
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import torch


def get_git_commit() -> str:
    """Return current git HEAD commit hash (best-effort)."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2.0,
        )
        return out.strip()
    except Exception:
        return "unknown"


def capture_rng_state(seed: int) -> dict[str, Any]:
    """Serialize torch (CPU/GPU), numpy, and python RNG states as JSON-safe hex strings."""
    torch_cpu_hex = torch.get_rng_state().numpy().tobytes().hex()
    torch_cuda_hex: list[str] = []
    if torch.cuda.is_available():
        try:
            for state in torch.cuda.get_rng_state_all():
                torch_cuda_hex.append(state.cpu().numpy().tobytes().hex())
        except Exception:
            pass
    np_state_hex = pickle.dumps(np.random.get_state()).hex()
    py_state_hex = pickle.dumps(random.getstate()).hex()
    return {
        "seed": int(seed),
        "torch_cpu": torch_cpu_hex,
        "torch_cuda": torch_cuda_hex,
        "numpy": np_state_hex,
        "python": py_state_hex,
    }


def restore_rng_state(rng_dict: dict[str, Any]) -> None:
    """Restore torch (CPU/GPU), numpy, and python RNG states from hex strings."""
    if not rng_dict:
        return
    try:
        if "torch_cpu" in rng_dict and rng_dict["torch_cpu"]:
            raw = bytes.fromhex(rng_dict["torch_cpu"])
            tensor = torch.frombuffer(bytearray(raw), dtype=torch.uint8)
            torch.set_rng_state(tensor)
        if torch.cuda.is_available() and rng_dict.get("torch_cuda"):
            states = []
            for h in rng_dict["torch_cuda"]:
                raw = bytes.fromhex(h)
                states.append(torch.frombuffer(bytearray(raw), dtype=torch.uint8))
            torch.cuda.set_rng_state_all(states)
        if "numpy" in rng_dict and rng_dict["numpy"]:
            np.random.set_state(pickle.loads(bytes.fromhex(rng_dict["numpy"])))
        if "python" in rng_dict and rng_dict["python"]:
            random.setstate(pickle.loads(bytes.fromhex(rng_dict["python"])))
    except Exception:
        pass


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def save_checkpoint(
    path: Path | str,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: Any | None,
    epoch: int,
    global_step: int,
    best_val_loss: float,
    best_val_acc: float,
    best_epoch: int,
    early_stop_triggered: bool,
    history: dict[str, list[Any]],
    config: dict[str, Any],
    seed: int,
) -> Path:
    """Save full-state checkpoint compatible with torch.load(..., weights_only=True)."""
    ckpt_path = Path(path)
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict() if scheduler is not None else {},
        "epoch": int(epoch),
        "global_step": int(global_step),
        "best_val_loss": float(best_val_loss),
        "best_val_acc": float(best_val_acc),
        "best_epoch": int(best_epoch),
        "early_stop_triggered": bool(early_stop_triggered),
        "history": history,
        "config": config,
        "rng": capture_rng_state(seed),
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "commit": get_git_commit(),
    }
    torch.save(payload, ckpt_path)
    return ckpt_path


def load_checkpoint(
    path: Path | str,
    model: torch.nn.Module | None = None,
    optimizer: torch.optim.Optimizer | None = None,
    scheduler: Any | None = None,
    restore_rng: bool = True,
    map_location: str | torch.device = "cpu",
) -> dict[str, Any]:
    """Load checkpoint safely with weights_only=True and restore states in §5 order."""
    ckpt_path = Path(path)
    ckpt: dict[str, Any] = torch.load(ckpt_path, map_location=map_location, weights_only=True)
    if model is not None and "model_state_dict" in ckpt:
        model.load_state_dict(ckpt["model_state_dict"])
    if optimizer is not None and ckpt.get("optimizer_state_dict"):
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
    if scheduler is not None and ckpt.get("scheduler_state_dict"):
        scheduler.load_state_dict(ckpt["scheduler_state_dict"])
    if restore_rng and "rng" in ckpt:
        restore_rng_state(ckpt["rng"])
    return ckpt
