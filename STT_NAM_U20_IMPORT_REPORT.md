# STT DATASET — NAM U20 BATCH IMPORT REPORT (A2 / A3 / A4)

**Date:** 2026-11-05 · **Repo:** `Data-Science-Major-Project` · **Branch:** `quang-manh`
**Type:** BATCH IMPORT — 3 ZIPs from `~/Downloads/Code/` → `Lê Hà/Nam 20/` group
**Result:** ✅ All 3 archives audited, 161/161 files NEW, fully integrated, validator PASS.

---

## A. Source ZIP Inventory

| ZIP | Size | SHA-256 | Audio | Integrity |
|---|---|---|---|---|
| `A2.zip` | 3,839,170 B | `c3edf79e…898c3d` | 80 | ✅ OK |
| `A3.zip` | 3,481,979 B | `106aa6db…c0e3673` | 80 | ✅ OK |
| `A4.zip` | 58,171 B | `b9eae235…62bec4484` | **1** ⚠️ | ✅ OK |

- All zips pass `unzip -t`; no zero-byte, non-audio, or corrupt members.
- Internal layout: `A/` folder + `metadata.json` + `A_*_{n,r}.wav` — identical exporter schema as prior Lê Hà batches (`A.zip`, `B*.zip`).
- Actual format (content-probed): **WebM/Opus 48 kHz mono mislabeled `.wav`** — same known anomaly as all Lê Hà raw batches.
- Original zips left untouched in `~/Downloads/Code/`; canonical copies archived.

## B. Speaker Classification (from embedded `metadata.json`, self-reported)

| Batch | Speaker ID | Gender | Age | Region/Province | Files | Session |
|---|---|---|---|---|---|---|
| A2 | `LH_A2` | Nam | 18 | Nam / TP.HCM | 80 | complete (80/80 prompts) |
| A3 | `LH_A3` | Nam | 20 | Trung / Bình Định | 80 | complete (80/80) |
| A4 | `LH_A4` | Nam | 20 | Nam / Đồng Nai | 1 | **incomplete (1/80)** ⚠️ |

All confirmed **Nam U20** → placed under `Lê Hà/Nam 20/` per existing collector/group/batch hierarchy. Three distinct subjects (distinct provinces & export dates). Note: A2 and existing batch `A` share app subject-id `"A"` and province (TP.HCM) but different self-reported age (18 vs 20) and zero shared content — treated as distinct speaker; flagged in §G.

## C. Duplicate Audit

Method: raw **MD5** of extracted bytes vs full corpus (2,795 files incl. archives-extracted backup); then normalized **PCM-MD5** — every file decoded to 16 kHz/mono/int16 via the same PyAV resampler the pipeline uses (covers re-encodes and raw-only batches B7/B8, F30_05). Filename never used as a criterion.

| ZIP | Total | NEW | Raw Dup | Processed Dup | Name Collision* | Invalid |
|---|---|---|---|---|---|---|
| A2 | 80 | **80** | 0 | 0 | 80 | 0 |
| A3 | 80 | **80** | 0 | 0 | 80 | 0 |
| A4 | 1 | **1** | 0 | 0 | 1 | 0 |

\* Name collisions = same basenames as batch `A` (`A_A_*`) and Trẻ con/batch A (`A_C*`) with **different content** — by design; resolved via `_dupN` sample_id suffix in manifests (filenames on disk unchanged).

## D. Integration Summary

| Layer | Destination |
|---|---|
| Raw archives | `data/raw/archives/Lê Hà/Nam 20/{A2,A3,A4}.zip` |
| Raw audio | `data/raw/real_voice/Lê Hà/Nam 20/{A2,A3,A4}/` (+ `metadata.json` each) |
| Processed audio | `src/data/stt/processed/real_voice/wav/Lê Hà/Nam 20/{A2,A3,A4}/` — WAV PCM_16 16 kHz mono via `scripts/convert_audio.py` (PyAV path, identical to prior batches) |

