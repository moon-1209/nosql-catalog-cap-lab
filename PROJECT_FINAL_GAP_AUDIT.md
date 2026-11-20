# PROJECT FINAL GAP AUDIT

Ngày: 19/11/2026 — `feat/Duy` @ `eaa3852` + remediation uncommitted.
Trước đó: `TEAM_PIPELINE_COMPLETENESS_AUDIT.md`, `DUY_PIPELINE_REMEDIATION_REPORT.md`, `PROJECT_FINALIZATION_AUDIT.md`.

## 1. Repository State

- `main` (`de1d1bd`): chỉ README — không phải source of truth.
- `develop` (`a2f4428`): Duy pre-remediation — lỗi thời.
- `feat/Duy` (`eaa3852` + working tree): experiments + contract v2 + docs + CI.
- `feat/Lam` (`8a87c69`): infra + chaos_runner + monitoring + audit tools.
- `feat/uyen-analysis-pipeline` (`38801e3`): analysis pipeline + contract v2 spec + 34 tests.
- Không branch nào merged về main/develop. Course PDFs (Ch1–Ch5) **không có trong workspace** → course-compliance assessment là **PROVISIONAL**, map theo docs nội bộ của chính project.

## 2. Course Requirement Mapping (provisional — rubric không có sẵn)

| Yêu cầu suy ra (từ docs + experiments) | Status | Evidence |
|---|---|---|
| NoSQL data modeling (schema A/B, partition key) | VERIFIED (design+code) | `queries-schema-*.cql`, `e1a/e1b` v2 |
| Distributed cluster deployment (multi-node) | IMPLEMENTED | `docker/`+`compose/` 3-node, chưa verify runtime tại máy này |
| Consistency levels / CAP experiment | IMPLEMENTED+partial VERIFIED | ONE/QUORUM real runs 18/11; ALL blocked |
| Network partition / chaos testing | IMPLEMENTED | `chaos.sh`, `chaos_runner`, `docker network disconnect` |
| Failover/recovery experiment | VERIFIED | E6 2 runs, 0 write loss |
| Monitoring | IMPLEMENTED | Prometheus/Grafana (feat/Lam) |
| Security practices | IMPLEMENTED | `docs/PROJECT_SECURITY_AUDIT.md` — lab-scope pass |
| Backup/recovery | IMPLEMENTED (doc) — runtime BLOCKED | `docs/PROJECT_BACKUP_RECOVERY.md` |
| Public cloud (AWS/GCP) | NOT_REQUIRED (provisional) | không rubric xác nhận |
| CI/CD | IMPLEMENTED (lightweight) | `.github/workflows/ci.yml` — justified by scale |

## 3. Existing Evidence

- REAL (legacy contract): 9 run dirs 18/11 — CAP_ONE 4008 ok, CAP_QUORUM 3916 ok, E1a/E1b 1000, LWT 50 (1 winner), Counter 99, E6 228+207. Analysis: `results/committed_runs/analysis.json`.
- SYNTHETIC: selftest run → 3 module Uyên PASS (labeled `origin=synthetic`).
- SIMULATED: `data/sample` (Uyên seeder, manifest origin=simulated).
- Charts: `results/committed_runs/charts/*.png` từ real runs, run invalid gắn nhãn.

## 4. Gap Matrix (final)

| Component | Status | Note |
|---|---|---|
| Contract v2 (ops/ts/chaos/manifest) | VERIFIED | selftest + edge cases + git_sha thật |
| CAP_ONE/QUORUM evidence | VERIFIED | legacy real runs, preserved |
| **CAP_ALL** | **BLOCKED** | code fixed; rerun cần Docker+driver |
| **Stale-read real** | **BLOCKED** | contract sẵn; cần run mới |
| **E1a/E1b comparable** | **BLOCKED** | code replay cùng ops; cần run mới |
| E6 failover | VERIFIED | 2 real runs |
| LWT/Counter | VERIFIED | real runs |
| Analysis consume v2 | VERIFIED | 3 modules pass |
| Chaos `--external-chaos` | IMPLEMENTED | chưa runtime verify |
| Architecture doc | VERIFIED | `docs/PROJECT_ARCHITECTURE.md` |
| Security audit | VERIFIED | `docs/PROJECT_SECURITY_AUDIT.md` |
| Backup/recovery | IMPLEMENTED→runtime BLOCKED | procedure documented |
| Monitoring doc | VERIFIED | `docs/PROJECT_MONITORING.md` |
| Deployment guide | VERIFIED | `PROJECT_DEPLOYMENT_GUIDE.md` + §7.5 |
| CI | IMPLEMENTED | contract-ci workflow |
| Merge → develop | MISSING | cần approval |
| Unit test suite (pytest) | MISSING | chỉ selftest/edge tests |

## 5. Recommended Priorities

P0: rerun trên máy lab (CAP_ALL, cap v2 stale, E1a/b comparable) → VERIFIED.
P1: merge 3 nhánh về develop, resolve `docker/` vs `compose/` (khuyến nghị canonical = `compose/` của Lâm — đầy đủ monitoring hooks; `docker/` giữ làm standalone dev path).
P2: pytest suite cho data_contract; backup/restore runtime verify.
