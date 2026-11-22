# MASTER_RUN — Technical Audit, Refactoring & Notebook Integration Report

Ngày: 20/11/2026 — `feat/Duy` @ `eaa3852` + remediation uncommitted.

## A. Initial Audit

**Cấu trúc thực tế (đã kiểm chứng bằng code, không giả định):**
- `scripts/`: experiment scripts (e1a, e1b, cap_matrix, lwt, counter, e6) + `data_contract.py` v2 + helpers mới (`product_catalog`, `lab_connect`, `selftest_contract`, `analyze_committed_runs`, `chart_committed_runs`).
- `src/catalog_analysis/` + `tests/` + `config/`: pipeline Uyên (mới đưa sang nhánh này từ `feat/uyen-analysis-pipeline` @ `38801e3`).
- `data/sample/`: dataset chung 5.000 products/20 categories (origin=simulated).
- `experiments/`: 11 run dirs — 9 run thật 18/11 (legacy contract) + 2 run lỗi.
- `docker/` + `compose/` (feat/Lam): 2 bộ infra song song — đã documented, giữ cả hai.

**Vấn đề phát hiện và đã sửa trong phase này:**
| # | File | Vấn đề | Xử lý |
|---|---|---|---|
| P1-1 | e1a/e1b/cap/lwt/counter | `LocalAddressTranslator`, `contact_points`, `wait_cluster_ready`, `up_nodes` **trùng lặp 5 nơi** | gom vào `scripts/lab_connect.py` |
| P1-2 | lwt/counter | vẫn `SimpleStrategy` RF=3 (lệch rack/AZ model) | dùng `ensure_keyspace` (NTS datacenter1) — **0 SimpleStrategy còn lại** |
| P1-3 | notebook cell | `missing` check dùng falsy → `bucket=0` hợp lệ bị tính thiếu (346 false positive) | sửa thành check `None`/chuỗi rỗng |
| P1-4 | notebook cell | `stale_read.run()` trả `by_consistency_level` không phải `summary` | sửa key |

**Vấn đề còn lại (không sửa — chờ môi trường/team):** CAP_ALL rerun, stale-read real, E1 comparable rerun, merge 3 nhánh, `docker/` vs `compose/` canonical.

## B. Changes Implemented

| File | Change | Reason |
|---|---|---|
| `scripts/lab_connect.py` | **MỚI** — connect/ensure_keyspace/wait_cluster_ready/up_nodes + translator fallback | dedup 5 scripts, 1 chỗ sửa topology/health |
| `scripts/e1a_zipf_workload.py`, `e1b_bucketing_workload.py` | dùng lab_connect + ensure_keyspace | dedup |
| `scripts/cap_matrix_e2_e5.py` | dùng lab_connect (giữ health gate/heal-wait) | dedup |
| `scripts/lwt_experiment.py`, `counter_experiment.py` | lab_connect + ensure_keyspace (NTS thay SimpleStrategy) | dedup + đúng spec |
| `src/`, `tests/`, `config/` | **đưa từ nhánh Uyên** vào feat/Duy | notebook cần import analysis modules trên cùng branch |
| `notebooks/MASTER_RUN.ipynb` | **MỚI** — 18 cells, 8 sections | single entry point |
| `README.md` | +section MASTER_RUN (LIVE vs OFFLINE, headless run, limitations) | hướng dẫn người mới |

## C. Notebook Design

- **Reuse, không copy**: import `product_catalog`, `data_contract`, `lab_connect`, `selftest_contract`, `analyze_committed_runs`, `src.catalog_analysis.*` trực tiếp; subprocess chỉ cho standalone experiment scripts khi LIVE.
- **Service detection**: docker binary + TCP probe 9042/27017 + driver check → `LIVE_SCYLLA`/`LIVE_MONGO`.
- **Idempotent**: CREATE TABLE/KEYSPACE IF NOT EXISTS, INSERT theo full PK (upsert), run dir mới theo `run_id`, selftest ghi ra temp dir ngoài repo.
- **Honesty**: CAP_ALL gắn INVALID; selftest gắn `origin=synthetic`; final cell chỉ PASS khi metric kiểm chứng được (run.consistency=ok, charts tồn tại), không auto-PASS theo cell success.

## D. Testing Results — executed thật bằng nbclient/ipykernel (không phải claim)

| Component | Status | Evidence |
|---|---|---|
| Environment setup | PASS | pandas/numpy/yaml/matplotlib/scipy OK; cassandra+pymongo missing (reported); docker absent → LIVE off |
| Data preparation | PASS | 5.000 products, 20 cats, **0 dup/0 missing/0 bad bucket**; workload READ:13.481/WRITE:1.519 |
| Database initialization | SKIPPED | no Docker — hướng dẫn in ra cell |
| Data ingestion | SKIPPED | no cluster |
| NoSQL operations | SKIPPED ×4 | e1a/e1b/lwt/counter — no live cluster |
| CAP experiments | EVIDENCE PASS | 3 run thật 18/11: ONE 100%×3 phases, QUORUM 100%, ALL=INVALID labeled |
| Results & evaluation | PASS | selftest→3 module Uyên (`run.consistency=ok`, stale=1/2 detected, n=199); 9 committed runs analyzed |
| Final validation | PASS | `results/master_run/master_run_report.json` ghi đầy đủ |
| **Run All (nbclient execute)** | **PASS** — kernel restart + execute toàn bộ, 1 lần | EXEC OK sau 2 fix cell |

## E. Remaining Issues

1. **LIVE path chưa verify** — không Docker/driver trên máy này; các cell LIVE chỉ được code-reviewed, chưa chạy thật. Trên máy lab: khởi động cluster → Run All sẽ tự vào nhánh LIVE.
2. `nbconvert` không có trong .venv (nbclient/ipykernel có — đủ để execute headless).
3. `results/master_run/` tái tạo mỗi run — đang untracked (quyết định commit evidence hay ignore khi team merge).
4. Merge 3 nhánh vẫn là P0 cho tích hợp thật sự (notebook hiện đã import được src/ của Uyên nhờ bước bring-over).

## F. Final Recommendations

- **Sẵn sàng cho**: review + commit nhóm thay đổi này; demo offline (notebook chạy được không cần cluster và vẫn có real evidence).
- **Cần trước khi nộp**: chạy Run All một lần trên máy lab để verify nhánh LIVE → sau đó merge về develop.
- Commit message đề xuất: `feat(notebook): MASTER_RUN single-entry pipeline + lab_connect refactor + uyen pipeline integration`
- **Không commit/push/merge** — toàn bộ thay đổi nằm trong working tree (54 files) chờ approval.
