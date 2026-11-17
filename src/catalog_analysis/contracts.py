"""Shared data-contract helpers for the analysis pipeline.

Contract versions
-----------------
v2 datasets (current seeder output) carry per-operation status columns
``success`` (bool) and ``error`` (nullable str) plus a ``run_id`` column
matching ``manifest.json`` for provenance.

Legacy datasets lack these columns.  They remain readable, are flagged
as ``status_mode == "legacy"`` and must not be silently treated as v2:
``normalize_success`` reports the mode so callers can surface it.

Status semantics
----------------
``success`` parsed values: true/false (case-insensitive) or 1/0.
Any other value is ``unknown`` - never coerced to success.  Unknown
rows are excluded from success denominators AND from failure counts;
they are reported separately so nothing is silently lost.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd

VALID_CONSISTENCY_LEVELS = ("ONE", "QUORUM", "ALL")

_TRUE = {"true", "1"}
_FALSE = {"false", "0"}


def normalize_success(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return (df with canonical `success` column, status metadata).

    Canonical column values: True, False, or NA (unknown status).
    """
    meta = {"status_mode": "ok", "unknown_status": 0}
    df = df.copy()
    if "success" not in df.columns:
        df["success"] = True
        meta["status_mode"] = "legacy"
    else:
        def conv(v):
            if isinstance(v, bool):
                return v
            s = str(v).strip().lower()
            if s in _TRUE:
                return True
            if s in _FALSE:
                return False
            return pd.NA
        s = df["success"].map(conv)
        meta["unknown_status"] = int(s.isna().sum())
        df["success"] = s
    if "error" not in df.columns:
        df["error"] = ""
    else:
        df["error"] = df["error"].fillna("")
    return df, meta


def ok_mask(df: pd.DataFrame) -> pd.Series:
    """Rows explicitly successful (unknown/NA rows are NOT ok)."""
    return df["success"].eq(True)


def fail_mask(df: pd.DataFrame) -> pd.Series:
    """Rows explicitly failed (unknown/NA rows are NOT failures)."""
    return df["success"].eq(False)


def load_manifest(data_dir: Path) -> dict:
    p = data_dir / "manifest.json"
    return json.loads(p.read_text()) if p.exists() else {}


def run_info(data_dir: Path, df: pd.DataFrame) -> dict:
    """Cross-check manifest run_id against the log's run_id column."""
    mid = load_manifest(data_dir).get("run_id")
    lid = str(df["run_id"].iloc[0]) if "run_id" in df.columns and len(df) else None
    if mid is None and lid is None:
        return {"run_id": None, "consistency": "legacy"}
    if lid is None:
        return {"run_id": mid, "consistency": "no-run-column"}
    if mid is None:
        return {"run_id": lid, "consistency": "no-manifest"}
    ok = set(df["run_id"].astype(str).unique()) == {mid}
    return {"run_id": mid, "consistency": "ok" if ok else "mismatch"}


def git_sha(repo_root: Path) -> str | None:
    """Best-effort commit SHA; None when git/worktree is unavailable."""
    try:
        p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root,
                           capture_output=True, text=True, timeout=10)
        return p.stdout.strip() if p.returncode == 0 else None
    except Exception:
        return None
