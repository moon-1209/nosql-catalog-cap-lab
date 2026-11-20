# STT AUDIO DATASET — FULL INVENTORY & GAP ANALYSIS

**Date:** 2026-11-01 · **Repo:** `Data-Science-Major-Project` · **Branch:** `quang-manh`
**Type:** AUDIT ONLY — no data modified. Companion file: `audio_inventory.csv` (3,668 rows).

---

## 1. Executive Summary

| Metric | Value |
|---|---|
| Audio entries inventoried | **3,668** (2,638 physical files + 1,030 zip members) |
| Physical audio files | **2,638** — **316.0 MB** |
| — `data/raw/real_voice/` | 1,213 |
| — `src/data/stt/processed/real_voice/wav/` | 1,143 |
| — `data/raw/_backup_f30_reimport_2026-10-30/` | 280 (audit trail) |
| — other (`sim_vision/godot/assets/sounds`) | 2 (game audio, not STT data) |
| ZIP archives scanned | 14 (11 active `data/raw/archives/` + 3 backup) — 1,030 audio members |
| Speaker groups (physical dirs) | **36** (16 raw + 15 processed + 4 backup + 1 other) |
| Distinct speakers (manifest) | 12 (`A`,`B`,`LH_A`,`LH_B1–4`,`LH_F30_2–5`,`LH_M30`) |
| Dataset records | unannotated 956 · review_queue 1,136 · stt_dataset 1,143 · download_manifest 1,700 |

**Headline findings:**
- Every Lê Hà batch is **complete vs its own metadata.json** (recordedFilesCount = actual, 11/11).
- Zero filename-sequence gaps anywhere.
- Only real pipeline gap: **`F30_05` — 70 raws restored 2026-11-01, no processed WAV, no dataset records** (storage-only by design).
- Gender imbalance: ~943 female vs ~270 male raw files (≈3.5:1).
- Smallest real-speaker groups: `Hoàng Tuấn/Nữ 20 tuổi` (10), `Male 30` + `Trẻ con` ×2 (25 each).

## 2. Complete Audio Inventory

### 2.1 By actual format (content-probed, not extension)

| Real container | Files | Note |
|---|---|---|
| WAV/PCM_16 (16k mono) | 1,425 | all `processed/` + backup processed + few raw |
| WebM/Opus 48k **mislabeled `.wav`** | ~770 | Lê Hà raw batches — known anomaly |
| AAC/M4A/MP4 48k | ~430 | B1,B2 (m4a-labeled .wav), Female 30, PU groups, HT Nữ 20, Male 30, Trẻ con |
| AAC raw (.aac ext) | 70 | Hoàng Tuấn/Nam 20 tuổi |
| WAV/PCM_16 game sfx | 2 | sim_vision/godot — excluded from STT stats |

### 2.2 By data_type

| data_type | files | manifest coverage |
|---|---|---|
| raw | 1,213 | 100% covered (dataset or download_manifest provenance) |
| processed | 1,143 | 100% covered |
| backup | 280 | 0 — audit trail by design |
| other (game) | 2 | 0 — out of scope |
| archive_member / backup_archive_member | 820 / 210 | zip provenance rows exist |

## 3. Folder-by-Folder Analysis

