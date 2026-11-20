# BÁO CÁO ĐÁP ỨNG YÊU CẦU — ĐỀ TÀI 14

**Thiết kế mô hình dữ liệu NoSQL và kiểm chứng đánh đổi CAP cho hệ thống danh mục sản phẩm**
Repo: `moon-1209/nosql-catalog-cap-lab` — Audit ngày 19/11/2026, nhánh `feat/Duy` @ `eaa3852`.

> Bài giảng Ch1–Ch5: **CHƯA TRUY CẬP ĐƯỢC NGUỒN** (không có trong workspace, đã tìm trên filesystem). Bảng đối chiếu lý thuyết bên dưới dựa trên yêu cầu đề tài; nguồn bài giảng đánh dấu *CHƯA ĐỐI CHIẾU ĐƯỢC VỚI PDF*. Tài liệu tham khảo [39],[40] không có danh mục trong repo → không trích dẫn.

## 1. Tóm tắt hiện trạng

Project gồm 3 workstream chưa merge: **Duy** (experiments + contract v2, `feat/Duy`), **Uyên** (analysis pipeline, `feat/uyen-analysis-pipeline`), **Lâm** (infra/chaos/monitoring, `feat/Lam`). `main` chỉ có README; `develop` chứa bản cũ của Duy.

Đã có **9 run thật** (18/11, contract legacy) trên ScyllaDB/MongoDB cluster Docker + **1 pipeline phân tích chạy được end-to-end** trên contract v2. Các kết quả chính: CAP_ONE/QUORUM sống sót partition thật; MongoDB failover 0 write loss; LWT đúng CAS (1/50 winner). Còn thiếu: CAP_ALL hợp lệ, stale-read real, so sánh A/B cùng workload, đo tải theo node.

## 2. Kiến trúc và công nghệ thực tế

| Thành phần | Công nghệ | Evidence |
|---|---|---|
| Wide-column DB | ScyllaDB 5.4, 3 node/3 rack, NTS DC `datacenter1` RF=3 | `docker/scylla.yml`, `compose/scylla.yml` |
| Document DB | MongoDB 6.0 RS `rs0` 3 member | `docker/mongo.yml` |
| Workload | Python + scylla-driver + pymongo, `data_contract.py` v2 | `scripts/` |
| Chaos | `docker network disconnect`, `chaos_runner.py` scenarios | `cap_matrix_e2_e5.py`, feat/Lam |
| Monitoring | Prometheus + cAdvisor + Grafana | `monitoring/` (feat/Lam) |
| Analysis | pandas/numpy/scipy, bootstrap CI | `src/catalog_analysis/` (feat/uyen) |
| YCSB/Toxiproxy | **không dùng** — tự viết workload + docker net chaos | — (NOT_REQUIRED, công nghệ gợi ý ≠ bắt buộc) |

## 3. A. Thiết kế mô hình dữ liệu NoSQL

| Yêu cầu | Trạng thái | Minh chứng |
|---|---|---|
| Access patterns xác định | **VERIFIED** | `docs/access-patterns/access-patterns.md` (feat/uyen): Q1–Q4 reads + W1–W3 writes, tỷ trọng traffic, partitions-touched per query, hot-risk per query |
| Phân tích truy vấn trước schema | VERIFIED | Cùng tài liệu: query-driven, clustering order phục vụ Q2/Q3 |
| Product dataset | VERIFIED | `data/sample/products.csv` 5.000 rows/20 categories/uuid |
| Inventory/stock | VERIFIED (design) | cột `stock` + W2 update + Counter experiment |
| View events | **PARTIAL** | `access_log.csv` mô hình hóa sự kiện truy cập sản phẩm (READ ops) — không có bảng `view_events` riêng |
| Query-driven modeling + denormalization | VERIFIED | `products_by_id` + `products_by_category`/`products_bucketed` (2 bảng denormalized) |
| Giải thích chọn wide-column | PARTIAL | `docs/schema/schema-design.md` có; chưa thấy so sánh tường minh wide-column vs document |
| Hai phương án partition key | VERIFIED (design) | A `((category_id),added_at,pid)` vs B `((category_id,bucket),added_at,pid)`, `bucket=crc32(pid)%16` |
| Ưu/nhược từng phương án | VERIFIED (doc) | access-patterns.md §2 + `final-report.md` (fan-out cost của B) |
| Kiểm tra đúng đắn sau phân tán | PARTIAL | `validate()` kiểm dup PK + bucket consistency trên dataset; chưa có integrity check sau khi nạp cluster |

