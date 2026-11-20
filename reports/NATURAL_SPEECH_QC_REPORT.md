# Natural Speech QC Report — Ariadne

**Date:** 2026-11-11 · Covers: pilot samples (all 3 datasets) + fully-acquired Bud500 test split (7,500 files)

## 1. Bud500 test split — full-file QC (7,500/7,500 decoded)

| Check | Result |
|---|---|
| File integrity / decodability | 7,500/7,500 OK — WAV PCM_16 |
| Sample rate | 16,000 Hz — 100% |
| Channels | Mono — 100% |
| Duration | mean 2.6 s · median 2.5 s · p5 1.6 s · p95 3.7 s (short ASR segments) |
| Empty transcripts | 0 |
| QC labels | **PASS 7,500 · REVIEW 0 · INVALID 0** |
| Internal raw-MD5 dups | 0 · duplicate transcripts: 2 groups |
| Cross-dataset dups (raw-MD5 + canonical PCM-MD5 vs 89k corpus) | **0 / 0** |

## 2. Naturalness assessment (transcript + audio evidence, not filenames)

### Bud500 — SPONTANEOUS / CONVERSATIONAL
Full test-shard transcript analysis (3,750 utterances):

| Marker | Rate |
|---|---|
| Informal pronouns (em/anh/chị/mình/bố/mẹ/ông/bà…) | **40.4%** of utterances |
| Fillers/hesitations (ừm/ờ/à/nhỉ/hả/kiểu/lắm…) | **10.2%** |
| Question-like forms | 5.4% |
| Exact word repetitions ("tôi thì tôi") | 1.8% |
| English code-switch | ~0.3% |

Segments are mid-utterance cuts of informal dialogue — consistent with vlogs/interviews/storytelling rather than read text. Transcription quality is human-grade coherent (VietAI-curated).

### VietSuperSpeech — INTERVIEW / CONVERSATIONAL (transcript caveat)
32-file pilot: podcast interviews (Vietcetera network). Genuine conversational content — informal register, code-switching. **BUT** transcripts are Zipformer ASR output: ALL-CAPS, and non-Vietnamese stretches produce garbage text ("IT SNOW THE IT ALL LE GON…"). On ingest, rows need a Vietnamese-language filter and `transcript_source=ASR`.

### VietSpeech — UNKNOWN
No samples accessible (gate). Classification deferred.

## 3. Comparison vs existing corpus

| Corpus | Speech type | Transcript | Speakers |
|---|---|---|---|
| VIVOS (held) | READ_SPEECH | verified prompts | 65 |
| FLEURS (held) | READ_SPEECH | verified official | 1,978 |
| VLSP2023 (held) | broadcast/news (mixed) | source-provided | unknown |
| **Bud500 (new)** | **SPONTANEOUS/CONVERSATIONAL** | human-quality | unknown* |
| **VSS (new)** | **INTERVIEW/CONVERSATIONAL** | ASR-silver | unknown* |

\* No speaker IDs in either new dataset — the corpus's biggest metadata gap persists.

## 4. QC labels applied

`qc_status` vocabulary used: PASS / REVIEW / INVALID / DUPLICATE_RAW_INTERNAL / DUPLICATE_CROSS_DATASET — consistent with the pipeline's audit trail. Nothing deleted; INVALID kept on disk.
