# PROJECT FINAL HANDOVER

## A. Executive Summary

**Final status: CONDITIONALLY COMPLETE**

Hoàn thành: contract v2 verified, schema/dataset aligned với spec, CAP fixes code-level (health gate + heal-wait + real contact points), chaos integration mode, security hygiene, 5 tài liệu vận hành mới, evidence analysis + 4 charts từ real runs, CI workflow.

Còn lại: **3 experiment cần rerun trên máy lab** (CAP_ALL, stale-read real, E1a/b comparable) + merge về develop. Course rubric không có sẵn → compliance assessment provisional.

## B. Requirement Matrix

| Source | Requirement | Implementation | Evidence | Status | Owner | Next action |
|---|---|---|---|---|---|---|
| project docs | Contract v2 | `data_contract.py` | selftest PASS + edge cases | VERIFIED | Duy | — |
| E1 | Schema A/B comparable | `e1a/e1b` replay cùng ops | code + `data/sample` | IMPLEMENTED→BLOCKED runtime | Duy | rerun trên cluster |
| E2–E5 | CAP matrix | `cap_matrix_e2_e5.py` | ONE/QUORUM real; ALL code-fixed | PARTIAL | Duy | rerun CAP_ALL |
| E2–E5 | Stale-read | consistency_log + version | contract sẵn | BLOCKED | Duy | rerun cap v2 |
| E6 | MongoDB failover | `mongodb_rollback_e6.py` | 2 real runs | VERIFIED | Duy | — |
| Lab | LWT/Counter | `lwt`/`counter` scripts | real runs (1/50 CAS) | VERIFIED | Duy | — |
| analysis | Uyên pipeline consume | modules @38801e3 | 3/3 PASS trên v2 output | VERIFIED | Uyên | chạy trên real run mới |
| infra | Chaos harness | `chaos_runner` + `--external-chaos` | code integrated | IMPLEMENTED | Lâm | runtime verify |
| Ch4(provisional) | Security | audit doc | `docs/markdown/deployment/PROJECT_SECURITY_AUDIT.md` | VERIFIED (lab scope) | Team | auth/TLS nếu public |
| Ch5(provisional) | Deploy/ops | guide + CI | `PROJECT_DEPLOYMENT_GUIDE.md`, `ci.yml` | VERIFIED | Team | — |
| ops | Backup/recovery | procedure doc | `docs/markdown/deployment/PROJECT_BACKUP_RECOVERY.md` | IMPLEMENTED→BLOCKED | Lâm | verify trên lab |
| ops | Monitoring | Prom/Grafana + audit | `docs/markdown/deployment/PROJECT_MONITORING.md` | IMPLEMENTED | Lâm | merge + verify |

## C. Experiment Evidence (REAL, traceable)

| Run ID | Experiment | Ops | Kết quả | File |
|---|---|---|---|---|
| `20261118164217_51d70a18` | CAP_ONE | 4008 | 100% ok, partition 20.5s, p50 1.43ms | `experiments/CAP_ONE/...` |
| `20261118164246_1e06bf4f` | CAP_QUORUM | 3916 | 100% ok, p50 1.54ms | `experiments/CAP_QUORUM/...` |
| `20261118164314_7e93eceb` | CAP_ALL | 4158 | **INVALID** — 0% kể cả healthy | giữ làm defect evidence |
| `20261118163502_71591fb6` | E1a | 1000 | ok; workload chưa comparable | `experiments/E1a_ScyllaDB/...` |
| `20261118163826_70a13d55` | E1b | 1000 | ok; sequential ≠ zipf | `experiments/E1b_ScyllaDB/...` |
| `20261118164826_d623b720` | LWT | 50 | 1 winner — đúng CAS | `experiments/LWT/...` |
| `20261118164827_db8197b5` | Counter | 99 | ok | `experiments/Counter/...` |
| `20261118165408_3b2facb5` | E6 failover | 228 | 0 loss | `experiments/E6_Mongo_Failover/...` |
| `20261118165508_a46786bb` | E6 failover | 207 | 0 loss, latency spike ~1s | cùng trên |

Charts: `results/committed_runs/charts/*.png`; analysis: `results/committed_runs/analysis.json`. git_sha run mới sẽ do `manifest.json` ghi nhận tự động.

## D. Test Results

