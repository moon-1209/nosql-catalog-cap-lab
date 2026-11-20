# DUY PIPELINE REMEDIATION REPORT

Branch: `feat/Duy` (trên nền `eaa3852`)
Tham chiếu: `TEAM_PIPELINE_COMPLETENESS_AUDIT.md`

---

## 1. Original Defects (từ audit)

| ID | Defect | File bằng chứng |
|---|---|---|
| D1 | `op` lowercase (`"write"/"read"/"lwt_buy"/"counter_inc"`) → `top_partitions` đếm 0 | `data_contract.py`, các script |
| D2 | `ts` ISO8601 → `stale_read.merge_asof` TypeError | `data_contract.py` |
| D3 | `consistency_log` chứa chaos markers, không có READ/WRITE + version → stale không đo được | `cap_matrix_e2_e5.py` |
| D4 | Không `manifest.json` trong run dirs → provenance không verify được | tất cả script |
| D5 | `category_id = key % 10`, không dùng `products.csv` | `e1a_zipf_workload.py` |
| D6 | Schema B sai: `bucket_id` toàn cụm, mất `category_id` | `e1b_bucketing_workload.py` |
| D7 | CAP_ALL 100% fail (358 ops khi healthy, 860 sau heal) | `experiments/CAP_ALL/20261118164314_*` |
| D8 | `.env`, `.pyc`, data output commit vào git | repo root |
| D9 | `docker/` trùng `compose/` của Lâm | `docker/` |
| D10 | develop lỗi thời — work mới chỉ trên feat/Duy | git refs |

## 2. Root Cause Analysis

- **D1/D2:** writer gốc không enforce canonical form — fix bằng `normalize_op()` + `now_ms()` trong `data_contract.py`.
- **D3:** `consistency_log` bị dùng sai mục đích (chaos lifecycle). Fix: tách `chaos_events.csv`, `consistency_log` chỉ nhận event `READ`/`WRITE` kèm `version` monotonic per key.
- **D5/D6:** workload tự sinh key thay vì đọc dataset chung. Fix: `product_catalog.py` load `data/sample/products.csv` (5.000 rows, 20 categories, uuid product_id) + replay `access_log.csv` của Uyên → E1a/E1b cùng workload 1-1.
- **D7 (CAP_ALL):** hai nguyên nhân xếp chồng — (a) không có wait-for-rejoin sau `docker network connect` (script chỉ `sleep 5` rồi sang run CL tiếp theo → node3 chưa UP khi ALL bắt đầu); (b) `LocalAddressTranslator` map mọi host về `127.0.0.1` → driver không nhìn thấy topology thật, `NoHostAvailable` thay vì `Unavailable`. Fix: health gate `wait_cluster_ready` trước run, probe WRITE ở CL đang test, heal-wait sau reconnect, hỗ trợ `SCYLLA_CONTACT_POINTS` IP thật khi chạy trong lab-net.
- **D8:** thiếu `.gitignore` trên nhánh.

## 3. Files Modified / Added

| File | Thay đổi |
|---|---|
| `scripts/data_contract.py` | **Rewrite**: epoch-ms `now_ms()`, `normalize_op()` → READ/WRITE + `op_detail`, `init/write_chaos_event` (chaos_events.csv), `new_manifest/finalize_manifest` (git_sha, origin, op_count, config) |
| `scripts/product_catalog.py` | **Mới**: load products.csv, `bucket_of = crc32(pid)%16`, `load_workload_ops` replay access_log |
| `scripts/e1a_zipf_workload.py` | **Rewrite**: schema A đúng spec `PK ((category_id), added_at, product_id)`, seed products.csv, replay access_log |
| `scripts/e1b_bucketing_workload.py` | **Rewrite**: schema B đúng spec `PK ((category_id, bucket), added_at, product_id)`, verify bucket==crc32(pid)%16 |
| `scripts/cap_matrix_e2_e5.py` | **Rewrite**: `cap_kv(key,version,val)`; consistency_log ghi READ/WRITE thật + version quan sát; chaos → chaos_events.csv; health gate + heal-wait; `--external-chaos` cho chaos_runner |
| `scripts/mongodb_rollback_e6.py` | op → WRITE, chaos → chaos_events.csv, manifest |
| `scripts/lwt_experiment.py` | op → `WRITE` + `op_detail="LWT_BUY"`, manifest |
| `scripts/counter_experiment.py` | op → `WRITE` + `op_detail="COUNTER_INC"`, manifest |
| `scripts/selftest_contract.py` | **Mới**: emit contract v2 synthetic (gắn nhãn `origin="synthetic"`) để test tiêu thụ không cần cluster |
| `data/sample/` | **Mới trên nhánh này** (lấy nguyên từ `feat/uyen-analysis-pipeline`): products.csv, access_log.csv, consistency_log.csv, manifest.json — dataset chung, provenance `simulated` rõ ràng |
| `.gitignore`, `.env.example`, `docker/.env.example` | **Mới** |
| `.env`, `docker/.env`, `scripts/__pycache__/*.pyc` | **Untrack** (file vẫn còn trên disk) |