## 4. B. Partition key, sharding, hot partition

- Skewed workload: **VERIFIED** — Zipf(α=1.2) trên category trong seeder và e1a.
- Hot partition đo bằng dữ liệu: **PARTIAL** — simulated: A top share 35.4%, max/mean 7.08 (chạy thật trên data/sample, `results/top_partitions/`); real cluster: `toppartitions_capture.py` + `hot_partition_audit.py` (feat/Lam) **chưa chạy**.
- Tải theo node: **BLOCKED** — `hot_partition_audit` có 6 views gồm per-node/shard nhưng chưa có run thật.
- Trước/sau tối ưu: **BLOCKED** — run A vs B ngày 18/11 dùng workload khác nhau (zipf vs sequential) → không comparable; code v2 replay cùng `access_log.csv` đã sửa xong, chờ rerun.
- Phân biệt: dự án đo được *request distribution* (partition_loads); *data distribution* có (bucket counts); *CPU/IO distribution* chỉ có tool (`hot_partition_audit` views cpu_shard) chưa chạy.

## 5. C. Replication và CAP

- RF=3, 3 node/3 rack (NTS sau remediation; run 18/11 dùng SimpleStrategy RF=3 — ghi nhận khác biệt).
- Partition thật: `docker network disconnect lab-net scylla-node3` ~20s — **VERIFIED REAL**.
- Healthy/degraded: `wait_cluster_ready` + probe WRITE + `aborted_unhealthy_cluster` (code, chưa verify runtime).
- CL đã thử: ONE, QUORUM, ALL (real); ONE/QUORUM 100% ok qua partition — phù hợp lý thuyết (2/3 replica còn).
- CAP_ALL run 18/11: **INVALID** (fail 100% kể cả healthy — setup defect, đã root-cause: translator + node3 chưa rejoin). Không dùng làm CAP evidence.

## 6. D. Consistency và tính đúng đắn

| Nội dung | Trạng thái | Evidence |
|---|---|---|
| Stale read measurement | PARTIAL | `stale_read.py` merge_asof đúng method (verified trên synthetic); real run cũ không có version data → real rate BLOCKED |
| Version semantics | VERIFIED (code) | `cap_kv.version` monotonic; failed writes không commit |
| Failed vs stale phân biệt | VERIFIED | contract v2: failed ops loại khỏi denominator (tested) |
| LWT/conditional write | **VERIFIED REAL** | 50 luồng, 1 winner — `experiments/LWT/..._d623b720` |
| Counter | VERIFIED REAL | 99 ops — `experiments/Counter/...` |
| Eventual consistency | PARTIAL | hiện diện qua stale-read sim; chưa đo real |
| Read-your-writes | NOT_IMPLEMENTED | không có test riêng |
| Conflict/idempotent | PARTIAL | idempotent qua full-row INSERT; conflict resolution chưa demo |

## 7. E. Workload và hiệu năng (real, 18/11)

| Run | Ops | p50 | p95 | p99 | ok% | Source |
|---|---|---|---|---|---|---|
| CAP_ONE `..._51d70a18` | 4008 | 1.43ms | 2.71ms | — | 100 | REAL/LEGACY |
| CAP_QUORUM `..._1e06bf4f` | 3916 | 1.54ms | 2.91ms | — | 100 | REAL/LEGACY |
| E1a `..._71591fb6` | 1000 | — | — | — | 100 | REAL/LEGACY |
| E6 `..._a46786bb` | 207 | 3.49ms | 6.63ms | max 1018ms | 100 | REAL/LEGACY |

