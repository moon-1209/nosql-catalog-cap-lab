# STT DATASET QUALITY AUDIT & BASELINE ERROR ANALYSIS

**Date:** 2026-10-27 · **Repo:** Data-Science-Major-Project · **Branch:** `quang-manh`
**Scope:** verify dataset integrity, reproduce baseline metrics, analyze errors, prepare listening-review manifest. No data deleted/overwritten; no commits.

---

## 1. Verified Counts (recomputed from files, not taken on faith)

| Claim | Verified |
|---|---|
| Raw voice files under `data/raw/real_voice/` | **393** ✔ (383 Drive + 10 local `Nu_C` alias copies) |
| Processed WAVs under `src/data/stt/processed/real_voice/wav/` | **393** ✔ |
| All WAVs 16 kHz / mono / PCM_16 | **393/393** ✔ (soundfile-verified) |
| Canonical benchmark samples | **180** ✔ — every annotation `file_id` maps to exactly one benchmark wav |
| Annotation records (`data/annotations.json`) | 180 (80 `_r`, 80 `_n`, 10 `Nam_C`, 10 `Nu_C`) |
| Download manifest rows | 393, all `readable`, 0 empty, 0 undecodable |
| Benchmark run | 180/180 evaluated, `failed_samples: []` |
| Reported normalized WER 28.73% | **Reproduced exactly** (see §4) |

## 2. Integrity Findings

### 2.1 Duplicate / redundant representations in the 393-file set

| Group | Files | Nature |
|---|---|---|
| `Nu_C01..10` vs `B_C01..10_r` | 10 pairs | **md5-identical** — intentional alias copies (no `Nu_C*` exists on Drive); both stems are benchmark `file_id`s, so these 10 utterances are scored twice by design of the annotation schema |
| `A_01..15_r`, `A_C01..10_r` in `Trẻ con/Nam 10` + `Trẻ con/Nữ 10` | 50 wavs | Same `file_id` stems, **different recordings** (child voices) — excluded from benchmark via canonical-folder rule in `evaluate_asr.py` |
| `A_01..30_{r,n} (1)` in `Nữ 20 tuổi` | 60 wavs | Same stems + " (1)" suffix, **different recordings** (md5 ≠, duration Δ mean 2.05 s, max 4.01 s) — separate takes, not re-encodes; excluded from benchmark |
| `Trường Giang`/`Trần Thành` `.m4a`+`.wav` pairs | 2 pairs | Same recording in two formats → `.m4a.wav` naming in processed set |

No unexpected byte-identical duplicates. No filename collisions remain (APFS Unicode-normalization edge case handled).

### 2.2 Benchmark mapping
- All 180 `file_id`s resolve to exactly one canonical wav (`stt_dataset_manifest.csv`, `in_benchmark=1`): speaker A ← `Hoàng Tuấn/Nam 20 tuổi/` + root `Nu_C`-style rule, speaker B/C-aliases ← `Phương Uyên/Nữ 20 tuổi/`, `Nu_Cxx` ← root copies.
- 50 kid-voice wavs + 60 "(1)" wavs share annotation stems but are correctly excluded (eval prints `INFO: 50 wavs share an annotated file_id…` / `WARNING: 163 audio files have no annotation…`).
- No missing files, no empty files, no filename collisions, no unmapped benchmark audio.

### 2.3 Audio quality
- Duration 1.75–10.71 s (mean 4.75 s) — none <1 s or >15 s.
- Clipping: **0 files** above 0.5% clipped samples; max peak 0.41 — no clipping problem.
- Loudness: no outliers below −40 dBFS or above −8 dBFS; quietest = `B_23_n` (−39.7 dBFS), `A_C06_r` (−38.3), `B_C06_r` (−38.2) — flagged for listening review.
- Speaker/group metadata preserved by folder hierarchy in both raw and processed trees.

### 2.4 Partition leakage
- No train/dev/test split exists (eval-only dataset). The only double-counted content is the intentional `Nu_C`↔`B_C_r` alias pairs (10 utterances scored under two `file_id`s).

