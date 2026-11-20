# PROJECT DEMO GUIDE

Demo ~15 phút. Bước **[LAB]** cần máy có Docker + lab images; bước còn lại chạy được trên repo.

## 1. Kiến trúc (2')

Trình bày sơ đồ trong `PROJECT_FINAL_REPORT.md` §5: ScyllaDB 3 node/3 AZ, MongoDB RS, Prometheus/Grafana, chaos_runner, contract v2 → analysis.

## 2. Start infra **[LAB]**

```bash
docker network create --subnet=10.88.88.0/24 lab-net
docker compose -f docker/scylla.yml up -d && docker compose -f docker/mongo.yml up -d
```

## 3. Cluster health **[LAB]**

```bash
docker exec scylla-node1 nodetool status        # 3/3 UN
docker exec mongo1 mongosh --eval 'rs.status().members.map(m=>m.stateStr)'
```

Nói rõ: health gate trong `cap_matrix_e2_e5.py` bắt buộc bước này — run unhealthy sẽ abort và ghi `aborted_unhealthy_cluster` vào manifest.

## 4. Run workload **[LAB]**

```bash
python scripts/e1a_zipf_workload.py --limit 2000     # Schema A, replay access_log chung
python scripts/lwt_experiment.py                      # 50 luồng tranh 1 item → chỉ 1 thắng
```

Mở `experiments/E1a_ScyllaDB/<run_id>/`: show `access_log.csv` (op READ/WRITE, ts epoch ms) + `manifest.json` (git_sha, origin=observed).

## 5. Network partition **[LAB]**

```bash
python scripts/cap_matrix_e2_e5.py --levels QUORUM   # script tu disconnect node3 giua run
# hoac co dieu phoi: ./chaos_runner.py scenarios/e1_hot_partition.json --harness-cmd "..."
```

Chỉ vào `chaos_events.csv` (partition_start/end, ts ms) — nhấn mạnh chaos markers tách khỏi consistency data.

## 6. Recovery **[LAB]**

Script tự heal + `wait_cluster_ready` — show `manifest.extra.post_heal_up_nodes == 3`.

## 7. Logs & provenance

```bash
head -5 experiments/CAP_QUORUM/<run_id>/consistency_log.csv   # READ/WRITE + version
cat experiments/CAP_QUORUM/<run_id>/manifest.json
```

## 8. Analysis pipeline

```bash
python -m src.catalog_analysis.top_partitions --data <run_dir> --out results/demo_tp
python -m src.catalog_analysis.stale_read    --data <cap_run>  --out results/demo_sr
python -m src.catalog_analysis.bootstrap_ci  --data <run_dir> --out results/demo_bc
```

Show `summary.json`: `origin`, `run.consistency: ok`, `failed_ops`, `stale_read_rate_pct`.

## 9. Present results

| Evidence | File/Chart | Kết quả |
|---|---|---|
| CAP availability ONE/QUORUM | `results/committed_runs/charts/cap_success_phases.png` | 100% qua partition ~20s |
| CAP_ALL | cùng chart | gắn nhãn INVALID (setup defect) — **đừng claim là CAP result** |
| E6 failover | `e6_failover_timeline.png` | 0 write loss, spike ~1s khi election |
| LWT | `lwt_outcome.png` | 1/50 winners |
| E1a/E1b | `e1_latency_cdf.png` | label: workloads chưa comparable — rerun v2 |

**Không có máy lab?** Vẫn demo được bước 7–9 bằng data đã commit + `scripts/selftest_contract.py` (gắn nhãn synthetic) chạy qua pipeline Uyên.
