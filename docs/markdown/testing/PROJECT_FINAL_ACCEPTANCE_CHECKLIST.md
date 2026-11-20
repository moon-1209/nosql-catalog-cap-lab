# PROJECT FINAL ACCEPTANCE CHECKLIST

Ngày: 19/11/2026 — `feat/Duy` @ `eaa3852` + remediation uncommitted.

| # | Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|---|
| 1 | Branches & changes inspected | ✅ | `PROJECT_FINALIZATION_AUDIT.md` §state |
| 2 | Data Contract v2 không mismatch | ✅ | `data_contract.py` + edge-case tests |
| 3 | Real output đọc được bởi analysis | ⚠️ | contract v2 output PASS (selftest→3 modules); **run thật cũ là legacy contract — cần rerun** |
| 4 | Schema A/B workloads comparable | ⚠️ | code replay cùng access_log — chưa verify trên cluster |
| 5 | CAP health evidence | ⚠️ | gate có trong code; chưa có run mới |
| 6 | CAP_ALL rerun | ❌ **BLOCKED** | không Docker/driver — xem Blockers |
| 7 | MongoDB failover evidence | ✅ | 2 run thật, `e6_failover_timeline.png` |
| 8 | Chaos harness integrated | ⚠️ | `--external-chaos` implemented, chưa chạy runtime |
| 9 | Failed ops xử lý nhất quán | ✅ | excluded khỏi stale denominator, đếm riêng `failed_ops` |
| 10 | Metrics traceable run_id | ✅ | manifest + run_id trong mọi row |
| 11 | Charts từ data hợp lệ | ✅ | 4 PNG, run invalid được gắn nhãn |
| 12 | Secrets không commit | ✅ | `.env` untrack + `.env.example` (nội dung verified không secret) |
| 13 | Deployment documented | ✅ | `PROJECT_DEPLOYMENT_GUIDE.md` |
| 14 | Security/ops limitations | ✅ | `PROJECT_FINAL_REPORT.md` §14–15 |
| 15 | Final report khớp evidence | ✅ | chỉ dùng số liệu đo được |
| 16 | Demo reproducible | ✅ | `PROJECT_DEMO_GUIDE.md` (lab vs non-lab rõ ràng) |
| 17 | Merge về develop | ❌ | cần team approval |
| 18 | Unit test suite scripts/ | ⚠️ | có selftest + edge cases; chưa có pytest suite |

**Score: 10 ✅ / 6 ⚠️ / 2 ❌ trong 18 mục.**

## Blockers còn lại

1. **CAP_ALL + stale-read + E1-comparable rerun** — cần máy Docker + `scylla-driver`. Lệnh chuẩn: `PROJECT_DEPLOYMENT_GUIDE.md` §5. Acceptance: CAP_ALL healthy ops >90% success; stale_read rate tính được từ version data; E1a/E1b cùng workload.
2. **Merge feat/Duy + feat/Lam + feat/uyen → develop** — cần review 3 người; conflict dự kiến ở `docker/` vs `compose/` (giữ 1 bộ) và README.

## Final acceptance decision

**CONDITIONALLY COMPLETE** — code/contract/documentation đạt; một nhóm thí nghiệm (CAP_ALL, stale-read real, E1 comparable) cần rerun có giám sát trước khi nộp kết quả CAP đầy đủ. KHÔNG được trình bày run CAP_ALL hiện tại như bằng chứng.