## 3. Metric Definitions (as implemented in `scripts/evaluate_asr.py`)

- **Normalization:** `text.lower()` → remove `[^\w\s]` (drops punctuation; Python `\w` keeps Vietnamese diacritics/letters) → collapse whitespace. Applied identically to GT and prediction for `norm_*` metrics. Capitalization & punctuation are ignored; **numbers are NOT normalized** (digits ≠ spelled-out words — see §5.2).
- **WER/CER:** jiwer, computed **corpus-level** (all refs vs all hyps concatenated) for aggregates — verified correct method; per-sample values stored too (naive mean of per-sample WER = 0.3106 ≠ corpus 0.2873, expected difference).
- **RTF:** `inference_time / audio_duration`, per sample; overall = total infer / total audio.
- **Missing/failed samples:** explicit warnings + `failed_samples` list; 0 failures this run.

## 4. Reproduced Baseline (from `predictions/asr_predictions_180_samples.csv`)

| Metric | Reported | Recomputed | Status |
|---|---|---|---|
| Raw WER | 0.3842 | 0.3842 | ✔ |
| Norm WER | 0.2873 | 0.2873 | ✔ |
| Norm CER | 0.2304 | 0.2304 | ✔ |
| Samples | 180 | 180 | ✔ |
| Failures | 0 | 0 | ✔ |
| Mean RTF / infer | 0.151 / 0.659 s | CPU run | ✔ |

Error totals (normalized, corpus): **S=141, D=16, I=263** over 1,462 reference words.

| Category | n | S | D | I | Corpus WER | Insertion share |
|---|---|---|---|---|---|---|
| reading `_r` | 80 | 44 | 4 | 11 | **8.8%** | 19% |
| common `Nam_C/Nu_C` | 20 | 8 | 0 | 4 | **10.5%** | 33% |
| natural `_n` | 80 | 89 | 12 | 248 | **51.8%** | **71%** |

## 5. Error Analysis

### 5.1 Dominant pattern — natural-mode ad-libs vs script GT
71% of natural-mode errors are **insertions** of conversational particles/fillers absent from the script text:
`mình`(18), `thì`(13), `á`(11), `bạn`(11), `em`(9), `cho`(9), `hỏi`(9), `vậy`(7), `ok`(5), `à`(5), `ba`(6), `đó`(5).

Speakers were *instructed* to speak naturally ("được ngập ngừng, thêm ờ/à/dạ, đổi vài chữ"), so GT for `_n` takes is inherently under-specified. Much of the 51.8% natural WER is **annotation mismatch, not model error**. Examples where the prediction is plausibly correct-but-different wording: `A_C06_n` GT "Nhà thuốc ở đâu?" → "Cho tôi hỏi nhà thuốc nằm ở đâu vậy?" (WER 125%).

### 5.2 Number rendering — systematic normalization gap (10 GT samples contain digits)
GT uses digits; model spells numbers out: `205`→"hai trăm linh lăm", `112`→"một trăm mười hai", `304`→"ba lẻ bốn"/"ba lễ tư"/"ba không bốn". Semantically right, string-wrong → e.g. `B_06_r` WER 44%, `A_07_r` 57%. All 10 digit-GT samples affected; also `sự ăn số ba lấy bốn là nằm` (`B_C04_n`) shows real mishearing compounding it.

### 5.3 Medical/domain terminology — genuine model weakness
`tim mạch`→"tin mặt"/"qua trên mặt", `siêu âm`→"sự ăn", `thu ngân`→"thủ nhân"/"thuốc ngưng", `điện tim`→"điện tiên", `X-quang`→"ít khoan", `chuyển khoản`→"chỉ khoản", `quầy`→"uầy", `nhé`→"nhép". 34 flagged samples in `error_categories.csv`.

### 5.4 Diacritics — minor but consistent
`mấy`→`máy`(3), `ạ`→`à`(3) + `ạ` deleted 5×, `khám`→`khá`, `tầng`→`từng`, `với`→`và`/`nha`. Tone/diacritic instability typical of small Whisper on Vietnamese.