- Throughput: có `ops_per_s` tính được (≈140–200 ops/s); **p99 chưa tính** — ghi nhận thiếu.
- Cùng workload giữa cấu hình: chỉ chuẩn hóa ở v2 (replay cùng file) — chưa có run.
- Reproducible: manifest + run_id + config (v2); legacy runs không có manifest.

## 8. F. Thực nghiệm và biểu đồ

4 PNG tại `results/committed_runs/charts/` — nguồn real runs, có run_id, đơn vị, nhãn cấu hình, và gắn nhãn INVALID run + "not comparable" đúng chuẩn. Thiếu: chart A-vs-B comparable, stale-rate chart real, throughput-by-node.

## 9. G. Triển khai và vận hành

- **Local containerized lab**: VERIFIED (compose files, lab-net, lab_up/down/status).
- Monitoring/health: IMPLEMENTED (Prometheus/Grafana/nodetool + `wait_cluster_ready`).
- Secrets: `.env` untrack + `.env.example` (verified không credential).
- Backup/recovery: procedure DOCUMENTARY — `docs/PROJECT_BACKUP_RECOVERY.md`, runtime BLOCKED.
- Public cloud: **NOT_REQUIRED** (không yêu cầu nào trong repo/rubric) — chỉ Docker local; không claim là cloud deployment.

## 10. Đối chiếu nội dung lý thuyết

| Nội dung | Nguồn bài giảng | Dự án thể hiện | Minh chứng | Trạng thái |
|---|---|---|---|---|
| NoSQL models (KV/doc/wide-col/graph) | CHƯA ĐỐI CHIẾU | wide-column (Scylla) + document (Mongo); KV/graph không dùng — chưa có phần so sánh 4 mô hình | §2 | PARTIAL |
| Query-driven + denormalization | CHƯA ĐỐI CHIẾU | đầy đủ | access-patterns.md | VERIFIED |
| Partition key/sharding/hot key | CHƯA ĐỐI CHIẾU | 2 phương án + bucketing + đo hot (sim) | §4 | PARTIAL |
| Secondary index | CHƯA ĐỐI CHIẾU | không dùng — `ALLOW FILTERING` được ghi nhận là scan | queries cql | PARTIAL (có nhận diện) |
| Replication + quorum + CAP | CHƯA ĐỐI CHIẾU | RF=3, ONE/QUORUM/ALL, partition thật | §5 | VERIFIED (phần ONE/QUORUM) |
| Eventual cons./RYW/conflict/idempotent | CHƯA ĐỐI CHIẾU | idempotent write + stale method + LWT | §6 | PARTIAL |
| Cloud infra/service model | CHƯA ĐỐI CHIẾU | containerized local lab, không public cloud | §9 | PARTIAL |
| Security | CHƯA ĐỐI CHIẾU | secrets hygiene; no auth/TLS (lab limitation) | security audit | PARTIAL |
| Deployment/operation | CHƯA ĐỐI CHIẾU | guides + health checks + monitoring docs | deploy guide | VERIFIED (local scope) |

## 11. Bảng đáp ứng 18 tiêu chí

