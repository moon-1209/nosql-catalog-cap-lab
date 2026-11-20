from __future__ import annotations

from pathlib import Path

import pandas as pd

from analyze_logs import load_runs, main, plot_h_vs_distance, summarize_batch

RUN_HEADER = "time_s,frame_id,state,n_det,conf,cx,h,true_distance_m,true_angle_deg,v,omega,infer_ms,connected\n"


def _write_logs(d: Path) -> None:
    (d / "batch_summary.csv").write_text(
        "seed,success,time_to_arrive_s,final_distance_m,collisions,frames,mean_infer_ms\n"
        "0,true,10.0000,1.4000,0,50,30.0000\n"
        "1,true,20.0000,1.2000,0,90,40.0000\n"
        "2,false,,2.5000,0,150,35.0000\n")
    (d / "run_20261021_000001.csv").write_text(
        RUN_HEADER
        + "0.2000,0,SEARCH,0,,,,4.0000,10.0000,0.0000,0.5000,30.0000,true\n"
        + "0.4000,1,APPROACH,1,0.9000,0.5000,0.4000,3.0000,0.0000,0.6000,0.0000,30.0000,true\n")
    (d / "run_20261021_000002.csv").write_text(
        RUN_HEADER + "0.2000,0,APPROACH,1,0.9000,0.5000,0.8000,1.5000,0.0000,0.1000,0.0000,30.0000,true\n")


def test_summarize_batch(tmp_path: Path) -> None:
    _write_logs(tmp_path)
    s = summarize_batch(pd.read_csv(tmp_path / "batch_summary.csv"))
    assert s["runs"] == 3 and s["successes"] == 2
    assert abs(s["success_rate"] - 2 / 3) < 1e-9
    assert s["mean_time_to_arrive_s"] == 15.0
    assert s["total_collisions"] == 0
    assert s["mean_infer_ms"] == 35.0


def test_load_runs_and_plot(tmp_path: Path) -> None:
    _write_logs(tmp_path)
    runs = load_runs(tmp_path)
    assert len(runs) == 3 and runs["run"].nunique() == 2
    out = tmp_path / "plot.png"
    assert plot_h_vs_distance(runs, out) == 2  # chỉ dòng có h
    assert out.stat().st_size > 0


def test_main_without_logs(tmp_path: Path, capsys) -> None:
    assert main(["--logs", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "không có" in out and "0 điểm" in out
    assert (tmp_path / "h_vs_distance.png").exists()


def test_main_prints_summary(tmp_path: Path, capsys) -> None:
    _write_logs(tmp_path)
    assert main(["--logs", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "2/3" in out and "15.00 s" in out
