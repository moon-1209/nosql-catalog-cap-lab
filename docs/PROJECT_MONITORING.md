# MONITORING & OBSERVABILITY

## 1. Hai lớp metrics — phân biệt rõ

| Lớp | Nguồn | Nằm ở | Dùng cho |
|---|---|---|---|
| **Experiment metrics** | `access_log`, `consistency_log`, `chaos_events`, `manifest.json` | `experiments/<EXP>/<run_id>/` | phân tích CAP/stale/latency (Uyên) |
| **Infrastructure metrics** | Prometheus scrape + cAdvisor + nodetool | `monitoring/` (feat/Lam) | health, resource, recovery của cluster |

## 2. Có thể quan sát gì

| Metric | Thu thập | Trạng thái |
|---|---|---|
| Node health (UN/DN) | `nodetool status`, `scripts/lab_status.sh`, `wait_cluster_ready` trong cap_matrix | IMPLEMENTED |
| Per-node/shard load | `hot_partition_audit.py` — PromQL `scylla_*` metrics, 6 views (intra_node_shard, cluster_shard, node, node_normalized, coordinator, cpu_shard) | IMPLEMENTED (feat/Lam) |
| Top partitions | `toppartitions_capture.py` — `nodetool toppartitions` song song mọi node | IMPLEMENTED |
| CPU/memory container | cAdvisor `compose/cadvisor.yml` → Prometheus | IMPLEMENTED |
| Latency/throughput ops | `latency_ms` per-op trong access_log; p50/p95/max qua `analyze_committed_runs.py` | VERIFIED (real run 18/11) |
| Failed ops | `success`/`error` columns + `failed_ops` trong summary | VERIFIED |
| Chaos events + recovery | `chaos_events.csv` + `manifest.extra.post_heal_up_nodes` | IMPLEMENTED |
| Grafana dashboard | `monitoring/nosql-cap-lab.json` | IMPLEMENTED |

## 3. Collection flow

```
Scylla nodes :9180 ─┐
cAdvisor :8080 ─────┼─► Prometheus (extra targets: monitoring/*_targets.yml) ─► Grafana
node exporter      ─┘
hot_partition_audit ──PromQL──► Prometheus API ──► CSV/JSON ──► Uyên charts
```

## 4. Operational troubleshooting

| Vấn đề | Kiểm tra | Lệnh |
|---|---|---|
| Node không UN | cluster membership | `docker exec scylla-node1 nodetool status` |
| Tải lệch | shard/node views | `hot_partition_audit.py --last 10m` |
| Partition hot nhất | sampler thật | `toppartitions_capture.py --ks catalog --cf products_by_category --duration-ms 30000` |
| Client-side lỗi | coordinator view | audit view `coordinator` — nếu lệch → driver không token-aware |
| Recovery chậm | post-heal nodes | `manifest.extra.post_heal_up_nodes` trong run dir |

## 5. Limitations

- Prometheus/Grafana stack nằm trên `feat/Lam`, chưa merge — trên `feat/Duy` chỉ có `docker/cadvisor.yml` (không kèm prometheus config).
- `toppartitions` là sampler gần đúng (~cardinality), không phải count chính xác — docstring của Lâm đã ghi rõ.
- Không alerting rules, không log aggregation (container logs xem bằng `docker logs`).
