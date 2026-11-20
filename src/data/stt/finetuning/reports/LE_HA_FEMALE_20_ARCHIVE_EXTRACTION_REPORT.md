# LÊ HÀ / NỮ 20 — ARCHIVE EXTRACTION & CLEANUP REPORT

**Date:** 2026-11-01
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh`
**Scope:** `data/raw/archives/Lê Hà/Nữ 20/` → `data/raw/real_voice/Lê Hà/Nữ 20/`
**Task type:** organize & extract only — no preprocessing, no manifest changes.

---

## A. Tổng quan

| Metric | Count |
|---|---|
| ZIP tìm thấy | 7 |
| ZIP hợp lệ (`unzip -t` OK, no path traversal / `__MACOSX`) | 7 |
| ZIP giải nén thành công trong phiên này | 3 (`B1`, `B2`, `B3`) |
| ZIP đã có sẵn thư mục đích verified 81/81 | 4 (`B`, `B (2)`, `Bản sao của B`, `B4`) |
| ZIP lỗi / bỏ qua | 0 |
| ZIP trùng nội dung theo SHA-256 | 3 cặp byte-identical (xem §B) |

Canonical path `data/raw/real_voice/` duy trì — không tạo cấu trúc song song.

## B. Bảng kiểm kê

| ZIP | SHA-256 (prefix) | Size | Audio trong ZIP | Audio sau giải nén | Trạng thái |
|---|---|---|---|---|---|
| `B.zip` | `6e989e14…099be3` | 5,764,653 | 80 wav + meta | 80 + meta | ✅ verified 81/81 (đã có sẵn) — ≡ `B3.zip` |
| `B (2).zip` | `1a9517fb…d55c0e` | 8,112,047 | 80 wav + meta | 80 + meta | ✅ verified 81/81 (đã có sẵn) — ≡ `B1.zip` |
| `Bản sao của B.zip` | `bd75c95f…ea83ac` | 7,803,183 | 80 wav + meta | 80 + meta | ✅ verified 81/81 (đã có sẵn) — ≡ `B2.zip` |
| `B1.zip` | `1a9517fb…d55c0e` | 8,112,047 | 80 wav + meta | 80 + meta | ✅ **extracted mới** — verified 81/81; byte-identical `B (2).zip` |
| `B2.zip` | `bd75c95f…ea83ac` | 7,803,183 | 80 wav + meta | 80 + meta | ✅ **extracted mới** — verified 81/81; byte-identical `Bản sao của B.zip` |
| `B3.zip` | `6e989e14…099be3` | 5,764,653 | 80 wav + meta | 80 + meta | ✅ **extracted mới** — verified 81/81; byte-identical `B.zip` |
| `B4.zip` | `43b120e0…446c73` | 4,348,476 | 80 wav + meta | 80 + meta | ✅ verified 81/81 (đã có sẵn) — unique |

**Cặp ZIP byte-identical (SHA-256 trùng):**
`B.zip`≡`B3.zip` · `B (2).zip`≡`B1.zip` · `Bản sao của B.zip`≡`B2.zip`
→ các bản re-export cùng nội dung; `B4.zip` là ZIP duy nhất có nội dung mới.

Cấu trúc trong mọi ZIP: `B/` → 80 `B_*.wav` + `metadata.json`.
Giải nén flat (strip prefix `B/`) nhất quán với các batch hiện có.

Subject self-reports (metadata.json): `B`/B3 = Nữ 20 Nam/TPHCM ·
`B (2)`/B1 = Nữ 20 Trung/Quảng Ngãi · `Bản sao của B`/B2 = Nữ 20 Bắc/hải phòng ·
`B4` = Nữ **19** Nam/Tây Ninh.

## C. Data Integrity

| Kiểm tra | Kết quả |
|---|---|
| File đối chiếu thành công (member-md5 vs on-disk) | **567/567** (7×81 files, gồm metadata.json) |
| File thiếu | 0 |
| File lỗi | 0 |
| Ghi đè file đã tồn tại | 0 — `B1/`, `B2/`, `B3/` là thư mục mới; dirs cũ chỉ verify |
| File trùng nội dung (raw md5) | **480 file / 240 nhóm** — `B`≡`B3`, `B (2)`≡`B1`, `Bản sao của B`≡`B2` (80/80 mỗi cặp) |
| Trùng tên nhưng khác nội dung | **80 filename** — mỗi prompt được ≥2 speaker/session khác nhau ghi (giữ riêng từng batch) |
| Không xác minh được | 0 |

Đối chiếu cross-batch nội dung: `B1`↔`B (2)` = 80/80 · `B2`↔`Bản sao của B` = 80/80 ·
`B3`↔`B` = 80/80 · `B4` vs tất cả = 0/80 (nội dung duy nhất — LH_B4).

## D. Cấu trúc sau khi hoàn thành

```
data/raw/
├── archives/Lê Hà/Nữ 20/
│   ├── B.zip               (LH_B1 — Nữ 20, Nam/TPHCM)
│   ├── B (2).zip           (LH_B2 — Nữ 20, Trung/Quảng Ngãi)
│   ├── Bản sao của B.zip   (LH_B3 — Nữ 20, Bắc/hải phòng)
│   ├── B1.zip              (re-export của B (2) — byte-identical)
│   ├── B2.zip              (re-export của Bản sao của B — byte-identical)
│   ├── B3.zip              (re-export của B — byte-identical)
│   └── B4.zip              (LH_B4 — Nữ 19, Nam/Tây Ninh)
│
└── real_voice/Lê Hà/Nữ 20/
    ├── B/               80 wav + metadata.json   ✓ verified vs zip
    ├── B (2)/           80 wav + metadata.json   ✓ verified vs zip
    ├── Bản sao của B/   80 wav + metadata.json   ✓ verified vs zip
    ├── B1/              80 wav + metadata.json   ✓ extracted + verified (audio ≡ B (2))
    ├── B2/              80 wav + metadata.json   ✓ extracted + verified (audio ≡ Bản sao của B)
    ├── B3/              80 wav + metadata.json   ✓ extracted + verified (audio ≡ B)
    └── B4/              80 wav + metadata.json   ✓ verified vs zip

    → 7 thư mục, 560 wav tổng, 320 unique content
