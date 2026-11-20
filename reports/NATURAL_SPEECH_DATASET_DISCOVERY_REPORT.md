# Natural Speech Dataset Discovery Report — Ariadne

**Date:** 2026-11-11 · **Phase A/B output** · Verified against live repos, READMEs, manifests and downloaded audio samples — not marketing claims.

## Executive summary

Three priority-1 datasets were audited. **None carries age, gender, or speaker-ID metadata.** Two passed pilot evaluation and are being acquired; one is blocked by an HF gate requiring a user click.

| Dataset | Hours | Files | Speakers | License | Gate | Naturalness (verified) | Transcripts | Verdict |
|---|---|---|---|---|---|---|---|---|
| thanhnew2001/VietSuperSpeech | ~245 (manifest) | 67,405 wav | no IDs (source-video proxy) | MIT | none | **INTERVIEW/CONVERSATIONAL** (Vietcetera podcasts: HaveASip, Vietnam Innovators, Cởi Mở…) | ASR (Zipformer-30M-RNNT) — silver, ALL-CAPS, fails on English code-switch | **ACQUIRE — in progress** |
| linhtran92/viet_bud500 | ~500 | 649,158 (parquet) | no IDs | cc-by-nc-sa-4.0 | auto — cleared | **SPONTANEOUS/CONVERSATIONAL** — informal dialogue, storytelling, vlogs | human-quality, lowercase-no-punct, mid-utterance cuts | **ACQUIRE — in progress** |
| NhutP/VietSpeech | ~1,100 | 1,026,047 (27 parquets) | no IDs | apache-2.0 | auto — **BLOCKED** | unverifiable (no samples accessible) | unknown origin | **BLOCKED — needs user click** |

## Per-dataset detail

### 1. VietSuperSpeech (`thanhnew2001/VietSuperSpeech`)
- **Reality vs README:** README is stale (32k samples/3 news sources). Live `manifest.json`+`train/dev.json` = **67,405 samples, 245.4 h**, all `asr_segments_vietcetera_*` (podcast network). Audio tree also contains orphaned dirs (nguoivietdailynews, trinhlieu, nguyenkhangofficial, vietcetera parts 12/15) not in the manifest.
- **Naturalness (sampled 32 files):** genuine interview conversation — fillers, informal pronouns ("em", "mình"), code-switching to English. Segments ~10–15 s.
- **Transcripts:** ASR-generated (silver). ~1.3 fillers/100 words observed; non-Vietnamese segments produce garbage text → **transcript_source=ASR, needs filtering**.
- **Audio:** WAV 16 kHz mono, decode OK, healthy peaks.
- **No age/gender/speaker IDs** — `source` field = source video (weak session proxy).
- License MIT. Ungated. ~64 GB total repo.

### 2. Bud500 (`linhtran92/viet_bud500`)
- ~500 h, 634,158 train + 7,500 val + 7,500 test; WAV 16 kHz mono PCM_16 in parquet shards (~52 GB train + 0.6 GB test).
- **Naturalness (sampled 30 rows/5 offsets):** informal spontaneous dialogue — "cho em nghe đi con sao rồi em đừng khóc", "vừa ăn tài vừa nói chuyện", "oải lắm". Short 1.4–4.5 s segments (mid-utterance cuts).
- **Transcripts:** coherent human-quality (VietAI-curated), normalized lowercase/no punctuation.
- **Official splits exist but no speaker IDs → disjointness unverifiable.**
- License **cc-by-nc-sa-4.0 — non-commercial**. Gate: auto, cleared with token `Jaozii`.

### 3. VietSpeech (`NhutP/VietSpeech`)
- 1,026,047 samples / ~1,100 h / 131 GB, apache-2.0, claims N/C/S accent diversity — **schema has only `audio`+`transcription`; no accent/speaker/age fields to verify the claim.**
- `gated: auto` — README resolves but LFS parquets return 403 "not in authorized list". The user (`Jaozii`) must click **"Agree and access repository"** at https://huggingface.co/datasets/NhutP/VietSpeech. Not bypassed. One click → instant approval → same pipeline can fetch.

## Priority 2 — commercial (investigation only, nothing purchased)

| Vendor | Dataset | Hours | Speakers | Metadata | License | Cost |
|---|---|---|---|---|---|---|
| Nexdata | 500h Conversational (mobile) | 500 | ~750, gender-balanced | speaker ID + gender; **no age** | commercial | quote only |
| Nexdata | 711h Spontaneous | 711 | n/a | speaker ID + gender; no age | commercial | quote only |
| Nexdata | 977h Call-center | 977 | 1,234 | speaker ID + gender; no age | commercial | quote only |
| SpeechData.ai | Vietnamese Conversational | 2,000 | 200 | **age + gender + region + device**; signed consent chain | commercial train+eval | **$65/h** (~$130k full; free sample pack on email request) |

**Only SpeechData.ai offers verified age metadata** among all candidates examined — currently the sole concrete path to 50+/elderly coverage besides Common Voice (still login-gated) and capleaf/viVoice (still gated, denied).

## Also worth noting (unprioritized but relevant)

- **IARPA Babel Vietnamese (LDC2017S01):** ~201h conversational telephone speech — real spontaneous dialogue; LDC license (fee, non-commercial for non-members).
- **GigaSpeech 2 (Vietnamese subset):** multi-domain YouTube/podcast/audiobook corpus, free for research — worth a follow-up look if more naturalness diversity is needed.

## Blockers

1. VietSpeech — user must accept the auto-gate (one click).
2. No free dataset anywhere in this audit provides verified age labels → elderly gap persists until SpeechData.ai samples/purchase, Common Voice login, or capleaf approval.
3. Speaker-disjoint splitting impossible within Bud500/VietSuperSpeech (no speaker IDs) — VSS `source` video is the only proxy; Bud500 splits must be trusted as published or held together.