## 4. Data Contract Changes

`access_log.csv`: `ts` int64 epoch-ms; `op` ∈ {READ,WRITE} uppercase; **cột 10 `op_detail`** (optional, rỗng với op thường; `LWT_BUY`, `COUNTER_INC` giữ semantics đặc biệt). Consumer pandas đọc theo tên cột → không vỡ.

`consistency_log.csv`: chỉ event `READ|WRITE` + `version` int monotonic; `ts` epoch-ms → `merge_asof` hoạt động.

`chaos_events.csv` (mới): `ts, run_id, event, target, detail` — giữ nguyên `partition_start/end`, `failover_start/end` như cũ, chỉ đổi chỗ chứa.

`manifest.json` (mới, mọi run): `contract_version=v2, origin=observed|synthetic, run_id, experiment_id, experiment_type, git_sha, created_at, started_at_ms, ended_at_ms, op_count, config, extra`.

## 5. Schema & Dataset Corrections

- E1a `products_by_category` / E1b `products_bucketed`: đúng `queries-schema-{a,b}.cql` của Uyên (đủ 10 cột, `added_at` bigint, `product_id` text uuid).
- `category_id` từ dataset thật (20 categories), `bucket` verify `crc32(product_id)%16` — script **abort nếu mismatch**.
- E1a/E1b replay **cùng** `access_log.csv` → workload 1-1 comparable (fix R4).
- Keyspace: `NetworkTopologyStrategy` DC=`$SCYLLA_DC` (mặc định datacenter1), RF=`$SCYLLA_RF` — thay SimpleStrategy theo khuyến nghị `apply_schema.sh`.
- Replication note: đổi từ SimpleStrategy → NTS là **deviation cố ý** (khớp rack/AZ model của lab).

## 6. CAP_ALL Investigation

| Cửa sổ | Quan sát audit | Giải thích |
|---|---|---|
| pre-partition (3s) | 358/358 fail `NoHostAvailable` | node3 không UP — nhiều khả năng chưa rejoin sau run QUORUM trước (chỉ sleep 5s) hoặc translator che topology |
| partition (20s) | 2940 fail | đúng kỳ vọng nếu node3 down + CL=ALL |
| post-heal | 860 fail | không có wait-for-UP → cluster chưa đủ 3 node |

**Đã fix trong code** (health gate + probe + heal-wait + real IPs). **Rerun BLOCKED**: máy audit không có Docker (`docker: command not found`) và không có `scylla-driver` — không thể chạy lại để verify. Cần rerun trên máy lab: kỳ vọng healthy ops >90% success, partition ops fail có điều kiện.

## 7. Integration với Uyên — VERIFIED

Chạy `scripts/selftest_contract.py` → run dir contract v2 → chạy thật modules của Uyên (worktree `38801e3`, `.venv` pandas):

| Module | Kết quả | Bằng chứng |
|---|---|---|
| `top_partitions` | **PASS** — reads/writes đếm đúng (80/80 gaming), `failed_ops:1`, `origin:synthetic`, `run.consistency:ok` | `/tmp/uy_tp/summary.json` |
| `stale_read` | **PASS** — merge_asof trên epoch-ms; stale=1/2 đúng thiết kế; failed read (ALL/PARTITIONED) loại khỏi denominator | `/tmp/uy_sr` |
| `bootstrap_ci` | **PASS** — latency n=199 (failed excluded), CI computed | `/tmp/uy_bc` |

