# PROJECT FINAL REPORT — NoSQL Catalog & CAP Lab

Đồ án Cloud Computing: thiết kế NoSQL catalog + thực nghiệm CAP trên cụm phân tán container.

## 1. Abstract

Dự án xây dựng một lab phân tán hoàn chỉnh: cụm ScyllaDB 3 node (3 rack = 3 AZ), MongoDB replica set 3 member, hạ tầng chaos có điều phối (`chaos_runner`), workload thực nghiệm theo Data Contract v2, và pipeline phân tích thống kê (hot partition, stale read, bootstrap CI). Mọi kết quả đều gắn `run_id` + `manifest.json` provenance và phân biệt rõ `origin: observed` vs `simulated`.

## 2. Problem Statement

- Catalog NoSQL có mô hình dữ liệu theo query: Schema A (partition per category) vs Schema B (bucketing). Câu hỏi: bucketing có phân tán được hot partition không?
- CAP: với RF=3 và network partition 1 node, hành vi availability/staleness ở CL=ONE/QUORUM/ALL ra sao?
- MongoDB RS: mất primary thì service interruption bao lâu?

## 3. Objectives

Đạt được: (i) lab tái lập được bằng Docker; (ii) workload sinh log theo contract chuẩn tiêu thụ được bởi pipeline phân tích; (iii) phân tích có CI và provenance; (iv) bằng chứng thực nghiệm lưu trong `experiments/`.

## 4. Scope và Limitations

- Phạm vi: Docker local, không deploy public cloud (không có yêu cầu rubric nào trong repo xác nhận cần AWS/GCP).
- **CAP_ALL chưa có kết quả hợp lệ** — run 18/11 bị setup defect (xem §9).
- Stale-read rate trên cluster thật: **chưa đo được** (run cũ không ghi version; code đã sửa, chờ rerun).
- Một số số liệu phân tích hiện có là **simulated** (pipeline Uyên, gắn nhãn rõ trong manifest `origin`).

## 5. Cloud Architecture

```
┌────────────────────── lab-net 10.88.88.0/24 ──────────────────────┐
│ scylla-node1 .11 (az1)  scylla-node2 .12 (az2)  scylla-node3 .13  │
│                       (az3)  + node4 scale-out                  │
│ mongo1 .31  mongo2 .32  mongo3 .33   (RS rs0)                    │
│ cadvisor ──► prometheus ──► grafana                              │
└──────────────────────────────────────────────────────────────────┘
   workload scripts (feat/Duy)  ──CQL/Mongo──►  clusters
   chaos_runner / chaos.sh (feat/Lam) ──docker network──► partition
   experiments/<exp>/<run_id>/ ──CSV v2──► src/catalog_analysis/*
```

## 6. Database & Storage Design

- ScyllaDB: keyspace `catalog`, NTS `datacenter1` RF=3 (đã chuyển từ SimpleStrategy — khớp rack/AZ).
- MongoDB: RS `rs0`, 3 member, dùng cho E6 failover + so sánh mô hình.
- Monitoring: Prometheus scrape Scylla metrics, cAdvisor container metrics, Grafana dashboard `nosql-cap-lab.json`.

## 7. Data Model & Partition Strategy

| Schema | Primary key | Mục đích |
|---|---|---|
| `products_by_id` | `(product_id)` | point lookup (chung A/B) |
| A: `products_by_category` | `((category_id), added_at, product_id)` | 1 partition/category — hot khi category hot |
| B: `products_bucketed` | `((category_id, bucket), added_at, product_id)` | `bucket=crc32(product_id)%16` — fan-out 16 partitions/category |

Dataset chung: `data/sample/products.csv` — 5.000 products, 20 categories, uuid `product_id` (nguồn: seeder Uyên, origin=simulated).

## 8. Experiment Methodology

- Workload replay `access_log.csv` của seeder → cùng 1 chuỗi ops cho A và B (comparable 1-1).
- Mỗi run: `run_id`, `access_log.csv` (op READ/WRITE, ts epoch ms, success, error), `consistency_log.csv` (READ/WRITE + version), `chaos_events.csv` (partition/failover markers), `manifest.json` (git_sha, config, op_count, origin).
- Health gate trước CAP: verify đủ node UP + probe op ở CL đang test; abort → ghi `aborted_unhealthy_cluster` trong manifest (không bao giờ coi setup failure là CAP result).
- Chaos: `--external-chaos` cho phép `chaos_runner --harness-cmd` điều phối partition (tránh 2 implementation Docker control).

## 9. CAP & Consistency Analysis — real evidence (run 18/11, legacy contract)

