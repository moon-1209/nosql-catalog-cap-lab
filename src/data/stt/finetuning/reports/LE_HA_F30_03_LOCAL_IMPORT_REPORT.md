# LÊ HÀ — F30_03 LOCAL ZIP IMPORT REPORT

**Date:** 2026-10-31
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh`
**Source:** local file `/Users/pickapu/Downloads/Nữ/F30_3.zip` (not Google Drive)

---

## 1. Source ZIP

| Property | Value |
|---|---|
| Path | `/Users/pickapu/Downloads/Nữ/F30_3.zip` |
| Size | 4,776,755 bytes |
| SHA-256 | `06ee3181b01b523247d3b802750b2f800bea1bf481f582c2e211a64fb80ddecb` |
| Integrity | `unzip -t` OK; no path traversal, no hidden/`__MACOSX`, no nested zips |
| Contents | `F30/` → 70 `.wav` + `metadata.json` |
| Subject (self-report) | id `F30`, **Nữ 30**, region **Trung**, province **Bình Thuận** |
| exportDate | 2026-10-28T17:31:26Z |
| Actual audio format | WebM/Opus 48 kHz mono (mislabeled `.wav`) — same anomaly as previous Lê Hà zips |

**New subject** — metadata differs from all previously imported F30 subjects
(age 34/Hà Nam [withdrawn], age 28/Quảng Ngãi `LH_F30_2`, age 30/Nam `LH_F30_3`).
Assigned speaker_id **`LH_F30_4`** (4th distinct F30 subject).

## 2. Duplicate Verification (checksum-based, not filenames)

| Comparison | Result |
|---|---|
| Member md5 vs all `data/raw/real_voice/Lê Hà/` | **0/70 identical** |
| Member md5 vs backup `data/raw/_backup_f30_reimport_2026-10-30/` | **0/70 identical** |
| Decoded PCM md5 (16 kHz mono) vs **all** processed wavs in dataset | **0/70 identical** |

→ All 70 recordings are genuinely new. No duplicate records created or needed.

## 3. Storage

| Artifact | Location |
|---|---|
| Source archive | `data/raw/archives/Lê Hà/Nữ 30/F30_03.zip` (copy; source zip untouched — SHA-256 re-verified identical) |
| Raw audio | `data/raw/real_voice/Lê Hà/Nữ 30/F30_03/` — 70 wav + `metadata.json` |
| Processed WAV | `src/data/stt/processed/real_voice/wav/Lê Hà/Nữ 30/F30_03/` — 70 wav |

`F30_03` name reuses the slot freed by the earlier duplicate cleanup;
provenance disambiguated via manifest notes + speaker_id.

## 4. Preprocessing

Pipeline: `scripts/convert_audio.py` (PyAV → WAV 16 kHz mono PCM_16), same as all
prior imports. Result: **70/70 converted, 0 failures.**

- Spec verified per file: 16000 Hz / 1 ch / PCM_16
- Duration range 2.10–8.34 s; total ~4.9 min
- Silent/empty/<0.5 s: 0 · heavy clipping (>1% samples at max): 0
- No trimming, no noise reduction, raw untouched; 1:1 raw↔processed

## 5. Manifest Updates (append-only, backups `*.pre_f30_03_backup`)

| Manifest | Before | After | Added |
|---|---|---|---|
| `finetuning/datasets/unannotated/metadata.csv` | 736 | **806** | 70 |
| `finetuning/reports/review_queue.csv` | 916 | **986** | 70 |
| `manifests/stt_dataset_manifest.csv` | 923 | **993** | 70 |
| `manifests/download_manifest.csv` | 1009 | **1081** | 72 (1 zip + 70 wav + 1 metadata.json) |

- `sample_id`: `F30_*_dup3` (70 rows) — continues the `_dupN` convention;
  `_dup1` = F30_01 subject, `_dup2` = F30_02 subject, `_dup3` = F30_03 subject.
- `speaker_id` = `LH_F30_4`; `voice_group` = `Lê Hà/Nữ 30/F30_03`.
- `script_reference`: 20 rows inferred via shared C-code convention
  (`F30_C*`, flagged `script_inferred=1`); 50 rows none (`F30_T*` — T prompts
  have no script in `data/annotations.json`).
- `transcript_status` = `pending_transcription`; no GT, no ASR prediction,
  no priority classification; all rows in `unannotated`.
- download_manifest `drive_relative_path` uses `local_downloads/Nữ/F30_3.zip[::member]`
  to mark the non-Drive source; each row carries source-sha256 + member md5.

## 6. Validation

`python src/data/stt/finetuning/scripts/validate_dataset.py` → **PASS**
(1 pre-existing warning: supervised splits empty — unrelated).

| Check | Result |
|---|---|
| ZIP integrity + SHA-256 stable | PASS (source unchanged post-import) |
| Extracted wavs | 70/70 |
| Conversions | 70/70 |
| Duplicate sample_id (all pools) | 0 |
| Broken raw/processed paths | 0 (986 rows verified) |
| Records created for duplicate audio | 0 (none existed) |
| Old rows modified | 0 (byte-identical vs backup) |
| New data in supervised splits | none (all `unannotated`) |
| Other groups (Nam 20/Nam 30/Nữ 20/F30_01/F30_02) | untouched |

## 7. Final Trees

```
data/raw/real_voice/Lê Hà/Nữ 30/
├── F30_01/   70 wav + metadata.json   (LH_F30_3 — prior import)
├── F30_02/   70 wav + metadata.json   (LH_F30_2 — prior import)
└── F30_03/   70 wav + metadata.json   (LH_F30_4 — this import)

data/raw/archives/Lê Hà/Nữ 30/
├── F30_01.zip  ├── F30_02.zip  └── F30_03.zip  (local source)

src/data/stt/processed/real_voice/wav/Lê Hà/Nữ 30/
├── F30_01/  ├── F30_02/  └── F30_03/   (70 wav each)
```
