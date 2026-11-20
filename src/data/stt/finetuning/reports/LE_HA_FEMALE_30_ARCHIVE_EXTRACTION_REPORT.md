# LÊ HÀ / NỮ 30 — ARCHIVE EXTRACTION & CLEANUP REPORT

**Date:** 2026-11-01
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh`
**Scope:** `data/raw/archives/Lê Hà/Nữ 30/` → `data/raw/real_voice/Lê Hà/Nữ 30/`
**Task type:** organize & extract only — no preprocessing, no manifest changes.

---

## A. Tổng quan

| Metric | Count |
|---|---|
| ZIP tìm thấy | 6 |
| ZIP hợp lệ (`unzip -t` OK, no path traversal / `__MACOSX`) | 6 |
| ZIP giải nén thành công trong phiên này | 2 (`F30_05`, `F30_06`) |
| ZIP đã có sẵn thư mục đích verified 71/71 | 4 (`F30_01`, `F30_02`, `F30_04`, `F30_07`) |
| ZIP lỗi / bỏ qua | 0 |
| ZIP trùng SHA-256 với nhau | 0 (6 SHA-256 khác nhau) |

Canonical path `data/raw/real_voice/` được duy trì — không tạo cấu trúc song song.

## B. Bảng kiểm kê

| ZIP | SHA-256 (prefix) | Size | Audio trong ZIP | Audio sau giải nén | Trạng thái |
|---|---|---|---|---|---|
| `F30_01.zip` | `7f002b06…98ad72c` | 5,432,318 | 70 wav + metadata.json | 70 + meta | ✅ verified 71/71 (đã có sẵn) |
| `F30_02.zip` | `ea772f3f…afb6c86f` | 11,489,244 | 70 wav + metadata.json | 70 + meta | ✅ verified 71/71 (đã có sẵn) |
| `F30_04.zip` | `06ee3181…80ddecb` | 4,776,755 | 70 wav + metadata.json | 70 + meta | ✅ verified 71/71 (đã có sẵn) |
| `F30_05.zip` | `8c925169…c3d6ae5` | 5,432,318 | 70 wav + metadata.json | 70 + meta | ✅ **extracted mới** — verified 71/71 |
| `F30_06.zip` | `09fa8917…13bb0` | 5,432,318 | 70 wav + metadata.json | 70 + meta | ✅ **extracted mới** — verified 71/71 |
| `F30_07.zip` | `6adbc647…7aef9e` | 4,408,831 | 70 wav + metadata.json | 70 + meta | ✅ verified 71/71 (đã có sẵn) |

Cấu trúc trong mọi ZIP: `F30/` → 70 `F30_*.wav` + `metadata.json`.
Giải nén flat (strip prefix `F30/`) để nhất quán với các batch hiện có — không tạo
thư mục lồng `F30/F30_0X/`.

## C. Data Integrity

| Kiểm tra | Kết quả |
|---|---|
| File đối chiếu thành công (member-md5 vs on-disk) | **426/426** (6×71 files, gồm metadata.json) |
| File thiếu | 0 |
| File lỗi | 0 |
| Ghi đè file đã tồn tại | 0 — `F30_05/`, `F30_06/` là thư mục mới; các dir cũ chỉ verify, không ghi |
| File trùng nội dung (raw md5) | **210 file** thuộc 70 nhóm — `F30_01` ≡ `F30_05` ≡ `F30_06` (70/70 mỗi cặp) |
| Trùng tên nhưng khác nội dung | **70 filename** — mọi `F30_*.wav` tồn tại ở ≥2 batch với nội dung khác nhau (cùng bộ prompt, khác speaker/session — giữ nguyên, không xóa) |
| Không xác minh được | 0 |
| ZIP sha-trùng nhau | 0 — `F30_05`/`F30_06` chỉ khác `metadata.json` (exportDate 07:15 vs 07:16) |

**Đối chiếu thư mục đã tồn tại (rule 6):** `F30_01/02/04/07` — 71/71 file khớp md5
với ZIP gốc, 0 file thừa, 0 file thiếu → giữ nguyên, không giải nén lại.

## D. Cấu trúc cuối cùng

```
data/raw/
├── archives/Lê Hà/Nữ 30/
│   ├── F30_01.zip  (LH_F30_3 — Nữ 30, Nam)
│   ├── F30_02.zip  (LH_F30_2 — Nữ 28, Nam/Quảng Ngãi)
│   ├── F30_04.zip  (LH_F30_4 — Nữ 30, Trung/Bình Thuận)
│   ├── F30_05.zip  (dup export của F30_01 — export 11-01 07:15)
│   ├── F30_06.zip  (dup export của F30_01 — export 11-01 07:16)
│   └── F30_07.zip  (LH_F30_5 — Nữ 30, Nam/Bảo Lộc)
│
└── real_voice/Lê Hà/Nữ 30/
    ├── F30_01/   70 wav + metadata.json   ✓ verified vs zip
    ├── F30_02/   70 wav + metadata.json   ✓ verified vs zip
    ├── F30_04/   70 wav + metadata.json   ✓ verified vs zip
    ├── F30_05/   70 wav + metadata.json   ✓ extracted + verified (audio ≡ F30_01)
    ├── F30_06/   70 wav + metadata.json   ✓ extracted + verified (audio ≡ F30_01)
    └── F30_07/   70 wav + metadata.json   ✓ verified vs zip

    → 6 thư mục, 420 wav tổng, 280 unique content
```

## E. Những thay đổi đã thực hiện

| Hạng mục | Chi tiết |
|---|---|
| Thư mục mới | `data/raw/real_voice/Lê Hà/Nữ 30/F30_05/`, `…/F30_06/` |
| ZIP đã giải nén | `F30_05.zip`, `F30_06.zip` (flat extraction, strip `F30/`) |
| File bỏ qua | 0 |
| Ghi đè dữ liệu | **Không** — 0 file |
| Xóa file | **Không** — kể cả 140 duplicate file (giữ đúng rule "không tự xóa trùng lặp") |
| ZIP gốc bị di chuyển/xóa | **Không** — 6 zip nguyên vẹn trong archives |
| Manifest thay đổi | **Không** — `download_manifest.csv` đã ghi provenance `duplicate_skipped` cho F30_05/F30_06 từ trước; các file mới extract nằm ngoài manifest (giống quy ước audit-trail của batch trùng trước đây) |
| Preprocessing / annotation / GT / splits | không đụng |
| Validator | **PASS** (1 pre-existing warning: supervised splits empty) |

## Lưu ý

- `F30_05/` và `F30_06/` chứa audio **byte-identical** với `F30_01/` — đây là các
  bản export trùng được giữ lại làm audit trail theo đúng yêu cầu tổ chức dữ liệu,
  **không** phải dữ liệu mới của dataset (0 manifest records, đúng trạng thái
  `duplicate_skipped` đã log).
- Không có batch `F30_03` — slot đó thuộc về Drive export đã bị loại bỏ trước đây
  (lịch sử trong `download_manifest.csv` dạng `duplicate_removed`).