| CL | Run ID | Pre | Partition (~20s) | Post | Kết luận |
|---|---|---|---|---|---|
| ONE | `20261118164217_51d70a18` | 430 ops 100% | 2858 ops 100% | 720 ops 100% | Availability giữ nguyên khi 1/3 node bị cô lập |
| QUORUM | `20261118164246_1e06bf4f` | 408 ops 100% | 2812 ops 100% | 696 ops 100% | QUORUM=2 vẫn đủ 2 node |
| ALL | `20261118164314_7e93eceb` | 444 ops **0%** | 2984 ops 0% | 730 ops 0% | **RUN INVALID** — fail cả khi healthy → setup defect (translator + node3 chưa rejoin), KHÔNG phải bằng chứng "ALL mất availability" |

- Latency healthy: ONE p50=1.43ms p95=2.71ms; QUORUM p50=1.54ms p95=2.91ms (n≈4000 mỗi CL).
- ONE/QUORUM giữ availability trong partition — **phù hợp lý thuyết** với 2/3 replica còn lại.
- CAP_ALL cần rerun với code đã sửa (health gate + heal-wait) — kỳ vọng kiểm chứng: partition ops fail có điều kiện, healthy ops >90%.

## 10. Schema A/B Benchmark

Run 18/11 (legacy, workload chưa comparable):
- E1a (schema A, zipf keys): 1000 ops, 0 fail — `20261118163502_71591fb6`.
- E1b (schema B cũ, sequential keys): 1000 ops, 0 fail — `20261118163826_70a13d55`.
- Latency CDF: `results/committed_runs/charts/e1_latency_cdf.png` — **ghi chú bắt buộc: 2 run dùng workload khác nhau nên KHÔNG kết luận A vs B được**; rerun v2 (cùng replay ops) sẽ cho số liệu so sánh hợp lệ.
- Simulated baseline (Uyên, origin=simulated): Schema A top share 35.4%, max/mean 7.08; Schema B top share 3.0%, max/mean 9.43 → dự đoán bucketing giảm peak load ~12×.

## 11. MongoDB Failover — real evidence

| Run | Ops | Fail | Latency | Quan sát |
|---|---|---|---|---|
| `20261118165408_3b2facb5` | 228 | 0 | mean 3.72ms | stepdown 10s — không mất write, driver election trong suốt |
| `20261118165508_a46786bb` | 207 | 0 | p95 6.6ms, max **1018ms** | cùng run — spike ~1s đúng cửa sổ bầu primary |

Timeline chart: `results/committed_runs/charts/e6_failover_timeline.png`. Kết luận: RS duy trì write availability qua failover, đổi lấy latency spike ≤ ~1s trong cửa sổ election (ở mức tải thấp 20 ops/s).

## 12. Chaos Testing

- `chaos/chaos.sh` (feat/Lam): disconnect/connect từng node; `chaos_runner.py` chạy scenario JSON có timeline, snapshot, phase marks.
- `scenarios/e1_hot_partition.json`: warm-up 60s, đo 240s, chụp `nodetool toppartitions` giây 120.
- `cap_matrix_e2_e5.py --external-chaos` đã tích hợp để chạy dưới `--harness-cmd` của chaos_runner.

## 13. Results & Visualizations

| Chart | Nguồn |
|---|---|
| `results/committed_runs/charts/cap_success_phases.png` | 3 CAP run thật 18/11 |
| `e1_latency_cdf.png` | E1a/E1b run thật (label: workloads not comparable) |
| `e6_failover_timeline.png` | E6 run `a46786bb` |
| `lwt_outcome.png` | LWT run `d623b720`: **1/50 thắng** — đúng CAS, 0 oversell |

Tất cả chart ghi rõ run_id và trạng thái dữ liệu; không chart nào dùng run invalid mà không gắn nhãn.

## 14. Security & Operational

- `.env`/`docker/.env` đã untrack + `.gitignore` + `.env.example` (nội dung chỉ là lab config, không secret — verify trực tiếp).
- DB không auth trong lab (developer mode) — **limitation**, phải nêu khi deploy thật.
- Network: `lab-net` isolated subnet; host chỉ publish 9042/27017 qua translator — dev-only.
- Backup/recovery: **không có implementation** — documented design: `nodetool snapshot` cho Scylla, `mongodump` cho RS; chưa test.
- Monitoring: Prometheus + Grafana sẵn sàng quan sát node health/latency/failure/recovery/resource.

## 15. Limitations

1. CAP_ALL + stale-read real: BLOCKED chờ rerun trên máy có Docker.
2. E1a/E1b real comparison: workload cũ không comparable — chờ rerun contract v2.
3. Backup/restore: design-only, chưa test.
4. Không rubric môn học trong repo → scope "cloud" giới hạn Docker local.
5. Một phần số liệu là simulated — luôn đọc `manifest.origin` trước khi trích dẫn.

## 16. Conclusion & Future Work

Kiến trúc lab hoàn chỉnh về mặt code và contract; bằng chứng thật đã có cho CAP-availability (ONE/QUORUM), failover, LWT, Counter. Còn thiếu: rerun CAP_ALL/stale-read/E1-comparable trên cluster, merge 3 nhánh, test backup. Khi các bước này xong, project đạt trạng thái end-to-end reproducible.
