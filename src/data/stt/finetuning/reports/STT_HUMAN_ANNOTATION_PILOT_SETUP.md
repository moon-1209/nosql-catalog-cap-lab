# STT HUMAN ANNOTATION PILOT — SETUP REPORT

**Date:** 2026-10-27 · **Branch:** `quang-manh` · No data/status changes; no training; no commits.

## 1. Tool status — READY (verified by earlier live tests)

`scripts/review_tool.py` capabilities, all verified against code + live runs:
- **Record selection:** iterates rows whose status starts with `pending` — completed rows are skipped on resume.
- **Playback:** `afplay` per record; `r` replays; `--auto` plays + advances automatically.
- **Transcript entry:** `verbatim>` prompt → writes the correct field (`transcript_verified` for `--set r`, `verbatim_transcript` for `n`/`u`).
- **Status marking:** explicit reviewer choice from an allowed list — `verified_match/verified_corrected` (r) or `transcribed/verified` (n/u); `needs_manual_review`, `unusable_audio` for problem audio; invalid input leaves row pending.
- **Persistence:** atomic `.tmp`+rename write on `q` or exit; verified end-to-end (row1 write → file reload → status persisted; restore test also passed). Ctrl+C in `--auto` saves predictions-only progress.
- **GT safety:** `model_prediction` is a separate column, displayed as `ASR:`/`model:` — never copied into transcript fields; no auto-verify path exists.

## 2. Pilot batch — 30 records

File: `reports/pilot_review_batch_30.csv` — **20 × P1 quick-confirm + 10 × P2 keyword-diff**, first rows of the verified queue (`review_queue.csv`). Each row has `sample_id, audio_path, dataset_group, speech_mode, script_inferred, script_reference, model_prediction, review_priority, current_status, recommended_action`. All 30 audio paths verified to exist. Mix: 21 `_r` + 9 `_n` (no inferred F30_C rows in the first 30).

## 3. What the user does

```bash
cd /Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project
# P1 rows (dataset_group=pending_review or unannotated; check pilot CSV column)
.venv/bin/python src/data/stt/finetuning/scripts/review_tool.py --set r        # pending_review rows
.venv/bin/python src/data/stt/finetuning/scripts/review_tool.py --set n        # _n takes
.venv/bin/python src/data/stt/finetuning/scripts/review_tool.py --set u        # unannotated (kids/F30/M30/dup-takes)
```

Per record: audio plays (or press `r` to replay) → type the verbatim transcript (for P1, confirm script if it matches exactly → `verified_match`; if wording differs → `verified_corrected`) → Enter on status → optional note. `q` saves & quits; reopening skips finished rows.

Pilot rows span three manifest sets — check the `dataset_group` column to know which `--set` each row lives in.

## 4. Validation

`validate_dataset.py` → **PASS**, 0 errors, 386 paths OK. Warnings unchanged (empty supervised splits, 2 speakers). Manifests untouched by pilot setup — the batch is a reports-only CSV.

## 5. Known limitations

- Tool plays a whole manifest's pending list — no per-record jump by ID; find pilot IDs in order or keep the CSV beside you.
- P2 keyword flags mean *verify the medical term carefully*, not "prediction is wrong".
- `F30_C*` inferred scripts (none in this batch) still need audio confirmation.
- Nothing auto-verifies; transcripts only become verified through the typed-status flow.
