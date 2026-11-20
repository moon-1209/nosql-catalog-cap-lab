"""Unit tests for RL Training & Telemetry Dashboard helper functions."""

from pathlib import Path
from src.ui.rl_dashboard import (
    find_existing_runs,
    find_checkpoints_for_run,
    load_history_records,
    generate_metric_plots,
    inspect_run,
    build_dashboard,
)


def test_find_existing_runs_returns_runs():
    runs = find_existing_runs()
    assert isinstance(runs, list)
    assert len(runs) > 0
    # First entry should have label and path
    label, path_str = runs[0]
    assert isinstance(label, str)
    assert Path(path_str).is_dir()


def test_find_checkpoints_for_run():
    runs = find_existing_runs()
    assert len(runs) > 0
    ckpts = find_checkpoints_for_run(runs[0][1])
    assert isinstance(ckpts, list)
    if ckpts:
        lbl, p_str = ckpts[0]
        assert isinstance(lbl, str)
        assert Path(p_str).is_file()


def test_inspect_run_and_generate_plots():
    runs = find_existing_runs()
    assert len(runs) > 0
    target_path = runs[0][1]

    records = load_history_records(target_path)
    assert isinstance(records, list)

    figs = generate_metric_plots(records)
    assert len(figs) == 4
    for fig in figs:
        assert fig is not None

    # Test full inspect_run output
    fig1, fig2, fig3, fig4, ep, r, help_cnt, eta, status, ckpt_upd = inspect_run(target_path)
    assert fig1 is not None
    assert isinstance(ep, str)
    assert isinstance(r, str)
    assert isinstance(status, str)
    assert ckpt_upd is not None


def test_generate_metric_plots_empty_fallback():
    figs = generate_metric_plots([])
    assert len(figs) == 4
    for fig in figs:
        assert fig is not None


def test_build_dashboard_instantiation():
    demo = build_dashboard()
    assert demo is not None
