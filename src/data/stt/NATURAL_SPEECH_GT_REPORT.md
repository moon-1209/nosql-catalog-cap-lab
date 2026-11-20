# NATURAL-SPEECH GROUND TRUTH & NUMBER-NORMALIZATION REPORT

**Date:** 2026-10-27 · **Repo:** Data-Science-Major-Project · **Branch:** `quang-manh`
Companion to `STT_QUALITY_AUDIT_REPORT.md`. No data overwritten; no commits.

---

## 1. Baseline preserved

| Check | Status |
|---|---|
| Original GT (`data/annotations.json/.csv`) | unchanged |
| Baseline predictions (`predictions/asr_predictions_180_samples.csv`) | unchanged |
| Baseline metrics (`metrics/asr_summary.json`) | unchanged — raw WER 0.3842, norm WER 0.2873, CER 0.2304 |
| Baseline reproducibility test | `tests/test_vi_number_norm.py::test_baseline_metrics_reproduce_from_predictions` — PASS |
| Model | PhoASR-whisper-small, untouched, no re-inference needed for the variant |

## 2. The 80 natural-mode recordings — review dataset

`src/data/stt/evaluation/error_analysis/natural_speech_review_manifest.csv` — **80 rows, all `review_status=pending_transcription`**.

Columns: `file_id`, `wav_path`, `raw_path`, `speaker`, `category`, `mode_label`, `intent`, `script_reference`, `phoasr_prediction`, `duration_s`, `norm_wer`, `norm_cer`, `verbatim_transcript` (blank), `review_status`, `reviewer_notes` (blank).

Status lifecycle: `pending_transcription` → `transcribed` → `verified`. Only `verbatim_transcript` filled by a human counts; the PhoASR prediction column is a reference aid, never Ground Truth.

Distribution: speaker A 40 (`A_01..30_n`, `A_C01..10_n`), speaker B 40 (`B_01..30_n`, `B_C01..10_n`); 60 regular prompts + 20 common takes.

**Script-vs-spoken mismatch is real, not model noise:** example `A_C06_n` — script "Nhà thuốc ở đâu?", prediction "Cho tôi hỏi nhà thuốc nằm ở đâu vậy?" — plausibly a faithful transcript of an ad-libbed utterance scored as WER 125%. This is why insertions are **not** automatically counted as model errors pending human verification.

## 3. Transcription workflow (existing + new)

The repo already has a verbatim-correction mechanism: `sim_vision/python/voice/prepare_data.py` writes `data/processed/transcripts_n_todo.csv` (`clip_id, text_script, text_fixed`) and reads back `text_fixed` as the corrected reference for `_n` clips (`ref_verified` flag). The review manifest mirrors that convention — `verbatim_transcript` ↔ `text_fixed`.

**Recommended reviewer flow:**
1. Open `natural_speech_review_manifest.csv`, sort by `file_id`.
2. Listen to `wav_path` (16 kHz mono, plays in any player) — raw `.m4a` at `raw_path` if needed.
3. Type exactly what was said into `verbatim_transcript` (keep hesitations, particles, paraphrases — verbatim, not the script).
4. Set `review_status=transcribed`; a second reviewer flips it to `verified`.
5. Doubtful audio / wrong-script cases: note in `reviewer_notes`.

**Three text tiers (kept distinct):**
- *Script reference* — `data/annotations.json` text (unchanged canonical baseline).
- *Verbatim transcription* — human-entered `verbatim_transcript` in the manifest.
- *Normalized reference* — derived at eval time by normalization (baseline or number-norm); never stored as a source of truth.

**Future incorporation (not done now):** once ≥1 row reaches `verified`, a derived GT file can be produced (e.g. `src/data/stt/manifests/annotations_verbatim.csv`, verbatim where verified else script) and a *separate* benchmark summary computed. The script-based baseline must remain the comparable run; do not overwrite `metrics/asr_summary.json` or `predictions/`.

## 4. Number-normalization variant (implemented, separately reported)

