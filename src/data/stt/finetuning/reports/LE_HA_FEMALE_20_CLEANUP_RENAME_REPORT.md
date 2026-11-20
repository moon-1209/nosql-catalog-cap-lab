# LÊ HÀ / NỮ 20 — CLEANUP DUPLICATE BATCHES & RENAME REPORT

**Date:** 2026-11-01
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh`
**Scope:** `data/raw/archives/Lê Hà/Nữ 20/` + `data/raw/real_voice/Lê Hà/Nữ 20/` + processed mirror

---

## ⚠️ Conflict Resolution Note (quan trọng)

Task gốc yêu cầu xóa `B (2)` và `Bản sao của B` như "duplicate batches" — nhưng
checksum + manifest audit chứng minh chúng là **canonical dirs giữ 160 records**
(LH_B2, LH_B3 — hai speaker khác nhau thật). Bản sao byte-identical thực sự là
`B1/`, `B2/` (0 records) và `B3/` (≡`B/`). Đồng thời `B3` đã tồn tại → rename
`B4→B3` bị chặn theo stop-condition của task.

**Phương án user duyệt (Repoint + đổi tên chuẩn):**
`LH_B2` repoint `B (2)`→`B1/` · `LH_B3` repoint `Bản sao của B`→`B2/` ·
xóa `B3/` (dup của `B`, 0 records) để giải phóng tên · rename `B4`→`B3`.

## 1. Git Status

- Branch `quang-manh`; working tree có thay đổi không liên quan — **không commit/push**.

## 2. Inventory (trước cleanup)

| Batch dir | Nội dung | Records | Zip archive |
|---|---|---|---|
| `B/` | LH_B1 (TPHCM) | 80 | `B.zip` |
| `B (2)/` | LH_B2 (Quảng Ngãi) | 80 | `B (2).zip` |
| `Bản sao của B/` | LH_B3 (hải phòng) | 80 | `Bản sao của B.zip` |
| `B4/` | LH_B4 (Tây Ninh, 19) | 80 | `B4.zip` |
| `B1/` `B2/` `B3/` | audit-trail copies | 0 | `B1.zip` `B2.zip` `B3.zip` |

## 3. Duplicate Verification (checksum evidence)

| Cặp | dir_md5 | Kết luận |
|---|---|---|
| `B (2)` vs `B1` | `49451a8a…` = `49451a8a…` (81 files) | byte-identical; zip sha256 `1a9517fb…` giống hệt |
| `Bản sao của B` vs `B2` | `9637dc61…` = `9637dc61…` (81) | byte-identical; sha `bd75c95f…` giống hệt |
| `B3` vs `B` | unique-content-files = 0/81 | `B3` chỉ là re-export của `B`; sha `6e989e14…` ≡ `B.zip` |
| `B4` | `cf428763…` (81) | unique — canonical content của LH_B4 |

Cross-subject: 0/80 shared files giữa 4 speaker — 4 người thật sự khác nhau.

## 4. Cleanup — đối tượng đã xóa (6)

| Đối tượng | Lý do |
|---|---|
| `real_voice/…/B (2)/` | content 100% bảo toàn tại `B1/` (records repoint) |
| `real_voice/…/Bản sao của B/` | content 100% bảo toàn tại `B2/` (records repoint) |
| `real_voice/…/B3/` | 0 records, byte-identical `B/` (canonical `B/` giữ nguyên) |
| `archives/…/B (2).zip` | byte-identical `B1.zip` (giữ lại) |
| `archives/…/Bản sao của B.zip` | byte-identical `B2.zip` (giữ lại) |
| `archives/…/B3.zip` | byte-identical `B.zip` (giữ lại) — giải phóng tên cho rename |

**Không mất recording/audio nào** — mọi nội dung tồn tại ở bản canonical.

## 5. Rename

| Tầng | Trước | Sau | Xác minh |
|---|---|---|---|
| raw dir | `B4/` | `B3/` | dir_md5 `cf428763…` identical |
| archive | `B4.zip` | `B3.zip` | sha256 `43b120e0…` unchanged |
| processed | `B4/` | `B3/` | 80 wav nguyên vẹn |
| processed | `B (2)/` | `B1/` | repoint target cho LH_B2 |
| processed | `Bản sao của B/` | `B2/` | repoint target cho LH_B3 |

## 6. Audio Integrity

- B4 trước rename = B3 sau rename: 80 wav + metadata.json, dir_md5 identical.
- ZIP ↔ extracted dir: `B.zip`↔`B/`, `B1.zip`↔`B1/`, `B2.zip`↔`B2/`, `B3.zip`↔`B3/` — 81/81 mỗi cặp.
- 0 file mất, 0 ghi đè, 0 sample_id trùng.

## 7. Manifest Updates (backup `*.pre_nu20_cleanup_backup`, sửa theo trường)

| Manifest | Rows sửa | Nội dung |
|---|---|---|
| `unannotated/metadata.csv` | 240 | LH_B2→`B1`, LH_B3→`B2`, LH_B4→`B3`: `audio_path`, `raw_path`, `voice_group`, `reviewer_notes` (+ rename annotation; **source zip name trong ngoặc `(local:…)` giữ nguyên**) |
| `review_queue.csv` | 240 | `audio_path` + `reason` (B4→B3) |
| `stt_dataset_manifest.csv` | 240 | `wav_relpath` + `note` (B4→B3) |
| `download_manifest.csv` | 409 + 1 fix + 1 annotate | repoint `local_relative_path`/`note` cho B (2)→B1, Bản sao→B2, B4→B3 (244 rows incl. 160 `duplicate_skipped` member rows của B1/B2.zip); 3 zip rows → `duplicate_removed`; B1/B2.zip annotate "now canonical archive"; **fix:** row `B4.zip`→`B3.zip` giữ `local_file` + rename note; history row `B3.zip` annotate "name reused by renamed B4.zip (LH_B4)" |

- `sample_id` (`_dupN`), `speaker_id` (`LH_B*`): **không đổi**.
- Line counts không đổi: 957 / 1137 / 1144 / 1629 (chỉ field updates).

## 8. Provenance

- `duplicate_skipped`/`duplicate_removed` rows giữ nguyên: source zip names
  (`B (2).zip`, `Bản sao của B.zip`, `B1–B4.zip` local sources), checksums, file_id
  Drive — đầy đủ lịch sử download/archive/extract/duplicate detection.
- Trạng thái `duplicate_removed` mới ghi rõ: nội dung canonical ở đâu, xóa khi nào.

## 9. Path Validation

- Nữ 20 broken refs trong active manifests: **0**
- Residual `B (2)/`, `Bản sao của B/`, `B4/` paths trong 3 manifests chính: **0**
- `drive_relative_path` giữ tên nguồn gốc (đúng — source provenance, không phải local path).

## 10. Validator

`.venv/bin/python src/data/stt/finetuning/scripts/validate_dataset.py` → **PASS**
(1 pre-existing warning: supervised splits empty). 1,136 audio paths OK, 0 broken,
0 duplicate sample_id, 12 speakers.

## 11. Directory Tree cuối cùng

```
data/raw/archives/Lê Hà/Nữ 20/
├── B.zip   (LH_B1)  ├── B1.zip  (LH_B2)  ├── B2.zip  (LH_B3)  └── B3.zip  (LH_B4, renamed từ B4)

