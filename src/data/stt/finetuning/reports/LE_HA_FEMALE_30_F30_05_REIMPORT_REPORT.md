# LÊ HÀ / NỮ 30 — F30 → F30_05 RESTORE & ZIP ARCHIVE REPORT

**Date:** 2026-11-01
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh`

---

## 1. Nguồn & Đích

| | Đường dẫn |
|---|---|
| Nguồn | `data/raw/_backup_f30_reimport_2026-10-30/real_voice/F30/` |
| Đích raw | `data/raw/real_voice/Lê Hà/Nữ 30/F30_05/` |
| Đích archive | `data/raw/archives/Lê Hà/Nữ 30/F30_05.zip` |

**Subject:** `F30`, Nữ, **34 tuổi**, Nam/Hà Nam (metadata.json, export 2026-10-28) —
đây là `LH_F30_1`, subject đã **withdrawn khỏi Drive vào 2026-10-30** và được lưu
vào backup trong đợt re-import. Restore này đưa audio trở lại storage chính thức
dưới slot `F30_05` (slot trống sau cleanup — zip/dir cũ là duplicate của F30_01 đã xóa).

## 2. Pre-Operation Checks

- Branch `quang-manh`; không commit.
- Nguồn tồn tại: **71 files** (70 wav + metadata.json), **8.8 MB**, 0 file ẩn.
- Đích trống hoàn toàn (`F30_05/` và `F30_05.zip` không tồn tại) → không ghi đè.
- Dedup: **0/70** wav trùng md5 với toàn bộ raw hiện có (nội dung duy nhất).
- Cross-verify nguồn gốc: 71/71 file khớp md5 với members của Drive zip gốc
  `F30.zip` còn lưu trong backup archives → restore đúng nội dung Drive ban đầu.
- Checksum SHA-256 nguồn: 71 files ghi nhận trước khi thao tác.

## 3. Di chuyển & Đổi tên

`F30/` → `F30_05/` (copy → verify → remove source):

| Check | Kết quả |
|---|---|
| Files sau copy | 71/71 SHA-256 identical với nguồn, 0 extra, 0 missing |
| Tên file / nội dung / metadata | nguyên vẹn, không sửa |
| Xóa nguồn | chỉ sau khi verify 71/71 — `backup/…/real_voice/F30/` đã xóa (backup còn `Bản sao của F30/`, archives, processed, manifests nguyên vẹn) |

## 4. ZIP Archive

- Tạo `F30_05.zip` (9,046,443 bytes, sha256 `0ac3bc2a…`) với inner root `F30_05/`
  — đúng spec, **không** lồng `F30_05/F30/…`.
- `unzip -t`: OK · giải nén thử `/tmp/f30_05_ziptest`: **71/71 SHA-256 khớp** `real_voice/F30_05/` · member↔dir: **71/71 khớp**.
- 70 wav (WebM/Opus 48k mislabeled `.wav` — giữ nguyên format gốc) + `metadata.json`.

## 5. Manifest & Metadata

`download_manifest.csv`: **+72 rows** (1 zip `local_file` + 70 wav `extracted` +
1 metadata `extracted/parsed`), ghi rõ chuỗi provenance:
backup-restore → Drive gốc `Lê Hà/Nữ 30/F30.zip` (file_id `1l8tJ3lOi…`) → canonical `F30_05`.
`stt_dataset_manifest.csv`, `unannotated/metadata.csv`, `review_queue.csv`:
**không đổi** — đây là storage restore, không tạo dataset records mới cho subject
đã withdrawn (giữ đúng trạng thái re-import trước; không đưa vào splits).
`sample_id`/`speaker_id`/transcript/annotation/GT: không đổi.

## 6. Validation

| Check | Kết quả |
|---|---|
| `real_voice/…/F30_05/` tồn tại | ✅ 71 files |
| `archives/…/F30_05.zip` tồn tại | ✅ integrity OK |
| Nguồn `F30/` trong backup | ✅ đã xóa sau verify |
| Audio count trước/sau | 70 = 70 |
| SHA-256 trước/sau | 71/71 khớp |
| ZIP ↔ folder | 71/71 khớp |
| F30_01/02/03/04 + speaker khác | không ảnh hưởng |
| `validate_dataset.py` | **PASS** (1 pre-existing warning: supervised splits empty) |

## 7. Directory Tree cuối

```
data/raw/real_voice/Lê Hà/Nữ 30/
├── F30_01/  F30_02/  F30_03/  F30_04/
└── F30_05/   ← RESTORED (LH_F30_1, Nữ 34 Hà Nam): 70 wav + metadata.json

data/raw/archives/Lê Hà/Nữ 30/
├── F30_01.zip  F30_02.zip  F30_03.zip  F30_04.zip
└── F30_05.zip  ← CREATED (sha256 0ac3bc2a…)
```

## 8. Lỗi phát sinh

Không có. Lưu ý: `processed/…/F30_05/` **không** được tạo (task cấm preprocessing);
bản processed gốc còn nằm tại `data/raw/_backup_f30_reimport_2026-10-30/processed/F30/`
nếu cần khôi phục riêng sau này. F30_05 hiện là batch storage-only (no dataset records).