Điều kiện còn lại cho integration thật: rerun script trên cluster để có `origin="observed"` data.

## 8. Integration với Lâm

- `cap_matrix_e2_e5.py --external-chaos --partition-at T1 --heal-at T2` cho phép chạy **dưới** `chaos_runner.py --harness-cmd` của Lâm: script không gọi docker, chỉ gắn nhãn `network_state` theo timeline trùng scenario; chaos_runner vẫn là nguồn partition duy nhất → không còn 2 implementation Docker control tranh nhau khi chạy có điều phối.
- `docker/` (Duy) vs `compose/` (Lâm): **trùng chức năng, cùng `lab-net` + container names** — giữ nguyên cả hai (không xóa vì script Duy + README tham chiếu `docker/`); **khuyến nghị sau merge giữ 1 bộ** (`compose/` của Lâm hoàn chỉnh hơn — có monitoring hooks).
- `data/sample` (origin=simulated) giờ là dataset chung duy nhất cho cả replay workload và analysis baseline.

## 9. Test Results

| Test | Kết quả |
|---|---|
| `py_compile` tất cả script | 9/9 OK |
| `git diff --check` | clean |
| Selftest → top_partitions/stale_read/bootstrap_ci | **3/3 PASS** (số liệu đúng thiết kế) |
| Real cluster rerun (E1a/b, CAP, LWT, Counter, E6) | **SKIPPED — BLOCKED**: không Docker/driver trên máy audit |
| Unit tests | không có suite sẵn trên nhánh — `selftest_contract.py` là integration smoke test mới |

## 10. Status Table

| Requirement | Before | After | Evidence | Status |
|---|---|---|---|---|
| op canonical | lowercase | READ/WRITE + op_detail | selftest run dir | FIXED AND VERIFIED |
| ts epoch ms | ISO8601 | int64 ms | merge_asof pass | FIXED AND VERIFIED |
| consistency_log real events | chaos markers | READ/WRITE+version; chaos tách file | stale=1/2 detected | FIXED AND VERIFIED |
| manifest per run | vắng | manifest.json v2 đầy đủ | git_sha thật, run ok | FIXED AND VERIFIED |
| products.csv usage | `key%10` | dataset chung 5k products | code path mới | FIXED BUT NOT VERIFIED (cần cluster) |
| Schema B đúng spec | bucket toàn cụm | `((cat,bucket))` + verify crc32 | DDL mới | FIXED BUT NOT VERIFIED |
| CAP_ALL | 100% fail | health gate + heal-wait + real IP | code fix | **FIXED BUT NOT VERIFIED — rerun blocked** |
| Lâm integration | tự disconnect | `--external-chaos` harness mode | flag + doc | FIXED BUT NOT VERIFIED |
| Hygiene | .env/.pyc tracked | untracked + .gitignore + .env.example | git status | FIXED AND VERIFIED |
| docker/ vs compose/ | trùng | giữ, documented | §8 | NOT FIXED (chờ quyết định merge) |

## 11. Remaining Blockers

1. **CAP_ALL + toàn bộ rerun thật: BLOCKED** — cần máy có Docker + cụm lab (`lab_up.sh`/docker compose) + `scylla-driver`. Tất cả verify "real" hiện mới là code-level; selftest chứng minh contract đúng, không chứng minh cluster chạy đúng.
2. `develop` vẫn lỗi thời — cần merge `feat/Duy` (sau khi review).
3. Quyết định `docker/` vs `compose/` — cần chủ nhân confirm.
4. `node` field trong consistency_log đang là `--node-label` thủ công (coordinator label) — nâng cấp sau lấy host thật từ `response_future`.

## 12. Git State

- Branch: `feat/Duy`, staged+modified: 14 file (xem `git status`).
- **CHƯA commit, CHƯA push** — chờ approval.
- Recommended commit: `fix(contract): align experiment outputs with data contract v2 (ops, epoch-ms, manifest, consistency events)`

Deviations from original design: NTS thay SimpleStrategy; thêm cột optional `op_detail`; `docker/` giữ song song `compose/` tạm thời.
