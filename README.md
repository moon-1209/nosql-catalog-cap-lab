# NoSQL Catalog & CAP Lab

Đồ án môn học Cloud Computing - Phân tích CAP và NoSQL.

## Yêu cầu môi trường
- Docker Desktop (đã cấp phát tối thiểu 4GB RAM)
- Python 3.11+
- Các thư viện: `pip install -r requirements.txt` (bao gồm pymongo, scylla-driver, hdrhistogram...)

## Hướng dẫn khởi chạy môi trường (Real Database)
Dự án sử dụng Docker để giả lập cụm phân tán thật:
1. Khởi tạo mạng: `docker network create --subnet=10.88.88.0/24 lab-net`
2. Khởi động ScyllaDB (3 node): `docker compose -f docker/scylla.yml up -d`
3. Khởi động MongoDB (Replica Set 3 node): `docker compose -f docker/mongo.yml up -d`
4. Khởi tạo Replica Set cho MongoDB:
   `docker exec -it mongo1 mongosh --eval "rs.initiate({_id: 'rs0', members: [{_id: 0, host: '10.88.88.31:27017'}, {_id: 1, host: '10.88.88.32:27017'}, {_id: 2, host: '10.88.88.33:27017'}]})"`

## Phân loại nguồn gốc dữ liệu (Provenance)
Theo yêu cầu của Data Contract v2, dự án phân định rõ ràng:
- **Real / Observed (Dữ liệu thật)**: Các script E1a, E1b, CAP E2-E5, LWT, Counter chạy và kết nối trực tiếp vào cụm ScyllaDB (3 node). Script E6 chạy trực tiếp trên cụm MongoDB Replica Set. Mọi log sinh ra trong thư mục `experiments/` đều là dữ liệu thật 100%.
- **Mock / Simulated (Giả lập)**: **Đã được loại bỏ hoàn toàn**. Các script sẽ văng lỗi kết nối và dừng chạy nếu database chưa sẵn sàng, tuyệt đối không tự động sinh dữ liệu giả.

## Danh sách các Script thực nghiệm
Tất cả kết quả log JSONL/CSV được lưu tự động vào thư mục `experiments/<Tên_Thí_Nghiệm>/<run_id>/`.

1. **E1a - ScyllaDB Schema A (Zipf):**
   `python scripts/e1a_zipf_workload.py`
2. **E1b - ScyllaDB Schema B (Bucketing & CRC32):**
   `python scripts/e1b_bucketing_workload.py`
3. **CAP E2-E5 - Network Partition (ONE, QUORUM, ALL):**
   `python scripts/cap_matrix_e2_e5.py` (Tự động ngắt mạng node3, chạy workload và phục hồi).
4. **LWT - Lightweight Transactions (Conditional Write):**
   `python scripts/lwt_experiment.py`
5. **Counter - Native Counter Increment:**
   `python scripts/counter_experiment.py`
6. **E6 - MongoDB Failover (Ép Primary step-down):**
   Chạy lệnh sau để thực thi bên trong mạng Docker:
   `MSYS_NO_PATHCONV=1 docker run --rm --network lab-net -v "/$(pwd):/app" -w /app python:3.11 bash -c "pip install pymongo && python scripts/mongodb_rollback_e6.py"`

## Chạy toàn bộ dự án bằng một notebook — MASTER_RUN.ipynb

`notebooks/MASTER_RUN.ipynb` là entry point duy nhất: mở notebook → **Restart Kernel → Run All**. Không cần chạy file Python nào trước (ngoại trừ khởi động database bên ngoài nếu muốn chạy LIVE).

Luồng: Environment Setup → Data Preparation → Database Init → Ingestion → NoSQL Ops → CAP Experiments → Results → Final Validation. Kết quả ghi vào `results/master_run/master_run_report.json`.

| Chế độ | Điều kiện | Hành vi |
|---|---|---|
| **LIVE** | Có Docker + cụm ScyllaDB/MongoDB + driver | chạy experiment thật (e1a/e1b/lwt/counter/cap_matrix) |
| **OFFLINE** | Không có cluster | các bước LIVE đánh dấu **SKIPPED** + hướng dẫn khởi động; vẫn phân tích **evidence thật đã commit** (`experiments/`) + contract selftest + charts |

Nguyên tắc: cell FAIL không được gán nhãn PASS; run CAP_ALL 18/11 được gắn nhãn INVALID (setup defect, không phải CAP evidence); dữ liệu selftest gắn `origin=synthetic` tách biệt `origin=observed`.

Chạy không qua UI (headless, cần nbclient+ipykernel trong venv):

```bash
.venv/bin/python - <<'EOF'
import nbformat
from nbclient import NotebookClient
nb = nbformat.read("notebooks/MASTER_RUN.ipynb", as_version=4)
NotebookClient(nb, timeout=240, kernel_name="python3",
               resources={"metadata": {"path": "notebooks/"}}).execute()
nbformat.write(nb, "notebooks/MASTER_RUN.ipynb")


## Chạy toàn bộ dự án bằng một notebook — MASTER_RUN.ipynb

`notebooks/MASTER_RUN.ipynb` là entry point duy nhất: mở notebook → **Restart Kernel → Run All**. Không cần chạy file Python nào trước (ngoại trừ khởi động database bên ngoài nếu muốn chạy LIVE).

Luồng: Environment Setup → Data Preparation → Database Init → Ingestion → NoSQL Ops → CAP Experiments → Results → Final Validation. Kết quả ghi vào `results/master_run/master_run_report.json`.

| Chế độ | Điều kiện | Hành vi |
|---|---|---|
| **LIVE** | Có Docker + cụm ScyllaDB/MongoDB + driver | chạy experiment thật (e1a/e1b/lwt/counter/cap_matrix) |
| **OFFLINE** | Không có cluster | các bước LIVE đánh dấu **SKIPPED** + hướng dẫn khởi động; vẫn phân tích **evidence thật đã commit** (`experiments/`) + contract selftest + charts |

Nguyên tắc: cell FAIL không được gán nhãn PASS; run CAP_ALL 18/11 được gắn nhãn INVALID (setup defect, không phải CAP evidence); dữ liệu selftest gắn `origin=synthetic` tách biệt `origin=observed`.

Chạy không qua UI (headless, cần nbclient+ipykernel trong venv): xem `notebooks/` — hoặc `jupyter nbconvert --to notebook --execute notebooks/MASTER_RUN.ipynb`.

## Giới hạn đã biết

- CAP_ALL và stale-read real: chờ rerun trên máy có Docker (`PROJECT_FINAL_HANDOVER.md` §F).
- E1a/E1b run 18/11 dùng workload khác nhau → không so sánh được; script v2 replay cùng `data/sample/access_log.csv`.
- Không có unit test suite cho `scripts/` (có `selftest_contract.py` + CI contract checks).
- Ba nhánh `feat/Duy`/`feat/Lam`/`feat/uyen-analysis-pipeline` chưa merge — xem `PROJECT_REMAINING_WORK.md` P0-5.
