# REVIEW TOOL SMOKE TEST — `--set u`

**Date:** 2026-10-27 · **Branch:** `quang-manh` · Scope: tooling verification only. No training, no model change, no commits.

## 1. Bug found & fixed

- **`--set u` was unreachable:** `SETS` gained the `u` entry but `argparse` still had `choices=["r","n"]` → `invalid choice: 'u'`. Fixed by extending choices to `["r","n","u"]`. Caught by this smoke test — the reason it existed.

## 2. Manifest coverage (`datasets/unannotated/metadata.csv`, 206 rows)

| Group | Rows | In manifest | Audio paths valid |
|---|---|---|---|
| `Female 30` | 71 | ✅ | 71/71 |
| `Male 30` | 25 | ✅ | 25/25 |
| `Phương Uyên/Trẻ con` (Nam 10 + Nữ 10) | 50 | ✅ (`KID_M10_*`/`KID_F10_*`) | 50/50 |
| `Phương Uyên/Nữ 20 tuổi` — `(1)` second takes | 60 | ✅ (`*_dup1`) | 60/60 |
| `Giọng clone` | — | excluded by rule (TTS data, not ASR) | n/a |

- 206/206 `transcript_status=pending_transcription`, `verbatim_transcript` empty.
- 110 rows carry `script_reference` (stem maps to an annotation code); 96 have none (`script_reference=""`, `annotation_source=none`) — no transcripts guessed.
- All `audio_path`/`raw_path` exist on disk (checked), unique `sample_id`s, no ID collides with annotated manifests.

## 3. `--set u` flow test (non-interactive, piped input)

- Manifest selection: correct file opened, 206 pending rows detected.
- Row rendering: sample_id, speaker_id, audio path, script_reference, model_prediction printed; `verbatim>` prompt accepts input.
- Write-back verified: typed transcript `"test transcript âấử"` (Unicode preserved), status `transcribed`, UTC `verification_timestamp` written; `1/206 reviewed` saved. **Test entry was then reverted from backup** — manifest is back to all-pending.
- Status handling: allowed set `pending_transcription|transcribed|verified|unusable_audio|needs_manual_review` enforced; invalid status leaves row pending; `q` saves & quits; empty input skips; `r` replays.
- Audio playback path (`afplay`) exists in code but was **not exercised** (`--no-audio` used; playback belongs to the human reviewer session). User runs: `python src/data/stt/finetuning/scripts/review_tool.py --set u` (without `--no-audio`) to hear files.

## 4. Validator after fix

`validate_dataset.py` → **PASS** — 386 audio paths OK, 0 broken, 0 duplicate IDs, no identical audio across splits, no unverified rows in supervised splits (still empty). Warnings: 0 supervised-eligible (no verified GT yet); only 2 speakers.

## 5. Remaining issues / notes

- `speaker_id` is blank for unannotated rows (group label in `voice_group` instead) — by design; speakers unverified.
- `_n`/`_r` mode inferred from filename only where applicable (`F30_*` has both takes; kids have `_r` only).
- `Giọng clone` deliberately absent from ASR manifests.
- No real transcripts were produced; nothing auto-verified.

## 6. Confirmations

No fine-tuning, no model/dependency changes, no source-audio edits, no fake GT, no commit/push.