| Test | Command | Kết quả | Data |
|---|---|---|---|
| Syntax | `python -m py_compile scripts/*.py` | 9/9 OK | — |
| Contract selftest | `python scripts/selftest_contract.py --out /tmp/duy_selftest` | emit đúng 4 file + manifest | synthetic |
| top_partitions consume | `python -m src.catalog_analysis.top_partitions --data <run>` | PASS — 80r/80w gaming, failed_ops=1 | synthetic v2 |
| stale_read consume | `... stale_read --data <run>` | PASS — stale=1/2, failed excluded | synthetic v2 |
| bootstrap_ci consume | `... bootstrap_ci --data <run>` | PASS — n=199 | synthetic v2 |
| Edge cases | inline asserts (normalize_op, manifest, git_sha=eaa3852) | ALL_OK | — |
| Committed-run analysis | `python scripts/analyze_committed_runs.py` | 9 runs parsed, phases+latency | REAL legacy |
| Charts | `.venv/bin/python scripts/chart_committed_runs.py` | 4 PNG | REAL legacy |
| Cluster rerun | — | **NOT EXECUTED** — no docker/cassandra | — |

## E. Security & Operations

- Không credential trong repo (verified grep); `.env`/`.pyc` untracked; `.env.example` placeholder-only.
- Lab không auth/TLS — documented limitation, chấp nhận được cho local lab.
- Ports publish tối thiểu (9042, 27017) — cần thiết cho host client; gợi ý bind 127.0.0.1 nếu siết.
- Backup/recovery: procedure documented, runtime BLOCKED. Monitoring: docs + tools sẵn (feat/Lam).
- CI: `contract-ci` chạy syntax + selftest + contract assertions — không cần cluster.

## F. Remaining Blockers

| Blocker | Root cause | Env cần | Owner | Lệnh | Kỳ vọng |
|---|---|---|---|---|---|
| CAP_ALL rerun | no Docker/driver | máy lab | Duy | `lab_up` → `nodetool status` 3UN → `python scripts/cap_matrix_e2_e5.py` | healthy ops >90% ok; partition fail có điều kiện |
| Stale-read real | cần run v2 | máy lab | Duy | cùng trên → `stale_read --data <cap_run>` | rate tính được từ version |
| E1 comparable | cần replay | máy lab | Duy | `e1a --limit N` + `e1b --limit N` cùng ops | A/B so sánh hợp lệ |
| Backup verify | no Docker | máy lab | Lâm | `docs/markdown/deployment/PROJECT_BACKUP_RECOVERY.md` §2 | COUNT khớp |
| Chaos runtime | no Docker | máy lab | Lâm | `chaos_runner ... --harness-cmd "cap_matrix --external-chaos ..."` | phase marks + network_state đúng |
| Merge develop | approval | — | Lead | merge 3 nhánh, chọn canonical compose | 1 infra |

## G. Team Task Assignment

- **Duy:** chạy lại CAP matrix + E1a/b + LWT + counter + E6 trên máy lab với script v2; verify manifest `post_heal_up_nodes==3`; KHÔNG trình bày run CAP_ALL cũ.
- **Uyên:** sau rerun — `top_partitions`/`stale_read`/`bootstrap_ci` trên run `origin=observed`; confirm `run.consistency=ok`; build final charts từ real v2 data.
- **Lâm:** verify `chaos_runner --harness-cmd` + `--external-chaos`; backup/restore theo procedure; confirm canonical `compose/`.
- **Team lead:** merge 3 nhánh → develop; resolve `docker/` vs `compose/`; approve commit+push của remediation hiện tại.

## H. Git Status

- Branch: `feat/Duy` @ `eaa3852` (chưa commit remediation).
- Staged: `data/sample/*` (4 file), deletions `.env`/`docker/.env`/`.pyc`.
- Modified: 7 scripts + `PROJECT_DEPLOYMENT_GUIDE.md`.
- Untracked mới: `.gitignore`, `.env.example`×2, `.github/workflows/ci.yml`, `scripts/{product_catalog,selftest_contract,analyze_committed_runs,chart_committed_runs}.py`, `docs/` (4 file), `results/committed_runs/`, 7 báo cáo `.md` root.
- **Không commit/push/merge nào được thực hiện.** Merge readiness: cần stage toàn bộ → 1-2 commit theo nhóm (contract+scripts vs docs+evidence).

## I. Final Recommendation

| Mục | Verdict |
|---|---|
| Technical acceptance | **CONDITIONAL** — đạt sau rerun 3 experiment trên lab |
| Final report submission | READY — `PROJECT_FINAL_REPORT.md` nhất quán với evidence, limitation rõ |
| Presentation | READY — demo guide có nhánh không cần lab |
| Live demonstration | READY có điều kiện — cần máy lab; fallback = committed evidence |
