# Natural Speech Fine-Tuning Readiness — Ariadne

**Date:** 2026-11-11 · **Status:** INTERIM — acquisition in progress; verdict will be revised when downloads complete.

## Current state

| Pool | Utterances | Verified |
|---|---|---|
| Natural speech added (Bud500 test) | 7,500 | fully QC'd, 0 dups |
| Bud500 train | ~634,158 | downloading (est. 12+/105 shards) |
| VietSuperSpeech | 67,405 | downloading (~4%) |
| Existing STT manifest pool | 22,096 | unchanged |

## Does this improve representation?

**Naturalness: YES — substantially.** For the first time the corpus has genuine spontaneous/conversational Vietnamese:
- Bud500: ~500 h informal dialogue (40% informal pronouns, 10% fillers) — complements the existing read-speech-heavy pool.
- VietSuperSpeech: ~245 h interview podcast conversation.
- Combined potential natural-speech addition: **~750 h** vs the existing ~35 h read-heavy pool — a major representativeness upgrade for hospital-style spontaneous queries.

**Age diversity: NO — unchanged.** Neither new source has age metadata; all incoming rows are `Unknown_Age`. The 50+/elderly gap is **not** addressed by this acquisition. Verified paths remain: SpeechData.ai (age metadata, $65/h, free sample on request), Common Voice (user login needed), capleaf/viVoice (gated, denied).

**Transcripts: MIXED.** Bud500 = human-quality (usable for supervised training). VSS = ASR-silver (usable only after language-filtering and confidence-flagging — treat as weakly-labeled).

**Speaker splits: WEAKENED.** Neither source has speaker IDs. Bud500 official splits must be trusted unverifiably; VSS `source`-video is a session proxy at best. Risk: same speaker across splits can't be ruled out — acceptable for pilot, flag for eval hygiene. Keep VSS `source`-grouped as the split unit (never split one source video across train/eval).

## Interim verdict

**CONDITIONALLY READY — pending acquisition completion.**

Recommended sequencing once downloads finish:
1. Complete extraction + QC + duplicate audit (scripted, ready).
2. Ingest into `dataset_manifest.csv` with `speech_type` (SPONTANEOUS/CONVERSATIONAL/INTERVIEW) and `transcript_source` fields.
3. Extend `stt_open_datasets_manifest.csv`: Bud500 test → eval set addition (natural-speech eval — valuable); Bud500 train + VSS (language-filtered) → train.
4. Re-issue readiness verdict with final counts.

## Immediate user action needed

- **VietSpeech (1,100 h, apache-2.0, biggest free pool):** click "Agree and access repository" at https://huggingface.co/datasets/NhutP/VietSpeech — instant auto-approval.
- **Optional:** request free SpeechData.ai sample pack (verified age+gender+region metadata — only known source) before deciding on purchase.

## Compliance check

No originals modified/deleted · no metadata fabricated · no ages inferred · Under_18 segregated and excluded · no Git operations · no training started.