| # | Group | Folder | Files | Format | Size | Duration | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Lê Hà/Nữ 20 | `B` (LH_B1, TPHCM) | 80 | opus | 5.8MB | 6.0min | meta ✓ 80/80 |
| 2 | Lê Hà/Nữ 20 | `B1` (LH_B2, Quảng Ngãi) | 80 | aac | 8.1MB | 5.9min | meta ✓ 80/80 |
| 3 | Lê Hà/Nữ 20 | `B2` (LH_B3, hải phòng) | 80 | aac | 7.8MB | 5.6min | meta ✓ 80/80 |
| 4 | Lê Hà/Nữ 20 | `B3` (LH_B4, Tây Ninh 19) | 80 | opus | 4.3MB | 4.4min | meta ✓ 80/80 |
| 5 | Lê Hà/Nữ 30 | `F30_01` (LH_F30_3) | 70 | opus | 5.4MB | 5.6min | meta ✓ 70/70 |
| 6 | Lê Hà/Nữ 30 | `F30_02` (LH_F30_2, 28) | 70 | opus | 11.5MB | n/a* | meta ✓ 70/70 |
| 7 | Lê Hà/Nữ 30 | `F30_03` (LH_F30_5, Bảo Lộc) | 70 | opus | 4.4MB | 5.1min | meta ✓ 70/70 |
| 8 | Lê Hà/Nữ 30 | `F30_04` (LH_F30_4, Bình Thuận) | 70 | opus | 4.8MB | 4.8min | meta ✓ 70/70 |
| 9 | Lê Hà/Nữ 30 | `F30_05` (LH_F30_1, 34 Hà Nam) | 70 | opus | 9.0MB | n/a* | meta ✓ 70/70; **no processed, no records** |
| 10 | Lê Hà/Nam 20 | `A` (LH_A, 20 TpHcM) | 80 | opus | 7.1MB | n/a* | meta ✓ 80/80 |
| 11 | Lê Hà/Nam 30 | `M30` (LH_M30, TPHCM) | 70 | opus | 4.3MB | 10.5min | meta ✓ 70/70 |
| 12 | Female 30 | `Female 30` | 71 | aac | 2.6MB | 4.4min | no metadata.json — expected UNKNOWN |
| 13 | Male 30 | `Male 30` | 25 | aac | 0.7MB | 1.3min | no metadata.json — UNKNOWN |
| 14 | Hoàng Tuấn | `Nam 20 tuổi` | 70 | aac(.aac) | 22.9MB | 5.4min | no metadata.json — UNKNOWN |
| 15 | Hoàng Tuấn | `Nữ 20 tuổi` | **10** | aac | 0.2MB | 0.7min | no metadata.json — UNKNOWN |
| 16 | Phương Uyên | `Nữ 20 tuổi` | 160 | aac | 4.5MB | 13.5min | no metadata.json — UNKNOWN |
| 17 | Phương Uyên | `Trẻ con/Nam 10` | 25 | aac | 0.4MB | 1.8min | no metadata.json — UNKNOWN |
| 18 | Phương Uyên | `Trẻ con/Nữ 10` | 25 | aac | 0.4MB | 1.7min | no metadata.json — UNKNOWN |
| 19 | Phương Uyên | `Giọng clone` | 7 | wav+aac | 3.3MB | 1.1min | **synthetic — excluded from real-voice pool** |
| 20 | backup | `…/processed/F30`, `…/Bản sao`, `…/real_voice/Bản sao`, `…/staging` | 280 | mixed | ~48MB | — | audit trail |
| 21 | other | `sim_vision/godot/assets/sounds` | 2 | wav | 0.4MB | — | game sfx, not STT data |

\* container-level duration metadata absent in some Opus exports (files decode fine; per-file duration available post-conversion).

Processed mirror: every raw group except `F30_05` and `Giọng clone`-raw-wavs has a complete processed dir (16kHz/mono/PCM_16), 1:1 mapping.

## 4. Missing Data Analysis

