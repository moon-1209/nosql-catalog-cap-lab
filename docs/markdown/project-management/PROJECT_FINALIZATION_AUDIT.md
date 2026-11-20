# PROJECT FINALIZATION AUDIT (Phase 0)

Ngày: 19/11/2026 — branch `feat/Duy` @ `eaa3852` + remediation chưa commit.
Tham chiếu: `TEAM_PIPELINE_COMPLETENESS_AUDIT.md`, `DUY_PIPELINE_REMEDIATION_REPORT.md`.

## Trạng thái repository

| Branch | Tip | Vai trò | Ghi chú |
|---|---|---|---|
| `main` | `de1d1bd` | Chỉ README | Trống — spec không nằm ở đây |
| `develop` | `a2f4428` | Duy (bản cũ 16/11) | LỖI THỜI — cần merge feat/Duy |
| `feat/Duy` | `eaa3852` + working tree | Experiments + remediation | Đang là nhánh tích hợp thực tế |
| `feat/Lam` | `8a87c69` | Infra/chaos/monitoring | Hoàn chỉnh, chưa merge |
| `feat/uyen-analysis-pipeline` | `38801e3` | Analysis + contract v2 | Hoàn chỉnh, chưa merge |

**Không tìm thấy rubric/đề bài môn học trong repo** (đã quét tất cả branch). Yêu cầu suy ra từ docs nội bộ: `docs/access-patterns`, `docs/data-dictionary`, `docs/markdown/reports/final-report.md` (nhánh Uyên), README các nhánh. "Five course chapters" không có trong repo — không thể đối chiếu.

## Entry points thực tế

| Tầng | Entry point | Branch |
|---|---|---|
| Infra | `scripts/lab_up.sh`, `compose/*.yml` | feat/Lam |
| Schema | `scripts/apply_schema.sh` + `queries-schema-*.cql` | feat/Lam + feat/uyen |
| Workload | `scripts/e1a_*.py`, `e1b_*.py`, `cap_matrix_*.py`, `lwt_*`, `counter_*`, `mongodb_rollback_e6.py` | feat/Duy |
| Chaos | `chaos_runner.py` (`--harness-cmd`, scenarios/) | feat/Lam |
| Logs | `experiments/<EXP>/<run_id>/{access,consistency,chaos}_log.csv + manifest.json` | contract v2 |
| Analysis | `src/catalog_analysis/{top_partitions,stale_read,bootstrap_ci}.py` | feat/uyen |
| Evidence | `results/committed_runs/` (script `analyze_committed_runs.py`) | feat/Duy |

## Ma trận trạng thái

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Data Contract v2 (ops/ts/chaos/manifest) | **VERIFIED** | selftest → 3 module Uyên PASS; edge cases pass |
| Dataset chung products.csv (5000, 20 cat) | **VERIFIED** (file) | `data/sample/` từ nhánh Uyên |
| Schema A/B đúng spec trong code | IMPLEMENTED, chưa verify trên cluster | `e1a/e1b` rewrite |
| CAP_ONE/QUORUM real evidence | **VERIFIED** (run 18/11, legacy contract) | `results/committed_runs/analysis.json`: 100% ok cả 3 pha |
| CAP_ALL | **BLOCKED — NOT VERIFIED** | code fix xong; không Docker/driver để rerun; run cũ invalid (0% ok kể cả healthy) |
| Stale-read E2–E5 real | BLOCKED | run cũ không có version data; cần rerun cap_matrix v2 |
| E6 MongoDB failover | **VERIFIED** | 2 run thật: 0 write loss, latency spike ~1s khi election |
| LWT | **VERIFIED** | 1/50 winners — đúng CAS |
| Counter | VERIFIED (99 ops) | run 18/11 |
| Chaos harness `--external-chaos` | IMPLEMENTED, chưa verify runtime | `--external-chaos` flag + docstring |
| Analysis consume contract v2 | **VERIFIED** | selftest pass trên worktree 38801e3 |
| Charts | **VERIFIED** (real committed data) | `results/committed_runs/charts/*.png` |
| Monitoring | IMPLEMENTED (feat/Lam) | Prometheus/Grafana files |
| Backup/recovery | NOT IMPLEMENTED | không có trong repo — nêu limitation |
| Public cloud deploy | NOT REQUIRED (không rubric) | Docker local là phạm vi hiện có |
| Unit test suite cho scripts/ | MISSING | chỉ có selftest integration |
| Merge về develop | MISSING | blocker phối hợp |

## Môi trường audit này thiếu gì

- `docker` — không cài (`command not found`) → không rerun cluster được.
- `cassandra` driver — không có trong `.venv` → script chưa chạy thật được.
- Đây là lý do mọi "FIXED BUT NOT VERIFIED" tồn tại — không phải thiếu code.
