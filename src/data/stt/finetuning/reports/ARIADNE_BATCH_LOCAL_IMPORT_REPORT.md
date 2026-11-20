# ARIADNE BATCH LOCAL ZIP IMPORT REPORT

**Date:** 2026-11-01
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh`
**Source:** local files under `/Users/pickapu/Downloads/Study/` (not Google Drive; sources left in place, SHA-256 re-verified unchanged post-import)

---

## A. ZIP Source Audit

10 ZIP objects audited: 9 standalone files in `Downloads/Study/` + `Nữ (2).zip`,
a **container** zip holding the whole `Nữ/` folder as 9 nested member zips.
8 of the 9 nested zips are **byte-identical** to the standalone files; the 9th is
`Nữ/F30_5.zip` — the zip previously reported MISSING (reserved slot `F30_O6`).

| ZIP | Source path | Size (bytes) | SHA-256 | Integrity | Audio | Real format | Classification |
|---|---|---|---|---|---|---|---|
| `B1.zip` | `Downloads/Study/Nữ/` | 8,112,047 | `1a9517fb…d55c0e` | OK | 80 | AAC/MP4 48k mislabeled `.wav` | FULL DUP of `Nữ 20/B (2)` (LH_B2) — logged in prior import |
| `B2.zip` | `Downloads/Study/Nữ/` | 7,803,183 | `bd75c95f…ea83ac` | OK | 80 | AAC/MP4 48k | FULL DUP of `Nữ 20/Bản sao của B` (LH_B3) — prior |
| `B3.zip` | `Downloads/Study/Nữ/` | 5,764,653 | `6e989e14…099be3` | OK | 80 | WebM/Opus 48k | FULL DUP of `Nữ 20/B` (LH_B1) — prior |
| `B4.zip` | `Downloads/Study/Nữ/` | 4,348,476 | `43b120e0…446c73` | OK | 80 | WebM/Opus 48k | Already imported → `Nữ 20/B4` (LH_B4) — prior |
| `F30_1.zip` | `Downloads/Study/Nữ/` | 4,776,755 | `06ee3181…ddecb` | OK | 70 | WebM/Opus 48k | **Byte-identical** to archived `F30_04.zip` (LH_F30_4, Nữ 30 Trung/Bình Thuận) — re-audit row only |
| `F30_2.zip` | `Downloads/Study/Nữ/` | 11,489,244 | `6c547130…3d97` | OK | 70 | WebM/Opus 48k | **Byte-identical** to archived `F30_02.zip` (LH_F30_2, Nữ 28 Quảng Ngãi) — re-audit row only |
| `F30_3.zip` | `Downloads/Study/Nữ/` | 4,408,831 | `6adbc647…aef9e` | OK | 70 | WebM/Opus 48k | **NEW** → batch `F30_07` (LH_F30_5, Nữ 30 Nam/Bảo Lộc) |
| `F30_4.zip` | `Downloads/Study/Nữ/` | 5,432,318 | `8c925169…6ae5` | OK | 70 | WebM/Opus 48k | **Byte-identical** to archived `F30_05.zip` — dup of `F30_01` |
| `Nữ (2).zip` | `Downloads/Study/` | 57,038,044 | `c6d0d3fa…25d4a` | OK | container (9 nested zips) | — | folder export; indexed, member zips handled individually |
| `Nữ/F30_5.zip` | nested in `Nữ (2).zip` | 5,432,318 | `09fa8917…3bb0` (as archived) | OK | 70 | WebM/Opus 48k | Previously-missing zip → archived as `F30_06.zip`; FULL DUP of `F30_01` (71/72 members identical to `F30_4.zip`, only `metadata.json` exportDate differs) |

- `unzip -t` passed for every object. No path traversal, no `__MACOSX`, no hidden files.
- Container `Nữ (2).zip` itself is **not copied** into the repo (57 MB of already-archived
  member zips); it is indexed in `download_manifest.csv`. The only unique member,
  `Nữ/F30_5.zip`, is preserved as `F30_06.zip`.
- Subject self-reports (metadata.json): F30_1 = Nữ 30 Trung/Bình Thuận ·
  F30_2 = Nữ 28 Nam/Quảng Ngãi · **F30_3 = Nữ 30 Nam/Bảo Lộc (new)** ·
  F30_4 / F30_5 = Nữ 30 Nam/(blank).

## B. Audio Deduplication

Method: member-level raw **MD5** vs all 1,073 pre-existing raw audio files, plus decoded
**PCM-MD5** (16 kHz mono) vs all 1,073 processed wavs. Filenames used only as reference.

| Metric | Count |
|---|---|
| Total audio members audited (standalone + unique nested F30_5) | 670 |
| **New audio** (0 raw-md5 hits AND 0 PCM-md5 hits) | **70** — all in `F30_3.zip` |
| Exact duplicates (md5-identical to existing raw) | 600 |
| — already logged in prior imports (B1–B4, F30_4→F30_05) | 390 |
| — re-audit: `F30_1.zip` 70/70 → `F30_04`, `F30_2.zip` 70/70 → `F30_02` | 140 |
| — `F30_5.zip` 70/70 → `F30_01` | 70 |
| Same filename, different content | 0 (all same-named files were byte-identical) |
| Invalid / corrupt audio | 0 |

Duplicate locations: `F30_5.zip` members → `data/raw/real_voice/Lê Hà/Nữ 30/F30_01/`;
`F30_1.zip` → `…/F30_04/`; `F30_2.zip` → `…/F30_02/`; `B1` → `Nữ 20/B (2)/`;
`B2` → `Nữ 20/Bản sao của B/`; `B3` → `Nữ 20/B/`; `B4` → `Nữ 20/B4/` (prior import).
No dataset records were created for duplicate audio — provenance only in `download_manifest.csv`.

## C. Subject Classification

| Subject (speaker_id) | Gender/Age | Group | Batch | Source ZIP | Audio |
|---|---|---|---|---|---|
| **LH_F30_5** (id `F30`, self-report) | Nữ 30, Nam/Bảo Lộc | `Lê Hà/Nữ 30` | **`F30_07`** | `F30_3.zip` | **70 new** |
| LH_F30_3 | Nữ 30, Nam/— | `Lê Hà/Nữ 30` | `F30_06` (archive only) | nested `F30_5.zip` | 70 dup |
| LH_F30_4 | Nữ 30, Trung/Bình Thuận | `Lê Hà/Nữ 30` | `F30_04` (existing) | `F30_1.zip` re-export | 70 dup |
| LH_F30_2 | Nữ 28, Nam/Quảng Ngãi | `Lê Hà/Nữ 30` | `F30_02` (existing) | `F30_2.zip` re-export | 70 dup |
| LH_B1–B4 | Nữ 19–20 | `Lê Hà/Nữ 20` | existing batches | B1–B4 re-exports | 320 dup |

1 new subject classified (**LH_F30_5**, the 5th distinct F30 speaker);
0 audio left unclassified; no mixed-subject zips.

## D. Preprocessing Results (F30_07 only — new content)

Pipeline: existing `scripts/convert_audio.py` (PyAV → WAV 16 kHz mono PCM_16), unchanged.

| Metric | Count |
|---|---|
| Successfully processed | **70 / 70** |
| Processing failed | 0 |
| Invalid audio | 0 |
| Silent / empty / <0.5 s | 0 |
| Heavy clipping (>1% samples at max) | 0 |
| Duplicate PCM checksum vs dataset | 0 |

Output spec verified per file: 16,000 Hz / mono / PCM_16.
Duration 2.58–7.92 s, total ≈ 5.2 min. No trimming, no noise reduction, raw untouched.
1:1 raw↔processed mapping verified (70 = 70, identical filename sets).

## E. Manifest Changes

Backups written before append: `*.pre_f30_07_backup` next to each modified CSV.

| Manifest | Before | Added | After |
|---|---|---|---|
| `finetuning/datasets/unannotated/metadata.csv` | 886 | **+70** | **956** |
| `finetuning/reports/review_queue.csv` | 1066 | **+70** | **1136** |
| `manifests/stt_dataset_manifest.csv` | 1073 | **+70** | **1143** |
| `manifests/download_manifest.csv` | 1481 | **+147** | **1628** |

`download_manifest` additions: 1 container row + 2 re-audit zip rows (F30_1/F30_2) +
72 F30_06 rows (1 zip + 70 `duplicate_skipped` + 1 metadata) + 72 F30_07 rows
(1 zip + 70 `extracted` + 1 metadata).
Duplicate-member rows excluded from dataset records: 70 (F30_06).
New rows pending transcription: 70.

- `sample_id`: `F30_*_dup4` (70) — `_dupN` convention continues
  (`_dup1`=F30_01, `_dup2`=F30_02, `_dup3`=F30_04, `_dup4`=F30_07).
- `speaker_id` = `LH_F30_5`; `voice_group` = `Lê Hà/Nữ 30/F30_07`.
- `script_reference`: 20 rows inferred via shared C-code convention
  (`F30_C*`, `script_inferred=1`); 50 rows none (`F30_T*` — T prompts have no script
  in `data/annotations.json`).
- `transcript_status` = `pending_transcription` ×70; **no** GT, **no** ASR
  prediction, **no** priority classification; all rows `unannotated`.

## F. Dataset Integrity

| Check | Result |
|---|---|
| Existing rows modified | **0** — all pre-import rows byte-identical to `*.pre_f30_07_backup` in all 4 manifests |
| Annotation / Ground Truth changed | none |
| Human review status changed | none |
| Unverified audio in supervised splits | none (all new rows `unannotated`; splits still empty) |
| Files overwritten / deleted | **0** — `F30_07` is a fresh directory; `F30_06.zip` a new archive name |
| Nam 20 / Nam 30 / Nữ 20 / F30_01 / F30_02 / F30_04 data | untouched |

## G. Validation

`.venv/bin/python src/data/stt/finetuning/scripts/validate_dataset.py` → **PASS**
(1 pre-existing warning: supervised splits empty — unrelated to this import).

| Check | Result |
|---|---|
| All source ZIPs integrity (`unzip -t`) | PASS (10/10 objects) |
| Source SHA-256 unchanged post-import | PASS (`6adbc647…`, `c6d0d3fa…` re-verified) |
| Duplicate sample_id (all pools) | 0 |
| Broken raw/processed paths | 0 (1,136 rows verified) |
| raw↔processed mapping | 1:1 (70/70) |
| Records for fully-duplicate audio | 0 |
| New unverified audio in train/val/test | 0 |
| Speakers after import | 12 (`LH_F30_5` registered) |
| **Overall** | **PASS** |

## H. Final Directory Tree

```
data/raw/real_voice/Lê Hà/Nữ 30/
├── F30_01/   70 wav + metadata.json   (LH_F30_3)
├── F30_02/   70 wav + metadata.json   (LH_F30_2)
├── F30_04/   70 wav + metadata.json   (LH_F30_4)
└── F30_07/   70 wav + metadata.json   (LH_F30_5 — NEW, Nam/Bảo Lộc)

data/raw/archives/Lê Hà/Nữ 30/
├── F30_01.zip  ├── F30_02.zip  ├── F30_04.zip
├── F30_05.zip  (dup of F30_01, archive only)
├── F30_06.zip  (nested F30_5.zip — previously missing; dup of F30_01, archive only)
└── F30_07.zip  (local F30_3.zip — NEW)

src/data/stt/processed/real_voice/wav/Lê Hà/Nữ 30/
├── F30_01/  ├── F30_02/  ├── F30_04/  └── F30_07/   (70 wav each, 16kHz mono PCM_16)
```

## Open Notes

- `F30_06` resolves the previously-open `F30_O6` slot: the missing zip turned out to
  be another duplicate export of `F30_01` — archive-only, zero dataset records.
- Source-zip name collision: `Downloads/Study/Nữ/F30_3.zip` (new, Bảo Lộc) differs
  from the earlier `Downloads/Nữ/F30_3.zip` (Bình Thuận → batch `F30_04`).
  Disambiguated by SHA-256 in all manifest notes.
- 10 pre-existing in-dataset PCM collisions exist among older files
  (1,143 wavs → 1,063 unique PCM); unrelated to this import — flagged for the team.