- **Naming:** exporter filenames preserved on disk; batch dirs named after zips (A2/A3/A4) matching convention (`A`, `B`, `B1`…). Manifest `sample_id`s disambiguated: `A_A_*` stems → `_dup1/_dup2/_dup3`, `A_C*` stems → `_dup2/_dup3` (continuing per-stem sequence).
- **Manifests updated** (backups `*.pre_nam_u20_backup` created first):
  - `download_manifest.csv` +167 rows (3 zip + 3 metadata.json + 161 members, md5+duration verified)
  - `stt_dataset_manifest.csv` +161 rows
  - `finetuning/datasets/unannotated/metadata.csv` +161 rows (`pending_transcription`, intent/script from `data/annotations.json`)
- **New dirs created:** 3 archive zips, 3 raw batch dirs, 3 processed batch dirs. No restructure, no overwrites, no deletions.

## E. Before / After Statistics

| Metric | Before | Added | After |
|---|---|---|---|
| Raw audio (`real_voice/`) | 1,372 | +161 | **1,533** |
| Processed WAV (16k mono) | 1,143 | +161 | **1,304** |
| ZIP archives (`archives/`) | 13 | +3 | **16** |
| Distinct speakers (manifest) | 12 | +3 | **15** |
| Unannotated records | 956 | +161 | **1,117** |
| Nam 20 audio (male U20 pool) | 150 | +161 | **311** ≈ 9.6 min added |

(Before-figures reflect on-disk state incl. post-`REPORT DATA.md` B7/B8 raw dirs.)

## F. Validation Results

| Check | Result |
|---|---|
| ZIPs processed 3/3, integrity OK | ✅ PASS |
| New audio files integrated | ✅ PASS — 161/161 raw→processed 1:1 |
| Duplicate check (raw MD5 + PCM-MD5 vs 2,795 files) | ✅ PASS — 0 dups, incl. B7/B8/F30_05 raw-only pools |
| Broken/corrupt files | ✅ PASS — 0 decode errors |
| Naming convention / `_dupN` uniqueness | ✅ PASS — 1,117 unique sample_ids |
| `validate_dataset.py` | ✅ PASS — 0 errors (1 pre-existing warning: empty supervised splits) |
| Manifest↔filesystem: every new path exists, md5/size/duration match | ✅ PASS — 167/167 DM rows md5-verified, 161/161 DS rows 16 kHz mono |
| Batch `A` + all prior data untouched | ✅ PASS — byte-level unchanged |
| STT pipeline compatibility | ✅ PASS — processed WAVs decode via soundfile/PyAV |

## G. Issues & Recommendations

1. ⚠️ **A4 is an incomplete session** — only `A_A_01_r.wav` (1/80 prompts, 3.7 s). Imported as its own batch for provenance; consider re-requesting the full export or merging into a future re-export of that subject.
2. ⚠️ **A2 vs batch `A` speaker identity ambiguous** — same app subject-id `"A"`, same city (TP.HCM), conflicting self-reported age (18 vs 20), but **zero content overlap**. Kept as `LH_A2` (distinct subject). If confirmed same person, merge under `LH_A` later — manifests make this a cheap relabel.
3. ℹ️ **B7/B8 (Nữ 20) remain filesystem-only** — raw + archive present since 2026-11-01 but **no processed WAVs and no manifest rows** (pre-existing gap, out of scope here). Recommend a follow-up import run using this same procedure.
4. ℹ️ **F30_05** storage-only status unchanged (known decision pending per `REPORT DATA.md`).
5. ℹ️ `audio_inventory.csv` + `REPORT DATA.md` (2026-11-01 snapshot) are now stale — regenerate next audit cycle.
6. ℹ️ 5 Giọng clone WAVs are non-16 kHz PCM (synthetic, excluded by design — no action).
7. 💡 Exporter keeps reusing subject-id `"A"` and the inner `A/` folder for different people; batch-dir naming (zip name) is the only reliable discriminator — keep current convention of never renaming member files.