**Module:** `scripts/vi_number_norm.py` — converts *unambiguous* Vietnamese number-word phrases → digits, one direction only (digits are never expanded; multiple valid readings make the reverse ambiguous).

**Supported:** `U trăm [lẻ|linh U]` (205), `U trăm mười [U]` (112), `U trăm U mươi [U]` (345), `U nghìn/ngàn/triệu […]`, `U mươi [U]` (21), `mười [U]` (12), lone units (except `không`, `năm`). Room-number shorthand `số|phòng U lẻ|không U` → `N0U` **only in `số`/`phòng` context** (e.g. "số ba lẻ bốn"→"số 304").

**Deliberately not normalized:** standalone `không` (usually negation), standalone `năm` (usually "year"), `N trăm U` without mươi/lẻ (ambiguous), non-standard markers ("ba lấy bốn" — a mishearing, not a number form).

**Recomputation:** `scripts/eval_numbernorm.py` reads the existing predictions CSV (no model rerun) and writes `predictions/asr_predictions_180_numbernorm.csv` + `metrics/asr_summary_numbernorm.json`.

### Results (baseline vs number-normalized, corpus-level)

| Category | n | Baseline WER | Numnorm WER | Baseline CER | Numnorm CER |
|---|---|---|---|---|---|
| reading | 80 | 8.75% | **7.12%** | 5.95% | 4.33% |
| common | 20 | 10.53% | **5.26%** | 6.74% | 2.17% |
| natural | 80 | 51.78% | **50.59%** | 42.90% | 41.48% |
| **overall** | **180** | **28.73%** | **27.02%** | **23.04%** | **21.28%** |

15 samples affected (`A_07_{r,n}`, `A_C04_{r,n}`, `B_06_{r,n}`, `B_08_r`, `B_18_n`, `B_20_n`, `B_22_{r,n}`, `B_C04_{r,n}`, `Nam_C04`, `Nu_C04`). Effect concentrated where expected: common questions halved (−5.3pp), reading −1.6pp, natural only −1.2pp (dominated by ad-lib mismatch, not numbers).

## 5. Benchmark partitions (kept separate)

| Partition | Reference | Status |
|---|---|---|
| Script-GT baseline (all 180) | `annotations.json` | done — 28.73% / 27.02% numnorm |
| Reading subset (80 `_r`) | script | 8.75% / 7.12% |
| Natural subset (80 `_n`) | script | 51.78% / 50.59% |
| Natural subset with verbatim GT | **human transcripts** | **not computed — 0/80 transcripts exist** |

No human-reference WER is reported because no verified transcripts exist yet.

## 6. Limitations

- 80 `_n` takes still lack verbatim GT — the headline natural WER remains an upper bound until transcription completes.
- Number normalization cannot fix *misheard* numbers ("ba lấy bốn"); those remain model errors by design.
- Reviewer needs Vietnamese listening ability; the manifest has no audio-player integration (any external player works on the wavs).
- `năm`/`không` dual-use means spelled-vs-digit equivalence for those tokens is intentionally unresolved — documented conservative choice.

## 7. Files added/changed

| File | Status |
|---|---|
| `src/data/stt/evaluation/error_analysis/natural_speech_review_manifest.csv` | new — 80 review rows |
| `scripts/vi_number_norm.py` | new — number-word→digit normalizer |
| `scripts/eval_numbernorm.py` | new — variant metric recomputation |
| `tests/test_vi_number_norm.py` | new — 23 tests, all pass |
| `src/data/stt/evaluation/predictions/asr_predictions_180_numbernorm.csv` | new |
| `src/data/stt/evaluation/metrics/asr_summary_numbernorm.json` | new |
| `src/data/stt/NATURAL_SPEECH_GT_REPORT.md` | new — this file |

Pre-existing test failures unrelated to this work: `test_dashboard.py` (missing `gradio` dep in venv), `test_smoke.py::test_core_directories_exist` (`data/external` dir absent — never tracked in git).
