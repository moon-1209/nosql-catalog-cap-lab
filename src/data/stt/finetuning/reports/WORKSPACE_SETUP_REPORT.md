# WORKSPACE SETUP REPORT — STT Fine-tuning

**Date:** 2026-10-27 · **Repo:** Data-Science-Major-Project · **Branch:** `quang-manh`
Scope: workspace setup only — no training, no model changes, no commits.

## 1. Structure created

```
src/data/stt/finetuning/
├── README.md
├── datasets/{train,validation,test,pending_transcripts,excluded}/metadata.csv
├── configs/          (empty — for future configs)
├── scripts/validate_dataset.py
├── experiments/      (empty — for future runs)
└── reports/WORKSPACE_SETUP_REPORT.md
```

## 2. Sample counts by status

| Manifest | Rows | Status |
|---|---|---|
| `train/` | 70 | `script_ref_unverified` (pilot candidates) |
| `validation/` | 6 | `script_ref_unverified` |
| `test/` | 14 | `script_ref_unverified` |
| `pending_transcripts/` | 80 | `_n` takes awaiting verbatim GT |
| `excluded/` | 10 | `excluded_duplicate` (`Nu_C*` ≡ `B_C*_r`, md5-identical) |
| **Total** | **180** | covers all annotation file_ids |

## 3. Path verification

- `wav_path` + `raw_path` checked for all 180 rows: **180 valid, 0 invalid**.
- Paths are repo-root-relative; resolution verified by `validate_dataset.py` (all decode as 16 kHz mono).
- Note: `A_C*` recordings physically live in `Phương Uyên/Nữ 20 tuổi/` (only Drive location) — manifest `raw_path` reflects the real location, not the assumed speaker-A folder.
- The path quoted in the task (`src/data/processed/Phương Uyên/Giọng Clone/`) does not exist; actual clone data is at `data/raw/real_voice/Phương Uyên/Giọng clone/` and `src/data/stt/processed/real_voice/wav/Phương Uyên/Giọng clone/`. Untouched; no dependency on the finetuning workspace. Voice-clone (TTS) and ASR datasets are kept separate.

## 4. Leakage guarantees (enforced by validate_dataset.py)

- Splits are **prompt-group-disjoint** (sentence code, e.g. `A_07`/`C04` in exactly one split) — test texts unseen in training.
- md5 check: no identical audio may appear in two splits — `Nu_C`↔`B_C_r` duplicates are kept out via `excluded/`.
- No `pending_transcripts`/unverified rows inside supervised splits.
- Duplicate `sample_id`s rejected.

## 5. Validation result

`python src/data/stt/finetuning/scripts/validate_dataset.py` → **PASS** (0 errors, 1 warning: only 2 speakers → no speaker-disjoint eval claim).

## 6. Could not verify / limitations

- Script refs for `_r` takes are **assumed verbatim, human-unverified** (`human_verified=0`).
- 80 `_n` transcripts pending — no usable GT for the spontaneous-speech domain.
- Only 2 adult speakers; child/F30/M30 audio has no transcripts.
- Validation split is small (6 rows) — sufficient for smoke-checks, not for reliable early stopping.

## 7. Before pilot training

1. Transcribe ≥40 `_n` takes (manifest ready at `../evaluation/error_analysis/natural_speech_review_manifest.csv`).
2. Human spot-check ≥20 `_r` refs → flip `human_verified=1`.
3. Add `peft`; write LoRA/frozen-encoder train script into `scripts/`.
4. Add ≥1 more annotated adult speaker for speaker-disjoint test.
5. Re-run `validate_dataset.py`; keep baseline eval unchanged.

## 8. Changes outside scope

None — no existing file moved, renamed, or modified; no new dependencies; no commits/pushes.
