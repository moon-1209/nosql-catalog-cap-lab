# HÀ LÊ (Lê Hà) VOICE DATA IMPORT REPORT

**Date:** 2026-10-30
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh`
**Source:** Google Drive folder `1tnp8mY7TyFq7wpwCVWtgLCmTOJipJhW0` → subfolder **`Lê Hà`**

---

## 0. Naming discrepancy (user-confirmed)

No folder named exactly `Hà Lê` exists on the Drive. The only new folder since the
previous audit (2026-10-27) is **`Lê Hà`** (surname-first order). The user confirmed
this is the intended folder; all imports below reference `Lê Hà`.

**Important structural finding:** each ZIP inside `Lê Hà` is a **different recording
subject** (self-reported metadata differs per zip — age/gender/region/province).
The Drive age-group folders are demographic buckets, not single-speaker folders.

---

## A. Google Drive Inventory

Recursive enumeration via `gdown --folder --json` (gdown 6.4.2, public share).
8 ZIP files found under `Lê Hà/`:

| Drive path | File ID | Size (bytes) | Inner folder | Files | Subject (self-reported) |
|---|---|---|---|---|---|
| `Lê Hà/Nam 20/A.zip` | `1eiMcAJ7ATK6PNFX7mdk6iVZpQcXwy-ns` | 7,120,513 | `A/` | 80 wav + metadata.json | Nam 20, Nam/TpHcM |
| `Lê Hà/Nam 30/Bản sao của M30.zip` | `1PbATeVtShnwRSgFpSrtWdvKuhg1a5xum` | 4,340,714 | `M30/` | 70 wav + metadata.json | Nam 30, Nam/TP.hcm |
| `Lê Hà/Nữ 20/B.zip` | `13HllFBqp_mKD_j7RAZHEDLsyueJSSrUz` | 5,764,653 | `B/` | 80 wav + metadata.json | Nữ 20, Nam/TPHCM |
| `Lê Hà/Nữ 20/B (2).zip` | `1NSa4NyD_G8WqVis_I_K-yQd7h8pfmQDu` | 8,112,047 | `B/` | 80 wav + metadata.json | Nữ 20, Trung/Quảng Ngãi |
| `Lê Hà/Nữ 20/Bản sao của B.zip` | `11p8iKmuZysIRHm7QEdejWjalufTAtgyP` | 7,803,183 | `B/` | 80 wav + metadata.json | Nữ 20, Bắc/hải phòng |
| `Lê Hà/Nữ 30/F30.zip` | `1l8tJ3lOi_mjiJxj2HVcbwD1CxNpuAceD` | 9,054,359 | `F30/` | 70 wav + metadata.json | Nữ **34**, Nam/Hà Nam |
| `Lê Hà/Nữ 30/Bản sao của F30.zip` | `16Jupd15cOaVroBsKV3PVFx-wVOZWBRIq` | 11,489,244 | `F30/` | 70 wav + metadata.json | Nữ 28, Nam/Quảng Ngãi |
| `Lê Hà/Nữ 30/Bản sao của F30.zip` ⚠ | `1pQJV80FbYrmYugudK5iccMLmdTx6_tcW` | 11,489,244 | `F30/` | 70 wav + metadata.json | Nữ 28, Nam/Quảng Ngãi |

⚠ Two distinct Drive files share the same name `Bản sao của F30.zip`; downloaded locally
as `Bản sao của F30.zip` and `Bản sao của F30 (2).zip`. Their zip md5s differ only due to
`metadata.json` exportDate — **all 70 member wavs are md5-identical** (see §B).

**Age groups discovered:** `Nam 20`, `Nam 30`, `Nữ 20`, `Nữ 30` (verbatim Drive names).
**Distinct subjects:** 7 (one speaker per zip; the 8th zip is a re-export).

Download: 8 found = 8 succeeded + 0 failed. All pass `unzip -t` integrity.
No path-traversal entries, no `__MACOSX`/hidden files, no nested zips.

**Format anomaly:** every member file is named `*.wav` but is actually
- `A.zip`, `M30`, `B.zip`, both `F30` zips → **WebM/Opus 48 kHz mono** (440 files)
- `B (2).zip`, `Bản sao của B.zip` → **MP4/AAC 48 kHz mono** (160 files)

Recorded in `download_manifest.csv` note field (`actual container=...`).

---

## B. Extraction Results

600 member wavs extracted to staging, checksummed, then organized into
`data/raw/real_voice/Lê Hà/<age group>/<subject folder>/`.
Subject folder = zip-internal top folder; disambiguated by zip stem where
multiple zips share the same inner name (`B (2)`, `Bản sao của B`, `Bản sao của F30`).
Original filenames kept verbatim; `metadata.json` kept alongside each subject.

| Age group | Subject folder | Wavs | md5-verified vs other zips |
|---|---|---|---|
| `Nam 20/` | `A/` | 80 | unique |
| `Nam 30/` | `M30/` | 70 | unique |
| `Nữ 20/` | `B/` | 80 | unique (0 identical to other B zips) |
| `Nữ 20/` | `B (2)/` | 80 | unique (0 identical to other B zips) |
| `Nữ 20/` | `Bản sao của B/` | 80 | unique (0 identical to other B zips) |
| `Nữ 30/` | `F30/` | 70 | unique (0 identical to Bản sao zips) |
| `Nữ 30/` | `Bản sao của F30/` | 70 | unique |
| — | `Bản sao của F30 (2)` (archive only) | 70 | **70/70 md5-identical to `Bản sao của F30`** → NOT integrated |

**Integrated wavs: 530.** Duplicate-export wavs: 70 (kept in
`data/raw/archives/Lê Hà/_staging/`; logged as `duplicate_skipped` in
`download_manifest.csv`).

Filename sets per subject:
- `A/`: `A_A_01..30_{r,n}` (60) + `A_C01..C10_{r,n}` (20)
- `M30/`: `M30_T01..T25_{r,n}` (50) + `M30_C01..C10_{r,n}` (20)
- `B*/` (×3): `B_B_01..30_{r,n}` (60) + `B_C01..C10_{r,n}` (20)
- `F30*/` (×2): `F30_T01..T25_{r,n}` (50) + `F30_C01..C10_{r,n}` (20)

Cross-dataset check: PCM-md5 of all 530 processed wavs vs all 393 existing
processed wavs → **0 matches** (no re-uploaded recordings).

---

## C. Preprocessing Results

Pipeline: existing `scripts/convert_audio.py` (PyAV → WAV 16 kHz mono PCM_16),
run as `--src data/raw/real_voice/Lê Hà --dest src/data/stt/processed/real_voice/wav/Lê Hà`.

| Metric | Value |
|---|---|
| Converted | **530 / 530** |
| Failed | 0 |
| Output spec | 16000 Hz, mono, PCM_16 — verified for all 530 via soundfile |
| Empty / silent / <0.5 s | 0 |
| Heavy clipping (>1% samples at ±max) | 0 |
| Duration range | 2.13 s – 10.92 s |
| Total audio | ~39.3 min |

Per-subject (processed): `Nam 20/A` 80 (4.3 min) · `Nam 30/M30` 70 (4.6 min) ·
`Nữ 20/B` 80 (6.1) · `Nữ 20/B (2)` 80 (5.9) · `Nữ 20/Bản sao của B` 80 (5.6) ·
`Nữ 30/F30` 70 (5.6) · `Nữ 30/Bản sao của F30` 70 (7.2).

No trimming, no noise reduction, raw audio untouched. 1:1 raw↔processed mapping
verified (0 orphans both directions).

---

## D. Dataset Integration

| Manifest | Before | Added | After |
|---|---|---|---|
| `finetuning/datasets/unannotated/metadata.csv` | 206 | **+530** | 736 |
| `finetuning/reports/review_queue.csv` | 386 | +530 | 916 |
| `manifests/stt_dataset_manifest.csv` | 393 | +530 | 923 |
| `manifests/download_manifest.csv` | 393 | +616 | 1009 |

download_manifest additions: 8 zip rows + 7 metadata.json rows + 530 integrated
wav rows + 70 `duplicate_skipped` rows + 1 dup-zip metadata row.

Backups written before append: `*.pre_leha_backup` next to each modified CSV.

**sample_id convention:** filename stem; on collision → `_dupN` (existing
convention, e.g. `A_01_r_dup1`). 340 of 530 new ids carry a `_dupN` suffix because
stems collide either with existing ids (`F30_*`, `A_C*`, `B_C*`) or across the
new same-labeled subjects (`B_B_*`, `F30_*`). Assignment order: A, M30, B,
B (2), Bản sao của B, F30, Bản sao của F30. `_dupN` here means "same prompt code,
different subject" — reviewer_notes on each such row state this explicitly.

**speaker_id (new):** `LH_A`, `LH_M30`, `LH_B1`, `LH_B2`, `LH_B3`, `LH_F30_1`,
`LH_F30_2` — from each zip's `metadata.json` (self-reported; recorded as source
metadata, not independently verified).

**script_reference:** filled only from `data/annotations.json` prompt-code mapping —
430 rows direct code match (`A_NN`, `B_NN`, `A_CNN`, `B_CNN`), 60 rows
C-code-inferred (`F30_C*`, `M30_C*`; flagged `script inferred from C-code
convention`, `script_inferred=1`), 40 rows none (`F30_T*`, `M30_T*`; `T` prompts
have no script in annotations). **No GT created; `transcript_status` =
`pending_transcription` for all new rows; `model_prediction` left empty**
(PhoASR not run, per task). review_queue rows: `review_priority` left empty —
priority classification intentionally not run.

**Duplicate handling:**
- `Bản sao của F30 (2).zip`: 70/70 members md5-identical to `Bản sao của F30.zip`
  → not integrated; per-file `duplicate_skipped` rows in download_manifest;
  zip retained at `data/raw/archives/Lê Hà/Nữ 30/Bản sao của F30 (2).zip`.
- Same-filename-different-speaker collisions: kept as distinct samples with
  `_dupN` ids (they are NOT audio duplicates — 0 identical md5s across the three
  B subjects and two F30 subjects).

`proposed_finetune_splits.csv` unchanged (benchmark-only, 180 rows).
`data/annotations.{json,csv}` unchanged. All pre-existing rows in all four
modified manifests verified byte-identical after append.

---

## E. Validation

`python src/data/stt/finetuning/scripts/validate_dataset.py` → **PASS**
(1 pre-existing warning: supervised splits empty — unrelated to this import).

| Check | Result |
|---|---|
| ZIPs found = downloaded + failed | PASS (8 = 8 + 0) |
| Audio extracted | 600 (530 integrated + 70 skipped) |
| Preprocessing success/fail | 530 / 0 |
| Every processed wav has raw source | PASS (530/530) |
| Duplicate sample_id (all pools) | PASS (0; validator + manual) |
| Broken audio/raw paths | PASS (0; 916 rows verified) |
| Old records preserved | PASS (206→736, 386→916, 393→923, 393→1009; old rows byte-identical) |
| Old GT / review status changed | PASS (none touched) |
| Lê Hà rows in train/val/test | PASS (supervised splits empty; all new rows in `unannotated`) |

**Validation limits:** validator does not check review_queue.csv integrity
(manual append-consistency check performed); script_reference for new rows is a
reference only — all new audio remains unverified pending human review.

---

## F. Final Folder Trees

```
data/raw/real_voice/Lê Hà/                     (537 files: 530 wav + 7 metadata.json)
├── Nam 20/
│   └── A/                 80 wav + metadata.json
├── Nam 30/
│   └── M30/               70 wav + metadata.json
├── Nữ 20/
│   ├── B/                 80 wav + metadata.json
│   ├── B (2)/             80 wav + metadata.json
│   └── Bản sao của B/     80 wav + metadata.json
└── Nữ 30/
    ├── F30/               70 wav + metadata.json
    └── Bản sao của F30/   70 wav + metadata.json

src/data/stt/processed/real_voice/wav/Lê Hà/   (530 wav, mirrors raw)

data/raw/archives/Lê Hà/                       (source zips + staging)
├── Nam 20/A.zip
├── Nam 30/Bản sao của M30.zip
├── Nữ 20/{B.zip, B (2).zip, Bản sao của B.zip}
├── Nữ 30/{F30.zip, Bản sao của F30.zip, Bản sao của F30 (2).zip}
└── _staging/Nữ 30/Bản sao của F30 (2)/        (70 dup wavs, audit trail)
```

## G. Not done (per task rules / flagged for humans)

- No transcripts produced; all 530 files are `pending_transcription` in `unannotated`.
- No PhoASR predictions, no review-priority classification for new rows.
- No train/val/test assignment; no fine-tuning.
- `Nữ 30/F30` subject self-reports age 34 and `Bản sao của F30` age 28 — folder
  labels retained verbatim from Drive as required; ages kept as source metadata.
- Provenance note: subject ids (A/B/M30/F30) coincide with existing annotation
  speaker labels (A/B) but are **different people** — ids `LH_*` keep them distinct.
