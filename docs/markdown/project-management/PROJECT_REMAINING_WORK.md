# PROJECT REMAINING WORK — Đề tài 14

Tham chiếu: `PROJECT_REQUIREMENT_COMPLIANCE_REPORT.md` (bảng 18 tiêu chí).

## P0 — Bắt buộc để đáp ứng đề tài

| # | Công việc | Lý do | File liên quan | Evidence cần | Acceptance | Owner |
|---|---|---|---|---|---|---|
| P0-1 | Rerun CAP_ALL trên cụm healthy | Run 18/11 invalid (0% kể cả healthy) — thiếu bằng chứng availability của ALL | `scripts/cap_matrix_e2_e5.py` | run dir có `manifest.extra.post_heal_up_nodes=3`, healthy ops >90% ok, partition ops fail có điều kiện | `success` theo phase khớp lý thuyết | Duy (máy lab) |
| P0-2 | Rerun cap matrix v2 → stale-read real | Stale rate chưa đo được real — chỉ synthetic | `cap_matrix` v2 + `stale_read.py` | `consistency_log` có READ/WRITE+version; `stale_read` chạy ra rate theo CL | `stale_read_rate_pct` hợp lệ cho ONE/QUORUM | Duy + Uyên |
| P0-3 | Rerun E1a/E1b cùng replay workload | Run cũ không comparable (zipf vs sequential) | `e1a/e1b` v2 + `data/sample/access_log.csv` | 2 run cùng ops, schema A vs B | `top_partitions` so sánh được share/max/mean | Duy |
| P0-4 | Đo tải từng node khi workload chạy | Tiêu chí "tải từng node" đang BLOCKED | `hot_partition_audit.py`, `toppartitions_capture.py` (feat/Lam) | Prom CSV + toppartitions.csv trên run thật | max/mean theo node và shard có số liệu | Lâm + Duy |
| P0-5 | Merge `feat/Duy` + `feat/Lam` + `feat/uyen` → `develop` | Pipeline end-to-end chỉ tồn tại trên 3 nhánh riêng | repo | `develop` chứa đủ scripts+src+compose | checkout develop chạy được `selftest` | Team lead |

## P1 — Cần để báo cáo/bảo vệ tốt

| # | Công việc | Lý do | File | Evidence | Acceptance | Owner |
|---|---|---|---|---|---|---|
| P1-1 | Charts từ real v2 runs (A/B share, stale rate, latency) | Charts hiện tại là legacy/not-comparable | `chart_committed_runs.py` hoặc module Uyên | PNG có run_id v2 | cập nhật final report | Uyên |
| P1-2 | Thêm p99 vào metric reporting | Đề tài nói p95; p99 nên có nếu dữ liệu cho phép | `analyze_committed_runs.py`, `bootstrap_ci` | summary có p99 | p50/p95/p99 đủ trong report | Duy/Uyên |
| P1-3 | Bảng `view_events` hoặc giải thích rõ access_log = view events | Tiêu chí dataset 3 nhóm chỉ PARTIAL | `docs/access-patterns`, schema | DDL + doc | tiêu chí 4 → VERIFIED | Uyên |
| P1-4 | Đối chiếu bài giảng Ch1–Ch5 khi có PDF | Lý thuyết đang "CHƯA ĐỐI CHIẾU" | section 10 compliance report | mapping theo tên chương | nguồn lý thuyết đầy đủ | Team lead |
| P1-5 | Xác nhận canonical compose (`compose/` vs `docker/`) | 2 bộ infra song song gây nhầm | `docker/`, `compose/` | quyết định ghi vào README | 1 bộ canonical + lý do | Lâm + Lead |
| P1-6 | Backup/restore runtime verify | Hiện DOCUMENTARY | `docs/markdown/deployment/PROJECT_BACKUP_RECOVERY.md` §2 | COUNT(*) trước/sau khớp | VERIFIED | Lâm |
| P1-7 | Read-your-writes demo (CL phù hợp) | Nội dung lý thuyết chưa thể hiện | `cap_matrix` hoặc script nhỏ | log RYW pass/fail | thêm vào phần consistency | Duy |

## P2 — Nâng cao (nếu phù hợp phạm vi)

| # | Công việc | Lý do | Acceptance | Owner |
|---|---|---|---|---|
| P2-1 | netem delay/loss để demo "replica chậm" (khác với disconnect) | Đề tài cho phép 2 cách gây gián đoạn | chaos event + latency delta thật | Lâm |
| P2-2 | pytest suite cho `data_contract.py` | hiện chỉ selftest | `pytest tests/` xanh | Duy |
| P2-3 | Scale-out node4 demo (đã có `compose/node4.yml` + `add_node4.sh`) | minh họa scalability | rebalance evidence | Lâm |
| P2-4 | So sánh 4 mô hình NoSQL (lý thuyết) trong báo cáo | nội dung lý thuyết chưa cover KV/graph | section lý thuyết đủ 4 mô hình | Team |

## Ghi chú

- Mọi P0 đều bị chặn bởi **môi trường** (cần Docker + scylla-driver), không phải thiếu code.
- Không đề xuất Kubernetes/Terraform/public cloud — không có yêu cầu nào trong rubric có sẵn.
- Không xóa run legacy: giữ làm evidence và so sánh contract.
