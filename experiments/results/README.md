# Experiment Results Index (5W1H)

## `rl_hospital/` — Hospital Helper Robot PPO Curriculum Training

- **What**: Consolidated training history (`training_history.json`), compressed rollout metrics (`rollout_summary.npz`), and best policy metadata for the `PPOHospitalAgent` (`31-D -> 2-D`) controller.
- **Why**: Train a single hospital helper robot (with shared team reward `R_team` ready for multi-agent expansion) to search for patients, answer questions (`+10`), call medical staff (`+20`), and physically escort elderly patients (`+30`, `2.5 m` tether) to Floor-1 rooms or the Elevator (`thang_may`).
- **Who**: Generated automatically by `python -m src.training.rl_hospital_train` (run `PPOHospital-converged-80ep-full`).
- **Where**: Source run directory `20261023_162628_PPOHospital-converged-80ep-full` under `experiments/runs/`; consolidated artifacts in `experiments/results/rl_hospital/`.
- **When**: Best checkpoint achieved at Epoch `77` (`val_R_team = 103.00`, `val_patients_helped = 4.00`).
- **How**: 2-Stage Curriculum PPO + LiDAR-aware behavior cloning warm-up over the 24 m × 18 m Floor-1 hospital layout with 17-ray 2D LiDAR fan (`200°` FOV, `6.0 m` range).
