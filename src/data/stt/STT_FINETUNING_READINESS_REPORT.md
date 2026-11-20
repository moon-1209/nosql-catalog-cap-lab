# STT FINE-TUNING READINESS ASSESSMENT

**Date:** 2026-10-27 · **Repo:** Data-Science-Major-Project · **Branch:** `quang-manh`
**Verdict: CONDITIONALLY READY — pipeline-validation pilot only; not ready for a result-meaningful run.**

No training performed. No data deleted. No commits.

---

## 1. Verified Inventory

| Item | Verified value |
|---|---|
| Raw recordings | 393 files under `data/raw/real_voice/` (Drive hierarchy preserved) |
| Processed WAVs | 393, all 16 kHz mono PCM_16 under `src/data/stt/processed/real_voice/wav/` |
| Benchmark set | 180 canonical file_ids, each mapping to exactly 1 wav |
| Benchmark duration | 854.6 s ≈ **14.2 min** (reading 7.1 min, natural 7.2 min) |
| Adult speakers | **2 only** — A (male, ~20, `Hoàng Tuấn/Nam 20 tuổi`), B (female, ~20, `Phương Uyên/Nữ 20 tuổi`) |
| Other speakers on disk | 2 children (`Trẻ con/`, 50 takes, no transcripts), `Female 30`/`F30_*` (71, no transcripts), `Male 30`/`Mỡ Nướng` (25, no transcripts), voice-clone samples (7, unrelated) |
| Model | `WhisperForConditionalGeneration`, whisper-small arch (d_model 768, 12+12 layers, vocab 51,865), `model.safetensors` 967 MB ≈ 242 M params — **inference package only** |
| Baseline | norm WER 28.73% / CER 23.04% (reproduced); number-norm variant 27.02%/21.28% |

## 2. Transcript Quality

| Bucket | Count | Status |
|---|---|---|
| Script reference (all 180) | 180 | present, canonical |
| Verified verbatim transcripts | **0** | `natural_speech_review_manifest.csv`: 80/80 `pending_transcription`, `verbatim_transcript` empty |
| `_r`/`Nam_C`/`Nu_C` reads (100 records, 90 unique utterances) | script ref **assumed-verbatim but unverified** | usable as references with that explicit caveat; speakers read the script but deviations were never human-checked |
| `_n` ad-lib takes (80) | script ref only — systematically mismatched (71% of natural-mode errors are particle insertions) | **not usable** as supervision until transcribed |
| Ambiguous provenance | `A_C*` + `A_*_(1)` in `Nữ 20 tuổi` folder | flagged; likely speaker-B takes of script A |
| Non-benchmark audio | 213 recordings (kids/F30/M30/clone) | **no transcripts at all** — excluded from training consideration |

No PhoASR prediction is treated as Ground Truth anywhere.

## 3. Audio & Metadata Findings

- All 393 files decodable (ffprobe), durations 1.75–10.71 s, zero clipping >0.5%, quietest −39.7 dBFS — acoustically healthy.
- Duplicate audio: `Nu_C01..10` ≡ `B_C01..10_r` (md5-identical) — must enter training **once** or the same utterance is double-counted.
- Same-stem leakage risk is real: `A_01..15_r`, `A_C01..10_r` exist in 3 folders (adult + 2 kids); `A_*` exists twice in `Nữ 20 tuổi` (` (1)` variants). Any split keyed by filename alone would leak.
- Common prompts `C01..C10` are read by **both** speakers — same text different voices; fine for training, but means speaker-disjoint eval measures voice generalization on identical sentences.
- Speaker/room metadata survives only via folder paths — preserved in manifests.

## 4. Recommended Split Strategy

Artifact: `src/data/stt/manifests/proposed_finetune_splits.csv` (180 rows; `eligible_pilot=1` for 90).

- **Speaker-disjoint is NOT feasible** with only 2 speakers: training on A and testing on B leaves no dev speaker and halves an already tiny set. Do not present such a split as a generalization result.
- **Prompt-group-disjoint within speakers** is the honest near-term split: partition by sentence code (`A_01..30`, `B_01..30`, `C`) so the same utterance text never appears in both train and test. Current proposal: hash-split → 70 train / 6 val / 14 test of the 90 eligible script-reliable utterances.
- `_n` takes and `Nu_C` duplicates → `holdout_no_verbatim_ref` until transcripts exist.
- **Minimum additional data for a real split:** ≥2 more adult speakers with transcripts, or verbatim transcripts for the 50 kid-takes + 96 F30/M30 takes to unlock speaker-disjoint evaluation.

## 5. Fine-tuning Feasibility

| Check | Finding |
|---|---|
| Architecture | Standard HF `WhisperForConditionalGeneration` — trainable via `transformers` Seq2SeqTrainer |
| Fine-tune code in repo | **None for ASR** (`src/training/` is RL; `train_phobert.py` is NLU); must be written |
| Framework deps | `transformers` 5.20.2, `accelerate` present; **no `peft`/`datasets`** — would need adding |
| Hardware | Apple Silicon arm64, torch MPS available; CPU eval RTF ≈0.15 |
| Memory/size | 242 M params: **full FT on ~7 min audio = extreme overfitting risk**; realistic options are LoRA (needs `peft`) or frozen-encoder decoder-partial FT |
| Data volume | ~7 min eligible speech — enough to *validate a pipeline*, not to move WER meaningfully |
| `_n` goal | The actual problem (natural speech) **cannot be trained on at all** until the 80 transcripts exist |

## 6. Readiness Classification

**CONDITIONALLY READY** — a limited *pipeline-validation* pilot is feasible now under explicit caveats:

- Eligible supervision: 90 unique utterances, `_r`-mode, script references assumed-verbatim **but human-unverified** (~7 min).
- Split: prompt-group-disjoint 70/6/14 — no utterance leakage; not speaker-disjoint.
- Expected outcome: proves training/eval plumbing works; **must not** be reported as a model improvement (data volume and GT quality are insufficient).

**Entry criteria for a *meaningful* pilot (not yet met):**
1. ≥40 `_n` verbatim transcripts `verified` in the review manifest (target: all 80).
2. Human spot-check of ≥20 `_r` takes confirming script refs are verbatim-accurate.
3. ≥1 additional adult speaker (or verified kid/F30 transcripts) enabling a speaker-disjoint test set.
4. Duplicate-utterance exclusion enforced (`Nu_C` vs `B_C_r`) — encoded in the split manifest.
5. Reproducible eval harness: fixed split file + fixed baseline (exists: `asr_summary.json` lock test) + same normalization rules.

**NOT READY for:** full fine-tuning, natural-speech improvement claims, speaker-generalization claims.

## 7. Prioritized Next Steps

1. **Transcribe the 80 `_n` takes** (workflow in `NATURAL_SPEECH_GT_REPORT.md`; `natural_speech_review_manifest.csv` ready) — unlocks the real training target.
2. Spot-verify a sample of `_r` takes so "assumed-verbatim" becomes verified.
3. Add `peft` and write a minimal LoRA fine-tune script (encoder frozen), wired to `proposed_finetune_splits.csv`.
4. Run pipeline-validation pilot on the 70-utterance train split; evaluate on the 14-utterance test split with identical normalization as the baseline.
5. Collect/annotate ≥1 more adult speaker (or transcribe kid/F30/M30 takes) for a true speaker-disjoint test.
6. Only then evaluate fine-tuning impact; keep PhoASR-whisper-small as the production baseline.
