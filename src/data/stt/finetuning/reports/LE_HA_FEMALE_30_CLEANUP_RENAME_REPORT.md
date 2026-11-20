# LÊ HÀ / NỮ 30 — CLEANUP DUPLICATE BATCHES & RENAME F30_07 → F30_03 REPORT

**Date:** 2026-11-01
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh`

---

## 1. Pre-Operation Checks

- Branch `quang-manh`, working tree có thay đổi không liên quan — không commit.
- `F30_03` không tồn tại ở cả 3 tầng (archives / real_voice / processed) → an toàn rename.
- `F30_05`, `F30_06`, `F30_07` tồn tại đầy đủ cả zip lẫn thư mục.
- Backup manifests: `*.pre_cleanup_backup` ×4.

**Lưu ý môi trường:** toàn bộ `~/Downloads/Study/Nữ/` đã bị xóa/di chuyển khỏi
Downloads trước khi task chạy — các archive trong repo là bản zip cuối cùng.
Điều kiện xóa vẫn thỏa vì audio content bảo toàn đầy đủ (xem §2).

## 2. Đối tượng đã xóa (4) — kèm bằng chứng checksum

| Đối tượng | Bằng chứng duplicate trước khi xóa |
|---|---|
| `data/raw/archives/Lê Hà/Nữ 30/F30_05.zip` (sha256 `8c925169…`) | 70/70 wav md5-identical `F30_01`; **0 recording độc nhất** |
| `data/raw/archives/Lê Hà/Nữ 30/F30_06.zip` (sha256 `09fa8917…`) | 70/70 wav md5-identical `F30_01`; **0 recording độc nhất** |
| `data/raw/real_voice/Lê Hà/Nữ 30/F30_05/` (71 files) | 70/70 wav = `F30_01`; metadata: Nữ 30 Nam/blank, export 07:15Z |
| `data/raw/real_voice/Lê Hà/Nữ 30/F30_06/` (71 files) | 70/70 wav = `F30_01`; metadata: Nữ 30 Nam/blank, export 07:16Z |

- Chỉ xóa đúng 4 đối tượng. Audio content của cả hai batch tồn tại nguyên vẹn tại
  canonical `F30_01/` (70 wav) — **không mất dữ liệu recording nào**.
- Provenance giữ nguyên trong `download_manifest.csv` (xem §5).

## 3. Rename F30_07 → F30_03 (3 tầng, nội dung nguyên vẹn)

| Tầng | Trước | Sau |
|---|---|---|
| Archive | `archives/…/F30_07.zip` | `archives/…/F30_03.zip` |
| Raw | `real_voice/…/F30_07/` | `real_voice/…/F30_03/` |
| Processed | `processed/wav/…/F30_07/` | `processed/wav/…/F30_03/` |

| Kiểm chứng | Kết quả |
|---|---|
| dir_md5 (71 files, sorted-member md5 concat) | `9ef56248…` — **identical trước/sau** |
| ZIP sha256 | `6adbc647…` — **unchanged** |
| ZIP ↔ dir sau rename | 71/71 members khớp |
| Audio count | 70 wav raw + 70 wav processed — không đổi |
| Tên file bên trong | không đổi; không re-process |

## 4. Manifest & Path Reference Updates

Backup trước sửa: `*.pre_cleanup_backup`. Sửa theo từng trường, không replace hàng loạt.

| Manifest | Rows sửa | Nội dung |
|---|---|---|
| `unannotated/metadata.csv` | 70 | `audio_path`, `raw_path`, `voice_group`, `reviewer_notes`: `F30_07`→`F30_03` (chỉ rows `LH_F30_5`) |
| `review_queue.csv` | 70 | `audio_path`, `reason`: `F30_07`→`F30_03` |
| `stt_dataset_manifest.csv` | 70 | `wav_relpath`, `note`: `F30_07`→`F30_03` |
| `download_manifest.csv` | 76 + 72 | 72 rows `F30_07`→`F30_03` (paths + "member of"/"batch" refs; **source path `F30_3.zip` giữ nguyên**); 4 rows zip/metadata `F30_05`+`F30_06`: `local_file`→`duplicate_removed` + removal note; 72 history rows `duplicate_removed` cũ được **annotate thêm**: "batch name 'F30_03' now reused by LH_F30_5 (renamed from F30_07) 2026-11-01" |

- `sample_id` (`F30_*_dup4`), `speaker_id` (`LH_F30_5`), transcript, annotation,
  GT: **không đổi**.
- 140 member rows `duplicate_skipped` của F30_05/06 giữ nguyên — canonical path
  `F30_01/` còn tồn tại, trạng thái vẫn đúng.
- Residual `F30_07` refs trong manifests: **0** (chỉ còn trong note lịch sử
  "renamed from F30_07" — cố ý giữ).
- `F30_03` path refs resolve: **280/280 OK, 0 broken**.

## 5. Validation

`.venv/bin/python src/data/stt/finetuning/scripts/validate_dataset.py` → **PASS**
(1 pre-existing warning: supervised splits empty).

| Check | Kết quả |
|---|---|
| `F30_05.zip`, `F30_06.zip` còn lại | không |
| `F30_05/`, `F30_06/` còn lại | không |
| `F30_03.zip` + `F30_03/` (raw + processed) tồn tại | có |
| Audio paths broken | 0 (1,136 verified) |
| Duplicate sample_id | 0 |
| Record counts | unannotated 956 · review_queue 1,136 · stt_dataset 1,143 · download_manifest 1,628 (không đổi — chỉ cập nhật trường) |
| Batch khác (F30_01/02/04, Nữ 20, Nam 20/30) | không ảnh hưởng |

## 6. Directory Tree cuối cùng

```
data/raw/archives/Lê Hà/Nữ 30/
├── F30_01.zip  ├── F30_02.zip  ├── F30_03.zip  └── F30_04.zip

data/raw/real_voice/Lê Hà/Nữ 30/
├── F30_01/  (LH_F30_3)   70 wav + metadata.json
├── F30_02/  (LH_F30_2)   70 wav + metadata.json
├── F30_03/  (LH_F30_5)   70 wav + metadata.json   ← renamed từ F30_07
└── F30_04/  (LH_F30_4)   70 wav + metadata.json

src/data/stt/processed/real_voice/wav/Lê Hà/Nữ 30/
├── F30_01/  ├── F30_02/  ├── F30_03/  └── F30_04/   (70 wav each)
```

Khớp cấu trúc kỳ vọng. Không batch ngoài danh sách nào bị động vào.

## 7. Backups đã tạo

- `src/data/stt/finetuning/datasets/unannotated/metadata.csv.pre_cleanup_backup`
- `src/data/stt/finetuning/reports/review_queue.csv.pre_cleanup_backup`
- `src/data/stt/manifests/stt_dataset_manifest.csv.pre_cleanup_backup`
- `src/data/stt/manifests/download_manifest.csv.pre_cleanup_backup`

## 8. Ghi chú

- `F30_05`/`F30_06` là các bản export trùng của `F30_01` (cùng session, exportDate
  07:15/07:16 ngày 01-11). Zip container đã xóa; audio canonical tại `F30_01`,
  metadata tóm tắt + checksums giữ trong `download_manifest.csv` và báo cáo này.
- Slot `F30_03` lần thứ hai được tái sử dụng: lần 1 = Drive export đã xóa
  (history `duplicate_removed`, đã annotate), lần 2 = batch `LH_F30_5` hiện tại.
