# nosql-catalog-cap-lab — Đề tài 14

Research lab on NoSQL (ScyllaDB + MongoDB), the CAP theorem, data partitioning,
consistency levels and hot partitions for a product-catalog workload.

Đồ án môn học Cloud Computing — tích hợp toàn bộ ba phần của nhóm trên nhánh
`feat/uyen-analysis-pipeline`.

## Repository layout (unified)

| Path | Owner | Contents |
|---|---|---|
| `docs/markdown/` | All | **Centralized docs**: `architecture/` (schema, access patterns, data dict), `implementation/` (Uyên+Duy impl reports), `experiments/` (run analysis outputs), `reports/` (final/slides/qa/MR), `testing/` (acceptance checklist), `deployment/` (deploy/backup/monitoring/security/demo), `project-management/` (audits, handover, compliance, remaining work). Non-md assets (`access-patterns/*.cql`, `schema/chebotko/*.svg`) stay in place |
| `src/catalog_analysis/` | Uyên | Seeder and analysis modules (hot partition, stale read, bootstrap CI) |
| `scripts/` | Duy + Lâm | Experiment scripts (e1a/e1b, cap_matrix, lwt, counter, e6), contract v2, helpers, lab utilities |
| `notebooks/MASTER_RUN.ipynb` | Devin | Single Run All entry point for the whole project |
| `compose/`, `docker/` | Lâm | Docker Compose clusters (scylla, mongo, node4, cadvisor) |
| `chaos/`, `chaos_runner.py`, `scenarios/`, `lib/`, `lab.env` | Lâm | Chaos orchestration, lab control, monitoring |
| `monitoring/` | Lâm | Prometheus targets, Grafana dashboard |
| `mongo/` | Lâm | Replica-set init script |
| `config/`, `data/sample/` | Uyên | Seeder config + committed sample datasets |
| `experiments/` | Duy | Committed real-run outputs (legacy runs were pruned) |
| `results/` | Uyên + Devin | Analysis outputs (tables, figures, committed-run evidence) |
| `tests/` | Uyên | Unit tests |

## Chạy toàn bộ dự án bằng một notebook — MASTER_RUN.ipynb

`notebooks/MASTER_RUN.ipynb` là entry point duy nhất: mở notebook →
**Restart Kernel → Run All**. Không cần chạy file Python nào trước (ngoại trừ
khởi động database bên ngoài nếu muốn chạy LIVE).

Luồng: Environment Setup → Data Preparation → Database Init → Ingestion →
NoSQL Ops → CAP Experiments → Results → Final Validation. Kết quả ghi vào
`results/master_run/master_run_report.json`.

| Chế độ | Điều kiện | Hành vi |
|---|---|---|
| **LIVE** | Docker + cụm ScyllaDB/MongoDB + driver | chạy experiment thật (e1a/e1b/lwt/counter/cap_matrix) |
| **OFFLINE** | Không có cluster | các bước LIVE đánh dấu **SKIPPED** + hướng dẫn khởi động; vẫn phân tích evidence thật đã commit + contract selftest + charts |

Nguyên tắc: cell FAIL không được gán nhãn PASS; run CAP_ALL 18/11 gắn nhãn
INVALID (setup defect); dữ liệu selftest gắn `origin=synthetic`.

## Hướng dẫn khởi chạy môi trường (Real Database)

Dự án sử dụng Docker để giả lập cụm phân tán thật:

1. Khởi tạo mạng: `docker network create --subnet=10.88.88.0/24 lab-net`
2. Khởi động ScyllaDB (3 node): `docker compose -f docker/scylla.yml up -d`
   hoặc dùng `compose/` của Lâm + `lab.env`/`scripts/lab_up.sh`.
3. Khởi động MongoDB (Replica Set 3 node): `docker compose -f docker/mongo.yml up -d`
4. Khởi tạo Replica Set cho MongoDB:
   `docker exec -it mongo1 mongosh --eval "rs.initiate({_id: 'rs0', members: [{_id: 0, host: '10.88.88.31:27017'}, {_id: 1, host: '10.88.88.32:27017'}, {_id: 2, host: '10.88.88.33:27017'}]})"`

## Phân loại nguồn gốc dữ liệu (Provenance)

Theo Data Contract v2, dự án phân định rõ ràng:
- **Real / Observed**: script E1a, E1b, CAP E2-E5, LWT, Counter chạy trực tiếp
  trên cụm ScyllaDB (3 node); E6 trên MongoDB Replica Set.
- **Mock / Simulated**: đã loại bỏ — script văng lỗi kết nối thay vì sinh dữ
  liệu giả. Dữ liệu `data/sample/` (seeder của Uyên) gắn `origin=simulated`.

## Danh sách các Script thực nghiệm

Kết quả log JSONL/CSV lưu trong `experiments/<Tên>/<run_id>/` (hoặc
`results/master_run/` khi chạy qua notebook).

1. **E1a - ScyllaDB Schema A (Zipf):** `python scripts/e1a_zipf_workload.py`
2. **E1b - ScyllaDB Schema B (Bucketing & CRC32):** `python scripts/e1b_bucketing_workload.py`
3. **CAP E2-E5 - Network Partition (ONE, QUORUM, ALL):** `python scripts/cap_matrix_e2_e5.py`
4. **LWT - Lightweight Transactions:** `python scripts/lwt_experiment.py`
5. **Counter - Native Counter:** `python scripts/counter_experiment.py`
6. **E6 - MongoDB Failover:** `MSYS_NO_PATHCONV=1 docker run --rm --network lab-net -v "/$(pwd):/app" -w /app python:3.11 bash -c "pip install pymongo && python scripts/mongodb_rollback_e6.py"`
7. **Lâm's chaos harness:** `python chaos_runner.py --scenario scenarios/e1_hot_partition.json`

## Quick start (analysis only)

```bash
pip install -r requirements.txt
python -m src.catalog_analysis.seeder --records 5000 --requests 20000 --out data/sample
python -m unittest discover -s tests -v
```

## Giới hạn đã biết

- CAP_ALL và stale-read real: chờ rerun trên máy có Docker (`docs/markdown/project-management/PROJECT_FINAL_HANDOVER.md`).
- E1a/E1b run 18/11 (nếu còn) dùng workload khác nhau → không so sánh được;
  script v2 replay cùng `data/sample/access_log.csv`.
- Không có unit test suite cho `scripts/` (có `selftest_contract.py` + CI).
- `docker/` và `compose/` là 2 bộ compose song song của Duy và Lâm — xem
  `docs/markdown/project-management/PROJECT_REMAINING_WORK.md` P0-5 cho câu hỏi canonical.
