# F30 BATCH RENAMING & EXTRACTION AUDIT

**Date:** 2026-11-01
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh`
**Scope:** correct batch naming F30_03 → F30_04; verify F30_05 & B4 — no re-import, no data deleted.

---

## 1. Batch Name Mapping

| Source ZIP | Previous name | Correct name | Status |
|---|---|---|---|
| local `Downloads/Nữ/F30_3.zip` | `F30_03` | **`F30_04`** | renamed everywhere |
| local `Downloads/Study/Nữ/F30_4.zip` | `F30_05` | `F30_05` | already correct — kept |
| local `Downloads/Study/Nữ/F30_5.zip` | `F30_O6` | `F30_O6` | **still MISSING** — not created |

## 2. Renamed Paths

| Level | Before | After |
|---|---|---|
| Archive | `data/raw/archives/Lê Hà/Nữ 30/F30_03.zip` | `…/F30_04.zip` |
| Raw | `data/raw/real_voice/Lê Hà/Nữ 30/F30_03/` | `…/F30_04/` |
| Processed | `src/data/stt/processed/real_voice/wav/Lê Hà/Nữ 30/F30_03/` | `…/F30_04/` |

Contents unchanged (rename only — 70 wav + metadata.json each level;
processed WAVs were already valid 16 kHz mono PCM_16, **not** re-converted).
`sample_id`s (`F30_*_dup3`), speaker_id `LH_F30_4`, and all annotation/status
fields untouched.

## 3. Extraction State per Batch (verified on disk)

| Batch | Archive zip | Raw dir | Processed dir | Records |
|---|---|---|---|---|
| `F30_01` | F30_01.zip | F30_01/ (70 wav + meta) | F30_01/ (70 wav) | 70 (LH_F30_3) |
| `F30_02` | F30_02.zip | F30_02/ (70 wav + meta) | F30_02/ (70 wav) | 70 (LH_F30_2) |
| `F30_04` | F30_04.zip | F30_04/ (70 wav + meta) | F30_04/ (70 wav) | 70 (LH_F30_4) |
| `F30_05` | F30_05.zip | *(not extracted — duplicate)* | — | 0 |
| `F30_O6` | — | — | — | 0 (source missing) |
| `B4` | B4.zip | `Nữ 20/B4/` (80 wav + meta) | `Nữ 20/B4/` (80 wav) | 80 (LH_B4) |

## 4. F30_05 Duplicate Verification (re-checked)

- `F30_05.zip` member-md5 vs canonical `F30_01/`: **70/70 identical** (re-verified
  2026-11-01). Canonical `F30_01/` present and complete (70 files).
- No extraction, no copied audio, no dataset records — logged
  `duplicate_skipped` in `download_manifest.csv` pointing at canonical files.

## 5. Manifest Changes

| Manifest | Change |
|---|---|
| `unannotated/metadata.csv` | 70 rows: `voice_group`, `audio_path`, `raw_path`, `reviewer_notes` → F30_04 (280 field edits) |
| `review_queue.csv` | 70 rows: `audio_path`, `reason` → F30_04 (140 edits) |
| `stt_dataset_manifest.csv` | 70 rows: `wav_relpath`, `note` → F30_04 (140 edits) |
| `download_manifest.csv` | 72 new-batch rows → F30_04 paths (144 edits); **72 old `duplicate_removed` rows annotated** to clarify they refer to the *removed Drive export* formerly at the `F30_03` name (history preserved, not rewritten) |

No sample_id, transcript, GT, annotation, or review-status field modified.
All pre-existing non-F30_04 rows verified unchanged.

## 6. Validation

`validate_dataset.py` → **PASS** (1 pre-existing warning: supervised splits empty)

| Check | Result |
|---|---|
| Audio paths verified | 1066 |
| Broken paths | 0 |
| Duplicate sample_id | 0 |
| F30_04 rows / paths valid | 70 / all exist |
| Stray `F30_03` refs in active manifests | 0 (only 72 `duplicate_removed` history rows, annotated) |
| New audio imported | 0 (rename-only task) |
| Records lost/changed out of scope | 0 |

## 7. Open Issues

- **`F30_5.zip` (→ `F30_O6`) still missing** — needs to be provided by the team.
- Naming reuse note: batch slot `F30_03` now permanently maps to the local
  `F30_3.zip` (LH_F30_4); the earlier removed Drive export's history is kept in
  `download_manifest.csv` as `duplicate_removed` with clarifying notes.
