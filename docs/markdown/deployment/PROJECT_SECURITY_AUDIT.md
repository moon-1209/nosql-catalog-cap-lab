# PROJECT SECURITY AUDIT

Phạm vi: trạng thái thực tế trên `feat/Duy` (+ đối chiếu `feat/Lam`). Không destructive testing.

## 1. Controls đã có

| Control | Trạng thái | Evidence |
|---|---|---|
| `.gitignore` | ✅ thêm mới | `__pycache__/`, `*.pyc`, `.env`, `docker/.env`, `.idea/`, `.venv/` |
| `.env` untracked | ✅ | `git rm --cached` cả `.env` + `docker/.env`; file vẫn trên disk |
| `.env.example` placeholders | ✅ | Nội dung = lab network config (subnet IP, image tags, SMP) — **verify: không chứa credential nào** |
| `.pyc` artifact | ✅ | `scripts/__pycache__/data_contract.cpython-311.pyc` đã untrack + xóa |
| Không hardcode credential | ✅ | grep `password|secret|token|api_key` trong `scripts/`, `docker/` → 0 kết quả |
| Network isolation | ✅ | `lab-net` bridge 10.88.88.0/24; DB chỉ lộ qua port publish tối thiểu |

## 2. Risks & findings

| # | Risk | Mức | Evidence | Khuyến nghị |
|---|---|---|---|---|
| S1 | ScyllaDB **không auth** — `cqlsh`/driver connect tự do | Medium | `docker/scylla.yml` (developer-mode, no authenticator config) | Lab-only; nếu demo public thì bật `PasswordAuthenticator` |
| S2 | Port `9042` publish ra host 0.0.0.0 | Low | `docker/scylla.yml:29`, `compose/scylla.yml:46` | Giới hạn `"127.0.0.1:9042:9042"` nếu host không tin cậy; cần thiết cho workload chạy từ host |
| S3 | MongoDB `27017` publish, không auth | Medium | `docker/mongo.yml:41` | Lab-only; RS member vẫn accept unauth connection trên lab-net |
| S4 | `LocalAddressTranslator` map mọi host → 127.0.0.1 | Low (correctness > security) | `e1a/e1b/cap_matrix` | Chỉ là fallback; chạy trong lab-net thì không dùng |
| S5 | Error message vào `access_log` có thể chứa endpoint/IP | Low | `str(e)[:80/120]` | Giới hạn cắt 120 chars — chấp nhận được cho lab |
| S6 | `.idea/` từng bị track trên nhánh khác | Low | audit trước | `.gitignore` đã cover |

## 3. Remediation đã thực hiện

- Untrack `.env` ×2 + `.pyc`; thêm `.env.example`/`docker/.env.example` (placeholder, không secret).
- `.gitignore` mới trên nhánh — trước đó nhánh không có file này.

## 4. Remaining limitations

- Không TLS client→DB, không RBAC, không audit log — **ngoài phạm vi lab local**, phải bổ sung nếu triển khai thật.
- Container chạy với quyền mặc định image (không `--user`), volumes bind-mount `./mongo` read-only (đã có `:ro`).
- Backup artifact (nếu tạo) chứa data — chưa có chính sách mã hóa/retention (xem `docs/markdown/deployment/PROJECT_BACKUP_RECOVERY.md`).

## 5. Security acceptance status

**PASS cho phạm vi "local Docker lab không dữ liệu nhạy cảm".** Nếu rubric yêu cầu môi trường shared/public → CONDITIONAL: phải bật auth + TLS + giới hạn publish port.
