# GROUND TRUTH VERIFICATION REPORT

**Date:** 2026-10-27 · **Branch:** `quang-manh`
Scope: verification workflow + manifests only. No training, no model/dependency changes, no commits.

## Sample counts (verified against files)

| Pool | Count | Content |
|---|---|---|
| `_r` script-read recordings in `pending_review/metadata.csv` | 90 | all `verification_status=pending_review` — none human-verified yet |
| `_n` spontaneous recordings in `pending_transcripts/metadata.csv` | 80 | all `transcript_status=pending_transcription`, `verbatim_transcript` empty |
| `excluded/metadata.csv` | 10 | `Nu_C*` — byte-identical duplicates of `B_C*_r` |
| Supervised-eligible (train/validation/test) | **0** | emptied per eligibility rules — no verified transcripts exist |

## Changes made this task

- `datasets/pending_review/metadata.csv` — 90 `_r` rows with required fields (`sample_id, audio_path, script_reference, transcript_verified, verification_status, reviewer_notes, verification_timestamp`) + `model_prediction`, `proposed_split`, `prompt_group` for later slotting.
- `datasets/pending_transcripts/metadata.csv` — 80 `_n` rows with required fields (`sample_id, audio_path, speaker_id, script_reference, model_prediction, verbatim_transcript, transcript_status, reviewer_notes`).
- `datasets/{train,validation,test}/metadata.csv` — header-only (schema ready); unverified rows moved OUT per §6 rule.
- `scripts/review_tool.py` — interactive reviewer helper: plays each wav via macOS `afplay`, shows script + model prediction, accepts typed verbatim transcript + status, writes back to the manifest with UTC timestamp. Never auto-fills, never auto-verifies.
- `scripts/validate_dataset.py` — extended: verification-state consistency (verified⇒transcript+timestamp; pending⇒empty), supervised splits require `human_verified=1` + verified status + non-empty transcript, excluded rows need `excluded_reason`, md5 no-cross-split, prompt-group leakage + consistent `proposed_split`, still fully read-only.
- `datasets/excluded/metadata.csv` — rebuilt with explicit `excluded_reason`.

## Validator result

`validate_dataset.py` → **PASS** — 180 audio paths OK, 0 broken, 0 supervised-eligible (correct: nothing verified yet).
Warnings: supervised splits empty; only 2 speakers (A, B) — no speaker-disjoint eval possible.

## Speaker metadata issues

- Only 2 adult speakers; `A_C*`/`A_*_(1)` provenance ambiguous (female folder); kid/F30/M30 audio untranscribed.
- `Nu_C*` alias IDs share audio with `B_C*_r` — quarantined.

## Remaining before pilot fine-tuning

1. Human review of the 90 `_r` rows via `review_tool.py --set r` (or CSV+spreadsheet) → `verified_match`/`verified_corrected` unlocks pilot set along `proposed_split`.
2. Human verbatim transcription of 80 `_n` rows (`--set n`) → `transcribed` → `verified`.
3. Only verified rows may enter train/validation/test — validator enforces this.
4. If verification reduces usable data, resize splits within verified data only; never borrow test into train.

## Not done (by design)

No transcripts fabricated; no predictions used as GT; no listening performed by the agent — all statuses remain `pending_*` until a human reviews.
