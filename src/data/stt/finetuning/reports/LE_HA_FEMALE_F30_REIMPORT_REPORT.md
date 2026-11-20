# LÊ HÀ — NỮ 30 F30 REIMPORT REPORT

**Date:** 2026-10-30
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh`
**Scope:** replace ONLY the `Lê Hà/Nữ 30` F30 data from the previous import.
All other voice groups untouched.

---

## 1. The Three Updated ZIPs

Drive folder `Lê Hà/Nữ 30` (folder id `1BWDjVEITFRxfNQt63C17ESdbU7H7PkzP`)
currently contains **three distinct Drive files, all named `F30.zip`**.
Sorted by modified time ascending → local names:

| Local name | Drive File ID | modifiedTime (ms) | Size (bytes) | SHA-256 |
|---|---|---|---|---|
| `F30_01.zip` | `1_FSuKvESP2WB1CpRGOJxeAD7SiMh4PZS` | 1793344907001 | 5,432,318 | `7f002b06…9198ad72c` |
| `F30_02.zip` | `19DxeSrG2UDrVM8Ko67a2J6uUjwSlIAf5` | 1793348764212 | 11,489,244 | `ea772f3f…2eafb6c86f` |
| `F30_03.zip` | `1aSiW9yUsLAgWxTgydpU2of_ze2ZabwQG` | 1793349734077 | 11,489,244 | `6c547130…93459c4c3d97` |

All downloaded fresh via gdown (no local cache reuse), `unzip -t` clean,
no path traversal, no nested zips, no hidden/macOS files.
Each contains `F30/` with 70 `.wav` + `metadata.json`.

## 2. ZIP → Subject Mapping (from metadata.json)

| Local ZIP | Subject self-report | exportDate | Content verdict (checksum-verified) |
|---|---|---|---|
| `F30_01` | id F30, **Nữ 30**, region Nam, province (blank) | 2026-10-30T07:21Z | **70/70 NEW recordings** — new speaker `LH_F30_3` |
| `F30_02` | id F30, Nữ 28, Quảng Ngãi | 2026-10-30T08:25Z | 70/70 md5-identical to previously imported `Bản sao của F30` — same subject `LH_F30_2`, re-uploaded under the name `F30.zip` |
| `F30_03` | id F30, Nữ 28, Quảng Ngãi | 2026-10-30T08:41Z | 70/70 md5-identical to `F30_02` — duplicate export of the same session |

Member-level md5 comparison (all 70 wavs each):
`F30_01` vs `F30_02`: 0 identical · `F30_01` vs `F30_03`: 0 identical ·
`F30_02` vs `F30_03`: **70 identical**.
`F30_02`/`F30_03` vs old `Bản sao của F30` on disk: 70/70 identical (raw bytes
**and** decoded-PCM identical after conversion — double-verified).

**Answers the earlier question:** the previous "duplicate" verdict on the two
`Bản sao của F30` files was **correct at content level** — the two exports
carry byte-identical audio. The genuinely new speaker data in this update is
`F30_01` (age-30 subject), which did not exist in the previous zips.
The previous `F30.zip` subject (Nữ 34, Hà Nam) is **not present** in the new
set — her recordings were withdrawn from Drive and moved to backup.

## 3. Replacement & Backup

Pre-reimport state (backed up to `data/raw/_backup_f30_reimport_2026-10-30/`):
- 3 old zips (`F30.zip`, `Bản sao của F30.zip`, `Bản sao của F30 (2).zip`)
- raw dirs `Nữ 30/{F30, Bản sao của F30}` + `_staging/Nữ 30`
- processed dirs `wav/Lê Hà/Nữ 30/{F30, Bản sao của F30}`
- copies of all 4 manifests before edits

No old file deleted permanently — everything recoverable from backup.

## 4. Audio Extracted / Integrated

| ZIP | Raw extracted | Converted (16k/mono/PCM_16) | Dataset samples |
|---|---|---|---|
| `F30_01` | 70 + metadata.json | 70 | **70** (new) |
| `F30_02` | 70 + metadata.json | 70 | **70** (same audio, new canonical path) |
| `F30_03` | 70 + metadata.json | 70 | **0** — `duplicate_skipped` (md5-identical to F30_02) |

- Replaced: 140 old Nữ 30 records (LH_F30_1 + LH_F30_2 sets).
- Integrated: 140 records (70 `LH_F30_3` new + 70 `LH_F30_2` re-pathed).
- sample_ids: `F30_*_dup1` (F30_01), `F30_*_dup2` (F30_02) — same `_dupN`
  convention; all `pending_transcription`, no transcripts, no predictions.
- All 210 wavs: 16 kHz mono PCM_16, 0 errors, 0 silent/empty/clipped.
- Cross-dataset PCM check: 0 matches vs all other dataset audio.

## 5. Folder Structure

```
data/raw/real_voice/Lê Hà/Nữ 30/
├── F30_01/   70 wav + metadata.json   (subject LH_F30_3 — NEW)
├── F30_02/   70 wav + metadata.json   (subject LH_F30_2 — same audio re-uploaded)
└── F30_03/   70 wav + metadata.json   (duplicate export of F30_02 — audit trail)