### 5.5 What is NOT the cause
- Not recording quality: no clipping, no silence outliers, RMS spread healthy; worst WER samples have normal levels.
- Not utterance length: durations are 2–11 s, well inside Whisper's window.
- Not speaker group: both A and B show the same mode-driven pattern (reading≈good, natural≈GT-mismatch-dominated).

### 5.6 Worst samples (all `_n`, script-deviating takes)
`A_C05_n` 200%, `B_C02_n` 180%, `B_C04_n` 157%, `B_C05_n` 140%, `B_C10_n` 133%, `A_C06_n`/`B_C01_n` 125%, `A_06_n`/`A_16_n`/`A_28_n` 117% — need listening to split paraphrase vs misrecognition.

**Artifacts written:**
- `error_analysis/per_sample_errors.csv` — S/D/I, durations, RMS, clipping per file
- `error_analysis/top_error_pairs.csv` — ranked substitutions/deletions/insertions
- `error_analysis/error_categories.csv` — 80 tagged samples (natural_paraphrase 41, medical_term 34, diacritic_minor 15, numbers_digits 10)
- `error_analysis/error_analysis_180_samples.csv` — top-50 worst + failures (from eval run)

## 6. Human Listening Review

`src/data/stt/evaluation/human_review_manifest.csv` — 27 rows with wav path, GT, prediction, WER/CER, duration, RMS, clipping, `reason_for_review`, `listening_status = pending_listening`. Buckets: near-perfect (5), highest-WER (8), digit mismatches (4), medical-term suspects (4), quietest (3), highest-peak (3).

**No listening validation has been performed** — status fields are explicitly pending; claims of GT correctness/incorrectness (esp. `_n` takes) require human review.

## 7. Data Limitations

1. `_n`-take GT = script text only → natural WER conflates paraphrase with model error; a fair acoustic WER needs re-transcribed references (or an LLM-aided semantic-match metric).
2. Digit GT vs spelled-out model output → normalizable mismatch, fix in eval normalization only.
3. `Nu_C`/`B_C_r` alias pairs double-score 10 utterances in the 180-sample benchmark.
4. `A_C*`/`A_*(1)` files in the female folder have ambiguous provenance (likely her takes of script A) — flagged, not blocking.
5. Single model, single pass; no confidence scores captured.

## 8. Recommendations (priority order)

1. **Re-transcribe `_n` takes** (80 files) — the single highest-impact fix; current natural WER is uninterpretable. Human listening manifest provided.
2. **Add number normalization** to eval (`205`↔"hai trăm lẻ năm") — mechanical, removes ~10-sample systematic inflation. Implement as a *variant* metric; keep current rules as the comparable baseline.
3. **Domain adaptation**: benchmark a stronger Vietnamese ASR (e.g. PhoWhisper-large / Whisper-medium-vi) before fine-tuning; medical-term errors are model-side.
4. **Deduplicate benchmark** scoring for alias pairs (score `Nu_C`/`B_C_r` once) in future runs.
5. **Data collection**: more speakers/ages exist (kids, F30, M30) — usable for robustness evals once annotated; keep them out of the 180 benchmark.
6. Do **not** fine-tune yet — fix reference transcripts first or fine-tuning optimizes toward mismatched targets.

---

## Addendum (2026-10-27, follow-up work — original findings above unchanged)

- 80-row verbatim review manifest created: `evaluation/error_analysis/natural_speech_review_manifest.csv` (all `pending_transcription`).
- Number-normalization variant implemented (`scripts/vi_number_norm.py`, `scripts/eval_numbernorm.py`): overall WER 28.73%→27.02%, common 10.53%→5.26%. Baseline untouched; see `metrics/asr_summary_numbernorm.json` and `NATURAL_SPEECH_GT_REPORT.md`.
- 23 new tests (`tests/test_vi_number_norm.py`) all pass, including baseline-reproducibility lock.
