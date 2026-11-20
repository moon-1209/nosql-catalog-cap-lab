# LÊ HÀ / NỮ 20 — 3 NEW DRIVE ARCHIVES IMPORT REPORT

**Date:** 2026-11-02 · **Repo:** `Data-Science-Major-Project` · **Branch:** `quang-manh`
**Source:** Google Drive folder `1kPTT0ZJx9nvXHgPjp7TOwcRvsMFgzvRk` (gdown 6.4.2)
**Scope:** download → archive → extract → verify. No preprocessing, no dataset-manifest records, no git ops.

---

## A. Tổng quan

| Metric | Count |
|---|---|
| Files trên Drive | 3 (đúng 3 ZIP mới) |
| Download thành công | 3/3 |
| ZIP hợp lệ (`unzip -t`) | 3/3 |
| ZIP trùng SHA-256 với archive cũ | 0 |
| ZIP là duplicate export của nhau | 1 (`B7` ≡ `B6` content) |
| Batch dir mới tạo | 3 (`B6`, `B7`, `B8`) |
| Audio mới unique | **159** (80 B6 + 79 B8); +80 audit-trail dup (B7) |

## B. Bảng kiểm kê archive

| ZIP (Drive name/id) | Size | SHA-256 | Audio | Batch đích | Trạng thái |
|---|---|---|---|---|---|
| `B6.zip` (`12iII1X0…l_p`) | 9,149,119 | `7bfd0e00cab0d894…` | 80 | `B6/` | ✅ NEW — subject Nữ 20 Nam/Đồng Tháp (export 11-01 14:47:00) |
| `B7.zip` (`1fzerYce…Mv`) | 9,149,119 | `b30840cdd87b59e4…` | 80 | `B7/` | ✅ extracted — **duplicate export của B6** (80/80 md5-identical; export +22s) |
| `B8.zip` (`1Cv62AWL…ds`) | 8,414,848 | `56a9acaea03f90ad…` | 79 | `B8/` | ✅ NEW — subject Nữ 20 Nam/Đắk Nông (export 16:19); **recordedFilesCount 79/80** |

Cấu trúc trong mỗi ZIP: `B/` → wavs + `metadata.json`. Giải nén flat (strip `B/`).

## C. Filename handling

- 80/80 (B6,B7) và 79/79 (B8) filenames trùng tên với files trong dataset hiện có (pattern `B_*`) — **checksum chứng minh nội dung KHÁC**: B6/B8 có 0 md5-hit vs toàn bộ 1,400+ raw hiện có.
- Quyết định: **giữ nguyên filename gốc** trong từng batch dir riêng (đúng convention B vs B1/B2/B3 hiện có — cùng tên khác nội dung tách theo batch). **Không file nào bị đổi tên → bảng mapping rỗng.**

## D. Duplicate analysis

| Loại | Count |
|---|---|
| Cùng tên, khác nội dung (vs dataset) | 159 filenames — giữ nguyên, tách theo batch |
| Trùng nội dung thực sự | **B7 = B6** (80/80 members md5-identical, chỉ `metadata.json` exportDate khác) — giữ cả hai làm audit trail |
| Khác tên cùng nội dung | 0 |
| File bị loại bỏ | 0 |

## E. Data Integrity

| Check | Result |
|---|---|
| Member↔extracted sha/md5 | **B6: 81/81 · B7: 81/81 · B8: 80/80** (incl. metadata.json) |
| File lỗi / thiếu | 0 (B8 thiếu `B_B_08_n.wav` là do nguồn chỉ ghi 79/80 — `recordedFilesCount=79`) |
| Ghi đè | 0 — 3 batch dirs đều mới |
| Path traversal / `__MACOSX` | 0 |
| Metadata tham chiếu | metadata.json nguyên vẹn mỗi batch, không ref filename cụ thể |
| Validator | **PASS** (1 pre-existing warning: supervised splits empty) |
| Batch cũ (B, B1, B2, B3) | 0 thay đổi |

## F. Directory tree

```
data/raw/archives/Lê Hà/Nữ 20/
├── B.zip  B1.zip  B2.zip  B3.zip          (cũ)
├── B6.zip  B7.zip  B8.zip                  (mới)

data/raw/real_voice/Lê Hà/Nữ 20/
├── B/   (LH_B1, TPHCM)        80 wav + meta
├── B1/  (LH_B2, Quảng Ngãi)   80 wav + meta
├── B2/  (LH_B3, hải phòng)    80 wav + meta
├── B3/  (LH_B4, Tây Ninh 19)  80 wav + meta
├── B6/  (B-subject, Đồng Tháp) 80 wav + meta   ← NEW
├── B7/  (≡ B6, dup export)      80 wav + meta   ← audit trail
└── B8/  (B-subject, Đắk Nông)   79 wav + meta   ← NEW (thiếu B_B_08_n)
```

## G. Thay đổi thực tế

- Tải xuống: 3 ZIP từ Drive ids ở §B → `/tmp/nu20_new/` → copy sang archives.
- Lưu trữ: `archives/Lê Hà/Nữ 20/{B6,B7,B8}.zip`.
- Batch dirs tạo mới: `real_voice/…/Nữ 20/{B6,B7,B8}/`.
- Đổi tên file: **không có** (0 file).
- Metadata sửa: **không có**.
- Ghi đè / xóa: **không có**.
- Manifest dataset (unannotated/review/stt_dataset): **không đổi** — storage-level import per task scope (không import vào fine-tuning dataset). download_manifest không sửa (ngoài phạm vi chỉ định; có thể bổ sung provenance rows nếu team yêu cầu).
- Vấn đề còn tồn tại: **B8 thiếu 1 recording** (`B_B_08_n.wav`) theo metadata nguồn; **B7 là dup export của B6** — đề xuất speaker ids dự kiến `LH_B5` (B6) và `LH_B6` (B8) nếu import vào dataset sau này.
