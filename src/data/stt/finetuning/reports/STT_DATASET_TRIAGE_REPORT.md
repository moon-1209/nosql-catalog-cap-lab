# STT DATASET TRIAGE REPORT — Ariadne

**Date:** 2026-10-27 · **Branch:** `quang-manh` · Read-only audit. No training, no model downloads, no commits.

## 1. Executive Summary

| Metric | Count |
|---|---|
| Physical audio files (`data/raw/real_voice/`) | **393** (388 `.m4a` + 5 `.wav`) |
| Processed WAVs (`src/data/stt/processed/real_voice/wav/`) | **393** |
| Logical manifest records | **386** (90 pending_review + 80 pending_transcripts + 206 unannotated + 10 excluded) |
| WAVs not in any manifest | **7 — all `Giọng clone/`** (voice-clone/TTS pipeline, deliberately out of ASR) |
| Records with script reference | **300** (90+80 annotated + 130 unannotated code-mapped) |
| Records with `model_prediction` | **376** (all except 10 excluded) |
| Verified Ground Truth | **0** |
| Missing script entirely | **76** (`F30_T*` 51 + `Mỡ Nướng` 25) |

**Discrepancy explained:** earlier "≈392" vs actual 393 = the `Nu_C*` alias copies at root were counted inconsistently; manifest count 386 = 393 wavs − 7 clone files. No unexplained gap remains. 0 broken manifest→file references.

## 2. Dataset Inventory

| Manifest | Rows | Script | Prediction | Verified GT |
|---|---|---|---|---|
| pending_review (`_r` reads) | 90 | 90 | 90 | 0 |
| pending_transcripts (`_n` ad-libs) | 80 | 80 | 80 | 0 |
| unannotated (kids/F30/M30/2nd takes) | 206 | 130 | 206 | 0 |
| excluded (`Nu_C` aliases) | 10 | 10 | 0 | 0 |
| train / validation / test | 0 | — | — | — |
| **ASR-eligible audio total** | **376** | | | |

## 3. Transcript Coverage

- Script reference present: 300 · Prediction present: 376 · Verified GT: 0 · Unverified: all 386.
- Missing transcript: all records (nothing human-verified). Missing script: 76.

## 4. Prediction-vs-Script Analysis (300 rows with both)

Normalization for comparison only: lowercase → punctuation strip → whitespace collapse → `vi_number_norm` number-word→digit. Class rules: `EXACT_MATCH` raw-equal · `NORMALIZATION_ONLY` equal after normalization · `MINOR_DIFFERENCE` word-sequence ratio ≥0.85 (difflib on normalized tokens) · `MAJOR_DIFFERENCE` <0.85 · `NO_REFERENCE`/`NO_PREDICTION` self-evident. Ratios are string similarity, **not** accuracy probability.

| Diff class | n | Note |
|---|---|---|
| EXACT_MATCH | 59 | still needs listen-confirm; not GT |
| NORMALIZATION_ONLY | 51 | mostly digit↔word forms & punctuation |
| MINOR_DIFFERENCE | 54 | |
| MAJOR_DIFFERENCE | 136 | dominated by `_n` ad-libs (script≠spoken content) |
| NO_REFERENCE | 76 | no script |

**Hospital-keyword priority flags (30 rows):** script/prediction differ on `tim mạch`, `khoa nhi`, `siêu âm`, `thu ngân`, `xét nghiệm`, `nhà thuốc`… e.g. `B_C01_r`, `B_C02_n`, `B_C04_n`, `F30_C02_r`, `A_C07_n`, `KID_M10_A_03_r`. Full list in `triage_audit_per_record.csv` (`next_action` column). Flag = review priority only, not an error verdict.

## 5. Human Review Priorities

1. **Quick-confirm (110):** `SCRIPT_AVAILABLE` + EXACT/NORM-ONLY — reviewer listens once, confirms. Lowest effort.
2. **Keyword diffs (30):** hospital-term mismatches — highest stakes for the Ariadne use-case.
3. **MAJOR/MINOR diffs (160 non-keyword):** mostly `_n` spontaneous takes — need verbatim transcription, not script-matching.
4. **NO_SCRIPT (76):** ASR draft exists in `model_prediction`; reviewer listens and corrects. Never accept draft unlistened.

Estimated load: ~110 confirmations are fast passes; ~266 need real listening effort.

## 6. Missing Script Analysis

`F30_T01..T25_{r,n}` + `F30_T08_n_wrong-order` (51) and `Mỡ Nướng 10..34` (25): no script text exists anywhere in repo/docs. Path forward = verbatim transcription only (ASR draft + human correction). `F30_C*` mappings to the C-section remain code-inferred pending reviewer confirmation.

## 7. PhoASR reusability

Local model loads `local_files_only` (verified in `--auto` runs); 376 predictions already stored — **no re-inference needed, none run in this audit.** Predictions never overwrite GT fields.

## 8. Proposed initial eval set (~40, once verified)

Stratified by speaker×mode: 10 A `_r` + 10 B `_r` + 10 `_n` + 5 kid (`KID_*`) + 5 F30 — all **after** human verification. Limits: only 2 adult verified speakers until kids/F30 transcripts exist; not yet a speaker-disjoint eval. Report-only proposal — nothing staged.

## 9. Data Integrity

Verified: no original audio moved/deleted (393 intact), no transcript/status changed by this audit, supervised splits remain empty, excluded rows untouched, no predictions written to GT fields.

## 10. Validation

`validate_dataset.py` → **PASS** (386 paths OK, 0 errors). Warnings unchanged and explained: supervised splits empty (0 verified GT); only 2 speakers (no speaker-disjoint eval possible).

## 11. Recommended next steps

1. Quick-confirm the 110 script-matching rows (est. minutes each).
2. Transcribe keyword-flagged 30, then remaining `_n` MAJOR-DIFF rows.
3. Verbatim-transcribe the 76 no-script rows against ASR drafts.
4. Then assemble the proposed ~40-sample eval set and the pilot train split from verified rows only.

## 12. Artifacts

- `reports/triage_audit_per_record.csv` — 386-row per-record audit (all fields per spec §5).
- This report. No manifest/code/data changes.
