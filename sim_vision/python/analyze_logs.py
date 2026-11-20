"""Phân tích log (G10): tỉ lệ thành công, thời gian trung bình, biểu đồ h theo true_distance_m.

Chạy: python analyze_logs.py [--logs ../logs] [--out ../logs/h_vs_distance.png]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

DEFAULT_LOGS: Path = Path(__file__).resolve().parent.parent / "logs"


def summarize_batch(df: pd.DataFrame) -> dict[str, float]:
    """Tóm tắt batch_summary.csv."""
    ok = df[df["success"]]
    return {
        "runs": len(df),
        "successes": len(ok),
        "success_rate": len(ok) / len(df) if len(df) else 0.0,
        "mean_time_to_arrive_s": float(ok["time_to_arrive_s"].mean()) if len(ok) else float("nan"),
        "total_collisions": int(df["collisions"].sum()),
        "mean_infer_ms": float(df["mean_infer_ms"].mean()) if len(df) else float("nan"),
    }


def load_runs(logs_dir: Path) -> pd.DataFrame:
    """Gộp mọi logs/run_*.csv, thêm cột `run` (tên file)."""
    frames = [pd.read_csv(p).assign(run=p.stem) for p in sorted(logs_dir.glob("run_*.csv"))]
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def plot_h_vs_distance(runs: pd.DataFrame, out: Path) -> int:
    """Vẽ h theo true_distance_m (chỉ các dòng có detection). Trả số điểm đã vẽ."""
    pts = runs.dropna(subset=["h", "true_distance_m"]) if not runs.empty else runs
    fig, ax = plt.subplots(figsize=(7, 4.5))
    if not pts.empty:
        ax.scatter(pts["true_distance_m"], pts["h"], s=8, alpha=0.5)
    ax.set_xlabel("true_distance_m (m)")
    ax.set_ylabel("h (chiều cao box / chiều cao ảnh)")
    ax.set_title("h theo khoảng cách thật")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return len(pts)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--logs", type=Path, default=DEFAULT_LOGS)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    out: Path = args.out or args.logs / "h_vs_distance.png"

    summary_csv = args.logs / "batch_summary.csv"
    if summary_csv.exists():
        s = summarize_batch(pd.read_csv(summary_csv))
        print(f"batch: {s['successes']}/{s['runs']} thành công ({s['success_rate']:.0%})")
        print(f"thời gian tới đích trung bình (lượt thành công): {s['mean_time_to_arrive_s']:.2f} s")
        print(f"tổng va chạm với người: {s['total_collisions']}")
        print(f"infer_ms trung bình: {s['mean_infer_ms']:.1f} ms")
    else:
        print(f"không có {summary_csv} (chạy tools/batch_run.tscn trước)")

    runs = load_runs(args.logs)
    n = plot_h_vs_distance(runs, out)
    n_runs = runs["run"].nunique() if not runs.empty else 0
    print(f"biểu đồ h theo true_distance_m: {n} điểm từ {n_runs} file run ➔ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
