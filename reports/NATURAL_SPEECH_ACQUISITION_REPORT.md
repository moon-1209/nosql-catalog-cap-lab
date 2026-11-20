# Natural Speech Acquisition Report — Ariadne

**Date:** 2026-11-11 · **Status:** IN PROGRESS — pilot phase complete; two acquisitions downloading; one dataset gated.

## Acquisition status

| Dataset | Status | Verified so far |
|---|---|---|
| **Bud500** (`linhtran92/viet_bud500`) | 🟡 Downloading | Test split COMPLETE: 2/2 shards, sha256-verified, **7,500 wavs extracted, 100% PASS, 0 dups**. Train: 105 shards (~52GB) in progress — 12+ shards done at report time |
| **VietSuperSpeech** (`thanhnew2001/VietSuperSpeech`) | 🟡 Downloading | Manifest-driven fetch of the 67,405 listed files in progress — ~2,700 done at report time. train.json/dev.json/manifest.json preserved |
| **VietSpeech** (`NhutP/VietSpeech`) | 🔴 Blocked | `gated: auto` — requires the user to click "Agree and access repository" at https://huggingface.co/datasets/NhutP/VietSpeech. Not bypassed |

## Verified acquisitions (on disk, validated)

### Bud500 test split — COMPLETE
- Location: `Unknown_Age/Bud500/test/{test-00000,test-00001}/row*.wav` — **7,500 files, 5.33 h**
- Source shards SHA-256: `a204d936…3bcfe`, `e5eb289a…6b` — both exact expected sizes (306,016,190 / 301,741,975 B)
- Original parquets: being preserved under `data/raw/archives/Lê Hà/Open_Datasets/Bud500/`
- **QC: 7,500 PASS / 0 REVIEW / 0 INVALID** — all WAV PCM_16 16 kHz mono, mean 2.6 s
- **Duplicates: 0 raw-MD5, 0 PCM-MD5 vs 89,249-file corpus; 0 internal**
- Transcripts: 100% present, human-quality, conversational (see QC report)
- Ingested into `dataset_manifest.csv` (+7,500 rows → 96,749 total)

### VietSuperSpeech — partial
- Location: `Unknown_Age/VietSuperSpeech/audio/asr_segments_vietcetera_*/`
- Pilot-verified: 32 samples — WAV 16 kHz mono, genuine interview/conversation
- MIT license; ASR (silver) transcripts — will need Vietnamese-language filtering on ingest

## Resume commands (if interrupted)

```bash
# Bud500 (parquets → archives)
hf download linhtran92/viet_bud500 --repo-type dataset \
  --local-dir "data/raw/archives/Lê Hà/Open_Datasets/Bud500"

# VietSuperSpeech (manifest-driven; skips existing)
.venv/bin/python /tmp/dl_vss.py   # re-run; idempotent
```

## Provenance & storage

| Dataset | Original archive | Extracted audio | License |
|---|---|---|---|
| Bud500 | `archives/…/Bud500/data/*.parquet` | `Unknown_Age/Bud500/{train,test}/` | cc-by-nc-sa-4.0 |
| VietSuperSpeech | downloaded wavs ARE originals | `Unknown_Age/VietSuperSpeech/audio/` | MIT |

Both remain `Unknown_Age` — neither source provides age metadata. No ages inferred.

## Remaining work (blocked on downloads)

1. Extract remaining Bud500 train shards → `Unknown_Age/Bud500/train/` (est. ~52GB → 634k files)
2. Complete VSS fetch (est. ~64k remaining files), then QC + ingest
3. Re-run cross-dataset duplicate audit on full corpora
4. If user accepts the VietSpeech gate → same pipeline applies