| Check | Result |
|---|---|
| Filename sequence gaps | **0** (all sequences contiguous within each batch's pattern) |
| Expected vs actual (11 metadata.json) | **all match** — no missing members |
| Raw without processed (real) | **F30_05: 70** (storage-only; backup holds original processed copies) + `Giọng clone/Trường Giang.wav`, `Trần Thành.wav` (2 wav-format raws; .m4a variants ARE processed as `*.m4a.wav`) |
| Processed without raw | **0 true orphans** — 390 flagged rows all resolve to non-`.wav` raw extensions (`.m4a`/`.aac` raws → `.wav` processed) |
| In manifest but missing on disk | **0** |
| On disk but not in any manifest | 282 = 280 backup + 2 game sfx (correct as audit trail/out-of-scope) |
| Duplicate content (physical) | 160 groups / 390 files — all resolved as canonical-vs-backup/archive copies (audit trail); **0 unexplained dups** |
| Same name, different content | 343 filenames — same prompt set recorded by different subjects (correct by design) |
| Folders without metadata.json | Female 30, Male 30, Hoàng Tuấn ×2, Phương Uyên ×4 → expected count **UNKNOWN** for all of them |
| Dataset-record gap | `F30_05` (LH_F30_1 withdrawn subject): raw+archive exist; **0 unannotated/review/stt_dataset records** — flagged, not auto-imported |

## 5. Priority Ranking

| Rank | Folder | Have | Expected | Missing | Completion | Priority |
|---|---|---|---|---|---|---|
| 1 | `Hoàng Tuấn/Nữ 20 tuổi` | 10 | UNKNOWN | n/a | n/a | **HIGH** — smallest real group (10 files, 0.7 min) |
| 2 | `Phương Uyên/Trẻ con/Nam 10` | 25 | UNKNOWN | n/a | n/a | **HIGH** — child voice, minority class |
| 3 | `Phương Uyên/Trẻ con/Nữ 10` | 25 | UNKNOWN | n/a | n/a | **HIGH** — child voice, minority class |
| 4 | `Male 30` | 25 | UNKNOWN | n/a | n/a | **HIGH** — male 30s underrepresented |
| 5 | `Lê Hà/Nam 30/M30` | 70 | 70 | 0 | 100% | MEDIUM — complete but male-pool thin overall |
| 6 | `Lê Hà/Nam 20/A` | 80 | 80 | 0 | 100% | MEDIUM — same reason |
| 7 | `Hoàng Tuấn/Nam 20 tuổi` | 70 | UNKNOWN | n/a | n/a | MEDIUM |
| 8 | `Female 30` | 71 | UNKNOWN | n/a | n/a | LOW |
| 9 | `Lê Hà/Nữ 20` ×4, `Nữ 30` ×4 | 600 | =expected | 0 | 100% | LOW — saturated |
| 10 | `Phương Uyên/Nữ 20 tuổi` | 160 | UNKNOWN | n/a | n/a | LOW — largest group |
| — | `Giọng clone` | 7 | n/a | n/a | n/a | N/A — synthetic, keep separate |
| — | `F30_05` | 70 | 70 | integration gap | storage-only | INFO — needs import decision, not collection |

**Direct answers:**
1. **Folder thiếu dữ liệu nhất:** không xác định được theo expected-count (ngoài Lê Hà, mọi group thiếu metadata.json → UNKNOWN). Theo quy mô tuyệt đối: `Hoàng Tuấn/Nữ 20 tuổi` (10 files) là nhỏ nhất.
2. **Ít audio nhất:** `Giọng clone` (7, synthetic); real-voice nhỏ nhất: `Hoàng Tuấn/Nữ 20 tuổi` (10).
3. **Completion thấp nhất:** UNKNOWN cho mọi non-Lê-Hà group; Lê Hà = 100%.
4. **Cần bổ sung trước:** `Hoàng Tuấn/Nữ 20 tuổi`, `Trẻ con` ×2, `Male 30`.
5. **Đề xuất bổ sung:** xem §6 (đề xuất ≠ số thiếu thực — expected UNKNOWN).
6. **Dư thừa/trùng lặp:** không còn dup thừa trong dataset sau cleanup; 390 file trùng = backup/archives audit trail (có chủ đích); `F30_05` là bản restore có chủ đích.

## 6. Recommended Data Collection Plan

Cân bằng mục tiêu: giọng nam : nữ ≈ 270:943 hiện tại → ưu tiên nam + trẻ con.

| Ưu tiên | Folder | Hiện có | Mục tiêu đề xuất | Cần bổ sung |
|---|---|---|---|---|
| 1 | `Hoàng Tuấn/Nữ 20 tuổi` | 10 | ≥70–80 (chuẩn batch) | **+60–70** |
| 2 | `Phương Uyên/Trẻ con/Nam 10` | 25 | ~70 | **+45** |
| 3 | `Phương Uyên/Trẻ con/Nữ 10` | 25 | ~70 | **+45** |
| 4 | `Male 30` | 25 | ~70 | **+45** |
| 5 | Nam pool chung (M30/A/Nam 20 HT) | 220 | ~1:1 vs nữ | thêm subject nam mới nếu có |
| 6 | `Female 30` | 71 | — | LOW |
| — | `F30_05` | 70 | — | quyết định: giữ storage-only hay import vào unannotated (+ processed) |
| — | Giọng clone | 7 | — | tách biệt, không trộn vào training pool |

Nguyên tắc: giữ Giọng Clone tách khỏi real-voice; mỗi subject mới đi kèm metadata.json; chuẩn batch ~70–80 audio/subject theo convention Lê Hà.

---
*Generated by full-repo scan. All numbers from content-level checks (MD5/SHA-256 + container probe), not filenames.*
