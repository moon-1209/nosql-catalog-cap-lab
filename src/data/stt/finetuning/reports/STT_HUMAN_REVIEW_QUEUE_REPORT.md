# STT HUMAN-REVIEW QUEUE — Verified Before Annotation

**Date:** 2026-10-27 · **Branch:** `quang-manh` · Audit-only; nothing modified.

## Queue integrity (verified from `triage_audit_per_record.csv`, 386 records)

| Priority group | Count | Overlap check |
|---|---|---|
| P1 quick-confirm (EXACT/NORMALIZATION_ONLY) | **110** | disjoint from all |
| P2 hospital-keyword diff | **30** | ⊂ diff set (30 of 190) |
| P3 other MINOR/MAJOR diffs | **160** | = 190 diff − 30 keyword |
| P4 no-script (verbatim from scratch) | **76** | disjoint |
| Excluded (`Nu_C` aliases) | 10 | stay excluded |
| **UNIQUE REVIEW QUEUE** | **376** | 110+30+160+76 — no double counting |

The 110/30/160/76 figures are accurate **as a partition**; the raw group totals (110 + 30 + 160 + 76) were only valid once keyword↔diff overlap (30) was subtracted — done above.

## Composition by speech mode

| Group | `_r` scripted | `_n` ad-lib | F30_C inferred | no-script |
|---|---|---|---|---|
| P1 quick-confirm (110) | 94 | 1 | 15 | — |
| P2 keyword (30) | 19 | 8 | 3 | — |
| P3 other diffs (160) | 87 | 71 | 2 | — |
| P4 no-script (76) | — | — | — | 76 |
| **Total** | **200** | **80** | **20** | **76** |

- `_r` count = 90 annotated reads + 50 kid + 60 "(1)" second takes. Their scripts are reference *candidates*, not auto-GT.
- `_n` = the 80 ad-lib takes; diff here likely means the *script* diverges from speech, not that ASR erred.
- `script_inferred=1` on the 20 `F30_C*` rows — mappings code-inferred until a listener confirms.

## Recommended review order (one listen per record, easiest→hardest)

1. **P1 (110)** — audio≈script; a single listen confirms `verified_match`. Fast, builds the first verified pool.
2. **P2 (30)** — hospital-keyword diffs; high stakes for the use-case; verify wording, then transcript.
3. **P3 (160)** — verbatim transcription; for `_n` rows the prediction may be the *correct* transcript — check prediction first, correct rather than retype.
4. **P4 (76)** — hardest: ASR draft + listening, no script aid.

Each record is listened to **once** in this order; status columns (`verbatim_transcript`/`transcript_status`) update via `review_tool.py` or the CSV.

## Outputs

- `reports/review_queue.csv` — 386 rows: `sample_id, audio_path, dataset_group, speech_mode, current_status, has_script, has_prediction, script_inferred, diff_class, review_priority, reason, recommended_action`. Sorted by priority.
- This report. No manifest/data changes.

## Validation

`validate_dataset.py` (run after audit) → **PASS**, 0 errors; warnings unchanged (empty supervised splits, 2 speakers). No transcript/status/GT field touched.

## Limitations

- P1 "quick-confirm" still requires a human listen — script≈prediction is a prioritization hint, not verification.
- `F30_C*` scripts remain inferred until audio-confirmed.
- `_n` mismatch verdicts impossible until verbatim transcripts exist (script isn't spoken content).
