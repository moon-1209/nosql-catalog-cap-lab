# F30_05 / F30_O6 / B1–B4 LOCAL IMPORT REPORT

**Date:** 2026-11-01
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh`
**Source:** local files `/Users/pickapu/Downloads/Study/Nữ/*.zip` (not Google Drive; sources left in place)

---

## A. ZIP Information

| ZIP | Local batch | Size (bytes) | SHA-256 (prefix) | Integrity | Subject (metadata.json) |
|---|---|---|---|---|---|
| `F30_4.zip` | `F30_05` | 5,432,318 | `8c925169…3d6ae5` | OK | F30, Nữ 30, Nam/blank — export 2026-11-01 |
| `F30_5.zip` | `F30_O6` | — | — | **MISSING — not found in source dir** | — |
| `B1.zip` | `B1` | 8,112,047 | `1a9517fb…d55c0e` | OK | B, Nữ 20, Trung/Quảng Ngãi |
| `B2.zip` | `B2` | 7,803,183 | `bd75c95f…ea83ac` | OK | B, Nữ 20, Bắc/hải phòng |
| `B3.zip` | `B3` | 5,764,653 | `6e989e14…099be3` | OK | B, Nữ 20, Nam/TPHCM |
| `B4.zip` | `B4` | 4,348,476 | `43b120e0…446c73` | OK | B, Nữ **19**, Nam/**Tây Ninh** — export 2026-10-28 |

- `F30_5.zip` (→`F30_O6`) **does not exist** in `/Users/pickapu/Downloads/Study/Nữ/`
  (dir contains F30_1..F30_4 only). No substitute created — flagged for the team.
- Actual audio format inside zips: WebM/Opus or AAC/MP4 48 kHz mono, all
  mislabeled `.wav` (same anomaly as previous Lê Hà batches).
- No path traversal, no nested zips, no hidden/`__MACOSX` entries in any zip.

## B. Duplicate Analysis (checksum-based)

Member md5 of every zip vs all existing raw files; decoded PCM-md5 (16 kHz mono)
vs all processed wavs:

| ZIP | Raw member-md5 vs dataset | PCM-md5 vs dataset | Verdict |
|---|---|---|---|
| `F30_4.zip` (F30_05) | **70/70 identical** → `Lê Hà/Nữ 30/F30_01/` | — | **FULL DUPLICATE** of LH_F30_3 set |
| `B1.zip` | **80/80 identical** → `Lê Hà/Nữ 20/B (2)/` | — | **FULL DUPLICATE** of LH_B2 set |
| `B2.zip` | **80/80 identical** → `Lê Hà/Nữ 20/Bản sao của B/` | — | **FULL DUPLICATE** of LH_B3 set |
| `B3.zip` | **80/80 identical** → `Lê Hà/Nữ 20/B/` | — | **FULL DUPLICATE** of LH_B1 set |
| `B4.zip` | **0/80 identical** | **0/80 identical** | **ALL NEW** — new subject `LH_B4` |

→ 80 new recordings (B4); 310 duplicate members across 4 zips; 0 corrupt files.
No records created for duplicate audio; provenance logged as `duplicate_skipped`.

## C. Storage

| Batch | Archive | Raw | Processed |
|---|---|---|---|
| `F30_05` | `data/raw/archives/Lê Hà/Nữ 30/F30_05.zip` | *(dup — not extracted; canonical `Nữ 30/F30_01/`)* | — |
| `B1` | `data/raw/archives/Lê Hà/Nữ 20/B1.zip` | *(dup — canonical `Nữ 20/B (2)/`)* | — |
| `B2` | `data/raw/archives/Lê Hà/Nữ 20/B2.zip` | *(dup — canonical `Nữ 20/Bản sao của B/`)* | — |
| `B3` | `data/raw/archives/Lê Hà/Nữ 20/B3.zip` | *(dup — canonical `Nữ 20/B/`)* | — |
| `B4` | `data/raw/archives/Lê Hà/Nữ 20/B4.zip` | `data/raw/real_voice/Lê Hà/Nữ 20/B4/` (80 wav + metadata.json) | `src/data/stt/processed/real_voice/wav/Lê Hà/Nữ 20/B4/` (80 wav) |

## D. Audio Processing (B4 only — new content)

- Converted **80/80** via existing `scripts/convert_audio.py` (PyAV).
- Spec verified per file: **16,000 Hz, mono, PCM_16**.
- Duration 1.80–5.46 s; total ~4.5 min.
- Silent/empty/<0.5 s: 0 · heavy clipping: 0 · failures: 0.
- No trimming, no noise reduction; 1:1 raw↔processed mapping verified.

## E. Dataset Statistics

| Manifest | Before | After | Δ |
|---|---|---|---|
| `unannotated/metadata.csv` | 806 | **886** | +80 |
| `review_queue.csv` | 986 | **1066** | +80 |
| `stt_dataset_manifest.csv` | 993 | **1073** | +80 |
| `download_manifest.csv` | 1081 | **1481** | +400 (5 zip + 80 B4 + 4 meta + 310 dup-skipped + 1 meta) |

## F. Annotation Status

- sample_id: `B_B_*_dup3` (60) and `B_C*_dup4` (20) — `_dupN` convention
  continues (`_dup1/2/3` already held by B / B (2) / Bản sao của B subjects).
- speaker_id `LH_B4`; voice_group `Lê Hà/Nữ 20/B4`.
- script_reference from `data/annotations.json` code map (B_NN, B_CNN — direct).
- `transcript_status = pending_transcription` ×80; **no** Ground Truth created,
  **no** ASR run, **no** priority classification; all rows `unannotated`.
- `F30_5.zip` (F30_O6): **NOT IMPORTED — source file missing.**

## G. Validation Results

| Check | Result |
|---|---|
| Audio paths verified | **1066** |
| Broken paths | **0** |
| Duplicate sample_id | **0** |
| Duplicate audio in dataset | 0 new (B4 all-new; dup zips excluded) |
| Existing records unchanged | PASS (all pre-import rows byte-identical to `*.pre_f30b_backup`) |
| Manifest consistency | PASS |
| Overall (`validate_dataset.py`) | **PASS** (1 pre-existing warning: supervised splits empty) |

## H. Final Verdict

- Found 5/6 requested zips; **`F30_5.zip` missing → F30_O6 not imported.**
- Imported **1 new batch: B4 (80 audio, speaker LH_B4)** — all new.
- **4 batches were exact duplicates** (F30_05, B1, B2, B3) — archived for
  provenance, `duplicate_skipped` in download_manifest, zero dataset records.
- 0 corrupted, 0 failed conversions, 0 overwrites.
- Outstanding: `F30_5.zip` needs to be provided by the team to complete F30_O6.