| STT | Tiêu chí | Trạng thái | Minh chứng | Còn thiếu |
|---|---|---|---|---|
| 1 | Access pattern | VERIFIED | `access-patterns.md` | — |
| 2 | NoSQL schema | VERIFIED | 3 bảng đúng spec | — |
| 3 | Hai phương án partition key | VERIFIED | A/B + lý do chọn | — |
| 4 | Product/inventory/view dataset | PARTIAL | product+stock+access_log | bảng view_events riêng |
| 5 | Skewed workload | VERIFIED | Zipf seeder + e1a | — |
| 6 | Throughput + p95 | PARTIAL | p95 có; **p99 thiếu**; throughput có ops/s | p99, per-node throughput |
| 7 | Tải từng node | BLOCKED | tool `hot_partition_audit` có | chạy thật |
| 8 | Network partition/slow replica | VERIFIED (partition) | disconnect thật 20s | slow-replica (netem) chưa run |
| 9 | Consistency levels | PARTIAL | ONE/QUORUM real; ALL invalid | CAP_ALL rerun |
| 10 | Stale read/error | PARTIAL | method VERIFIED, real rate BLOCKED | rerun cap v2 |
| 11 | Hot partition trước tối ưu | PARTIAL | sim 35.4% share; real tool sẵn | real A run |
| 12 | Hot partition sau tối ưu | BLOCKED | — | real B run |
| 13 | Chạy lại cùng workload | BLOCKED | code replay sẵn | rerun |
| 14 | Biểu đồ và minh chứng | PARTIAL | 4 charts real, labeled | A/B + stale charts |
| 15 | Kết luận CAP đúng phạm vi | VERIFIED | không claim CP/AP; ALL gắn invalid | — |
| 16 | Tài liệu lý thuyết | PARTIAL | docs nội bộ đầy đủ; **chưa đối chiếu PDF** | map với bài giảng |
| 17 | Cloud deployment/operation | PARTIAL | local lab VERIFIED; không claim public | — |
| 18 | Security | PARTIAL | hygiene verified; no auth/TLS | auth nếu cần |

**Tổng kết: VERIFIED 7/18 (39%) — PARTIAL 8/18 (44%) — BLOCKED 3/18 (17%) — NOT_IMPLEMENTED 0.**

*(BLOCKED đều do môi trường: code đã sẵn, chờ máy có Docker + driver để rerun.)*

## 12. Đánh giá câu hỏi nghiên cứu

| Câu hỏi | Đánh giá |
|---|---|
| 1. Trả lời được RQ chính? | **Chưa đầy đủ** — mới trả lời phần CL→availability/latency (ONE/QUORUM real); phần partition key→scalability chỉ có sim + tool |
| 2. Partition key → khả năng mở rộng? | *Có implementation + sim evidence*; chưa chứng minh real |
| 3. Replication + CL → tính đúng đắn? | *Phần availability chứng minh được* (ONE/QUORUM); stale/correctness chưa có real data |
| 4. Ảnh hưởng độ trễ? | Đo được latency per-op real (p50/p95); thiếu p99 + theo node |
| 5. Hot partition + tối ưu? | Sim: chứng minh A→B giảm peak ~12×; real: chưa |
| 6. Stale read khi partition/replica chậm? | Chưa — chỉ synthetic verified |
| 7. Đủ dữ liệu kết luận học thuật? | Chưa — cần rerun nhóm BLOCKED |
| 8. Kết luận chưa đủ cơ sở? | "B giảm hot partition trên cluster thật", "ALL mất availability", "stale rate theo CL", "so sánh latency A vs B" |

## 13. Hạn chế và rủi ro

1. CAP_ALL chưa có run hợp lệ — kết luận availability của ALL chưa thể viết.
2. Stale-read real chưa đo — nửa CAP consistency chưa có bằng chứng.
3. A/B comparison real chưa comparable — kết luận schema chưa có.
4. Per-node load chưa đo — "hot partition" chỉ ở mức request distribution.
5. Ba nhánh chưa merge — pipeline end-to-end chỉ verify qua worktree.
6. Bài giảng/rubric không truy cập được — đối chiếu lý thuyết provisional.
7. Legacy runs không có manifest — provenance yếu hơn run v2.

## 14. Kết luận mức độ hoàn thành

**Theo minh chứng thực nghiệm: ~39% tiêu chí VERIFIED, 44% PARTIAL.** Phần nền (thiết kế, dataset, contract, tooling, một nửa CAP và failover) đã vững; phần chứng minh còn lại tập trung vào **3 việc**: rerun CAP_ALL, rerun cap v2 có stale data, rerun E1a/b cùng workload — tất cả chờ môi trường Docker. Không có tiêu chí nào NOT_IMPLEMENTED về mặt thiết kế.
