# LÊ HÀ / NỮ 20 — REMOVE REDUNDANT BATCH B6 REPORT

**Date:** 2026-11-02 · **Repo:** `Data-Science-Major-Project` · **Branch:** `quang-manh`
**Scope:** `data/raw/archives/Lê Hà/Nữ 20/` + `data/raw/real_voice/Lê Hà/Nữ 20/` only.

---

## 1. Xác minh trước khi xóa

| Check | Kết quả |
|---|---|
| `B6.zip` / `B7.zip` tồn tại | ✅ cả hai |
| `B6/` / `B7/` tồn tại | ✅ cả hai (81 files mỗi dir: 80 wav + metadata.json) |
| Raw MD5 80 cặp wav B6↔B7 | **80/80 identical** |
| File độc nhất chỉ có trong B6 | **0** |
| File khác nội dung | chỉ `metadata.json` (exportDate khác — duplicate export, đúng audit trước) |
| `B7` thay thế đầy đủ B6 | ✅ verified — đủ 80/80 bản ghi |

## 2. Backup ghi nhận

- `B6.zip` sha256: `7bfd0e00cab0d894…` · `B7.zip` sha256: `b30840cdd87b59e4…`
- Manifest refs tới `/B6/` paths: **0** trên cả 4 manifests → không cần cập nhật (B6 chưa từng có dataset records — storage-only batch).

## 3. Đối tượng đã xóa (đúng 2)

- `data/raw/archives/Lê Hà/Nữ 20/B6.zip`
- `data/raw/real_voice/Lê Hà/Nữ 20/B6/` (81 files)

Không xóa: `B7.zip`, `B7/`, `B`, `B1`, `B2`, `B3`, `B8` và mọi dữ liệu khác.
Provenance: lịch sử B6 giữ trong báo cáo import
(`LE_HA_FEMALE_20_NEW_ARCHIVES_IMPORT_REPORT.md`) — zip source Drive id `12iII1X0…`,
sha256 `7bfd0e00…`, subject Nữ 20 Nam/Đồng Tháp; nội dung = `B7` (canonical giữ lại).

## 4. B7 giữ nguyên — xác nhận

- `B7.zip`: tồn tại, `unzip -t` OK, sha256 `b30840cd…` không đổi.
- `B7/`: 80 wav + metadata.json đầy đủ, checksum không đổi (dir không bị đụng).

## 5. Validation

| Check | Kết quả |
|---|---|
| `B6.zip` / `B6/` còn lại | không |
| `B7` nguyên vẹn | ✅ |
| `validate_dataset.py` | **PASS** (1 pre-existing warning: supervised splits empty) |
| Broken paths mới | 0 |
| sample_id trùng | 0 |
| Batch khác bị ảnh hưởng | 0 |

## 6. Directory tree sau cleanup

```
data/raw/archives/Lê Hà/Nữ 20/
├── B.zip  ├── B1.zip  ├── B2.zip  ├── B3.zip  ├── B7.zip  └── B8.zip

data/raw/real_voice/Lê Hà/Nữ 20/
├── B/   (LH_B1, TPHCM)
├── B1/  (LH_B2, Quảng Ngãi)
├── B2/  (LH_B3, hải phòng)
├── B3/  (LH_B4, Tây Ninh)
├── B7/  (B-subject, Đồng Tháp — bản lưu canonical)
└── B8/  (B-subject, Đắk Nông — 79 wav)
```

Khớp cấu trúc kỳ vọng. Không batch nào khác bị đổi tên/xóa/sửa.