```

## E. Thay đổi thực tế

| Hạng mục | Chi tiết |
|---|---|
| Thư mục mới | `data/raw/real_voice/Lê Hà/Nữ 20/B1/`, `B2/`, `B3/` |
| ZIP đã giải nén | `B1.zip`, `B2.zip`, `B3.zip` (flat, strip `B/`) |
| ZIP bỏ qua | 0 |
| Ghi đè dữ liệu | **Không** — 0 file |
| Xóa file | **Không** — kể cả 240 duplicate file (audit trail) |
| ZIP gốc | 7/7 nguyên vẹn trong archives |
| Manifest thay đổi | **Không** — provenance `duplicate_skipped` của B1–B3 đã log trong `download_manifest.csv` từ import trước; dirs mới extract nằm ngoài manifest (quy ước audit-trail) |
| Preprocessing / annotation / GT / splits | không đụng |
| Validator | **PASS** (1 pre-existing warning: supervised splits empty) |

## Lưu ý

- `B1/`, `B2/`, `B3/` chứa audio **byte-identical** với canonical `B (2)/`,
  `Bản sao của B/`, `B/` — giữ lại làm audit trail theo yêu cầu 1 ZIP ↔ 1 thư mục;
  không phải dataset records mới (đã `duplicate_skipped` trong manifest).
- Dataset records canonical: `LH_B1`→`B`, `LH_B2`→`B (2)`, `LH_B3`→`Bản sao của B`,
  `LH_B4`→`B4` (80 records mỗi speaker trong unannotated/review_queue/stt_dataset).