data/raw/archives/Lê Hà/Nữ 30/
├── F30_01.zip  ├── F30_02.zip  └── F30_03.zip

src/data/stt/processed/real_voice/wav/Lê Hà/Nữ 30/
├── F30_01/  ├── F30_02/  └── F30_03/   (70 wavs each; F30_03 unmanifested)
```

## 6. Dataset Totals

| Manifest | Before | After | Δ |
|---|---|---|---|
| `unannotated/metadata.csv` | 736 | **736** | −140 old, +140 new |
| `review_queue.csv` | 916 | **916** | −140, +140 |
| `stt_dataset_manifest.csv` | 923 | **923** | −140, +140 |
| `download_manifest.csv` | 1009 | **1009** | −216, +216 |

(Expected counts 806/986/993 from the task do NOT apply: they assumed the
previously-skipped 70 were new content. Checksums proved F30_03 is a true
duplicate → 0 additional samples, replacements net to zero.)

## 7. Validation

`python src/data/stt/finetuning/scripts/validate_dataset.py` → **PASS**
(1 pre-existing warning: supervised splits empty).

| Check | Result |
|---|---|
| 3 distinct Drive File IDs present | PASS |
| ZIP integrity ×3 | PASS |
| Preprocessing | 210/210 OK |
| raw↔processed 1:1 | PASS (210/210) |
| Duplicate sample_id | PASS (0) |
| Broken paths | PASS (0; 916 rows verified) |
| Non-Nữ-30 manifest rows changed | **0** (byte-identical vs backup) |
| Nam 20 / Nam 30 / Nữ 20 data | untouched (81/71/243 files) |
| Original 393 recordings | untouched |
| Annotations / GT / review status | untouched |
| F30_03 in dataset records | 0 rows (correctly excluded) |
| New rows in supervised splits | none (supervised empty anyway) |

## 8. Caveats

- `F30_03` wavs exist on disk (raw + processed) for auditability but carry
  **no manifest records** — flagged `duplicate_skipped` in download_manifest.
- `LH_F30_3` (age 30) and `LH_F30_2` (age 28 QN) are distinct subjects;
  the withdrawn age-34 subject retains id `LH_F30_1` only in backup.
- All new audio: `pending_transcription`, unverified, no GT, no ASR draft.

---

## 9. F30_03 Duplicate Cleanup (2026-10-30)

Post-verification re-check confirmed `F30_03` carries **no active manifest
records** (0 rows in unannotated / review_queue / stt_dataset_manifest) and
70/70 member wavs md5-identical to `F30_02` (only `metadata.json` differs —
exportDate). Removed from local storage:

- `data/raw/archives/Lê Hà/Nữ 30/F30_03.zip` — deleted
- `data/raw/real_voice/Lê Hà/Nữ 30/F30_03/` — deleted (70 wav + metadata.json)
- `src/data/stt/processed/real_voice/wav/Lê Hà/Nữ 30/F30_03/` — deleted (70 wav)

**Manifest handling:** the 72 `download_manifest.csv` rows documenting the
F30_03 zip and its members were kept as provenance history with
`download_status = duplicate_removed` (was `downloaded`/`extracted`/
`duplicate_skipped`); a removal note was appended. No rows deleted, no other
manifest touched. Pre-reimport backup `data/raw/_backup_f30_reimport_2026-10-30/`
untouched — the removed content remains recoverable there.

**Post-cleanup validation:** `validate_dataset.py` → **PASS**;
counts unchanged — unannotated 736, review_queue 916, stt_dataset_manifest 923,
download_manifest 1009; 0 active rows reference missing files; `F30_01`/`F30_02`
and all other groups untouched.
