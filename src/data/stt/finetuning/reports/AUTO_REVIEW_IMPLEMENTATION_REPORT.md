# AUTO REVIEW IMPLEMENTATION REPORT

**Date:** 2026-10-27 · **Branch:** `quang-manh`

## A. Summary

Implemented `--auto` mode in `review_tool.py`: continuously plays each pending record's audio, runs the local PhoASR model when available, displays ID/group/script/ASR side-by-side, and auto-advances — no Enter needed. Predictions are stored **only** in `model_prediction`, never as transcript/GT. Not implemented: speaker-verified audio confirmation (no physical-speaker probe), per-record pause menu (Ctrl+C is the pause/save mechanism).

## B. Files changed

| File | Change | Why |
|---|---|---|
| `src/data/stt/finetuning/scripts/review_tool.py` | added `--auto`, `--limit`, `--dry-run`; lazy PhoASR loader (`get_asr`), `transcribe()`, atomic `save_csv()` (`.tmp`+rename), `auto_loop()` with KeyboardInterrupt→save | auto-advance review with safe resume |
| `datasets/unannotated/metadata.csv` | 3 rows gained real `model_prediction` values | evidence of real inference |

## C. Test evidence

| Test | Result | Evidence |
|---|---|---|
| A — CLI | **PASS** | `--help` lists all flags; `--set z` → clean `invalid choice` error |
| B — audio playback | **PASS (limited)** | `afplay` invoked per record in real run; all 3 records processed sequentially and program saved+exited. Physical speaker output not instrumented — cannot claim ears-on verification |
| C — ASR | **PASS** | `models/PhoASR-whisper-small` loaded via `local_files_only` (MPS on Apple Silicon); 3/3 real predictions, e.g. `F30_C01_n` → "Cho tôi hỏi khó tim mạch ở đâu". No mocks used |
| D — data integrity | **PASS** | diff before/after: exactly 3 changed cells, all `model_prediction`; sample IDs, transcripts, statuses, supervised splits, sources untouched; pending count still 206 |
| E — resume | **PASS** | second `--auto` run reused cached `model_prediction` (no re-inference), identical output; reviewed (non-pending) rows are skipped at status level |
| F — validator | **PASS** | 386 paths OK, 0 errors; warnings unchanged (empty supervised splits, 2 speakers) |

## D. ASR details

- Model: `models/PhoASR-whisper-small` (local Whisper-small ~242M), `local_files_only=True` — nothing downloaded.
- Device: MPS (Apple Silicon). 3 samples inferred, 0 failed; ~1–2 s/sample after one-time ~2 s load.
- Predictions are stored/displayed separately from `script_reference`; both shown to the reviewer. Prediction ≠ Ground Truth anywhere.

## E. Integrity

Before/after manifest diff: 3 cells (`model_prediction` only). No transcript/status/verified fields touched; train/validation/test remain header-only; sources/annotations unchanged.

## F. How to run

```bash
cd /Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project
.venv/bin/python src/data/stt/finetuning/scripts/review_tool.py --help
.venv/bin/python src/data/stt/finetuning/scripts/review_tool.py --set u --auto --limit 3 --dry-run   # safe trial
.venv/bin/python src/data/stt/finetuning/scripts/review_tool.py --set u --auto                      # full auto pass (Ctrl+C saves)
.venv/bin/python src/data/stt/finetuning/scripts/review_tool.py --set u                             # resume interactive transcription
.venv/bin/python src/data/stt/finetuning/scripts/validate_dataset.py                                # validator
```

## G. Limitations / remaining

- Physical audio output not verifiable by automation — user must confirm they hear playback.
- ASR errors don't abort the run (fallback = audio-only); if model fails to load, message printed once and playback continues.
- `--auto` never advances a row past `pending` — transcripts still require human typing in interactive mode (intended).
- 2-speaker limit and empty supervised splits persist until human verification completes.