data/raw/real_voice/Lê Hà/Nữ 20/
├── B/   (LH_B1, TPHCM)        80 wav + metadata.json
├── B1/  (LH_B2, Quảng Ngãi)   80 wav + metadata.json
├── B2/  (LH_B3, hải phòng)    80 wav + metadata.json
└── B3/  (LH_B4, Tây Ninh)     80 wav + metadata.json   ← renamed từ B4

src/data/stt/processed/real_voice/wav/Lê Hà/Nữ 20/
├── B/  ├── B1/  ├── B2/  └── B3/   (80 wav each, 16kHz mono PCM_16)
```

## 12. Backups

- `unannotated/metadata.csv.pre_nu20_cleanup_backup`
- `review_queue.csv.pre_nu20_cleanup_backup`
- `stt_dataset_manifest.csv.pre_nu20_cleanup_backup`
- `download_manifest.csv.pre_nu20_cleanup_backup`

## Ghi chú

- `~/Downloads/Study/Nữ/` đã không còn — zip sources ngoài Downloads mất, nhưng
  mọi audio bảo toàn trong repo (canonical dirs + archives giữ lại).
- Mapping cuối: `LH_B1`→`B`, `LH_B2`→`B1`, `LH_B3`→`B2`, `LH_B4`→`B3`.
