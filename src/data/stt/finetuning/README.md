# STT Fine-tuning Workspace

Isolated workspace for preparing and validating data for future Vietnamese ASR
(PhoASR / Whisper-small) fine-tuning experiments. **No training happens here
yet** — see "Why no fine-tuning yet" below.

## Layout

```
finetuning/
├── README.md                     this file
├── datasets/                     manifests only — audio is NOT copied here
│   ├── train/metadata.csv        70 rows — pilot candidates (script ref, unverified)
│   ├── validation/metadata.csv    6 rows — pilot candidates
│   ├── test/metadata.csv          14 rows — pilot candidates
│   ├── pending_transcripts/metadata.csv  80 rows — _n takes awaiting verbatim GT
│   └── excluded/metadata.csv      10 rows — excluded_duplicate (Nu_C* = B_C*_r audio)
├── configs/                      future fine-tuning configs
├── scripts/validate_dataset.py   read-only manifest/audio/split checker
├── experiments/                  future runs + checkpoints
└── reports/WORKSPACE_SETUP_REPORT.md
```

All `wav_path` / `raw_path` fields are **repo-root-relative** and verified by
`validate_dataset.py`. Audio stays in `data/raw/real_voice/` and
`src/data/stt/processed/real_voice/wav/` — never copy WAVs into this workspace.

## Data statuses

| status | meaning | usable for supervised FT |
|---|---|---|
| `script_ref_unverified` | transcript = original script; speaker read it aloud, but no human verified verbatim accuracy | pilot-candidate only |
| `pending_transcripts` | `_n` spontaneous take; script is NOT a valid reference | no — needs verbatim transcript |
| `excluded_duplicate` | byte-identical audio already in the dataset under another ID | no |
| `excluded_unverified` | neither audio nor reference usable | no |

## Adding verified transcripts

1. Transcribe `pending_transcripts` rows (or the 80-file review manifest at
   `../evaluation/error_analysis/natural_speech_review_manifest.csv`).
2. Store the verbatim text in a `transcript` update with
   `transcript_source=verbatim_human`, `human_verified=1`,
   `transcript_status=verbatim_verified`.
3. Only then may a row move to train/validation/test — reassign by
   `prompt_group`, never randomly per-file.
4. Re-run `validate_dataset.py` after every manifest change.

## Split & leakage rules

- Splits are **prompt-group-disjoint**: a `prompt_group` (sentence code such as
  `A_07` or `C04`) appears in at most one of train/validation/test — so the
  test set contains utterance *texts* the model never saw in training.
- `excluded_duplicate` rows (Nu_Cxx ↔ B_Cxx_r, md5-identical audio) can never
  enter any split twice.
- **Speaker-disjoint evaluation is NOT possible**: only 2 adult speakers (A:
  male ~20, B: female ~20). A speaker-held-out test would leave no dev speaker
  and is therefore not claimed.
- Child voices (`Trẻ con/`), `Female 30`, `Male 30`, and voice-clone samples
  exist on disk but have no transcripts — out of scope until annotated.

## Validate the data

```bash
python src/data/stt/finetuning/scripts/validate_dataset.py
```

Checks: manifest readability, stable sample IDs, audio existence + 16 kHz mono
decode, duplicate IDs, same-audio-across-splits (md5), unverified transcripts
in supervised splits, prompt-group leakage, required fields. Read-only —
never modifies data. Exits non-zero on errors.

## Why no fine-tuning yet

Per `../STT_FINETUNING_READINESS_REPORT.md` (**CONDITIONALLY READY**):
- 0 human-verified transcripts; the 80 `_n` takes (the actual target domain)
  have no usable Ground Truth.
- ~7 min of eligible script-referenced audio — enough to validate a training
  pipeline, not to produce a better model.
- 242 M-param Whisper-small on ~7 min of audio ⇒ full fine-tuning would
  overfit; a pilot should use LoRA/PEFT or a frozen encoder.

## Current dataset limitations

- 2 adult speakers only → no speaker-generalization claims.
- `Nu_C*` are alias copies of `B_C*_r` — kept in `excluded/`.
- `A_C*`/`A_*_(1)` recordings live inside the female speaker's Drive folder —
  provenance ambiguous (flagged in upstream manifests).
- Script references for `_r` takes are assumed verbatim but not human-verified.
