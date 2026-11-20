# STT GOOGLE DRIVE ACCESS REPORT

**Date:** 2026-10-27
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh` (verified — up to date with `origin/quang-manh`)
**Drive folder:** https://drive.google.com/drive/folders/1tnp8mY7TyFq7wpwCVWtgLCmTOJipJhW0

---

## Result Classification

| Check | Status |
|---|---|
| DRIVE ACCESS | **PASS** — Public share link; folder enumerated and contents verified |
| AUDIO DOWNLOAD | **PASS** — 170/170 target files downloaded, all decodable |
| GROUND TRUTH MAPPING | **PASS** — 170 exact `file_id` matches; 10 `Nu_Cxx` resolved via documented alias; 180/180 annotations covered |
| STT SMOKE TEST | **PASS** — 6-sample run (model loads locally, plausible transcriptions, metrics computed) |
| FULL BENCHMARK | **PASS** — 180/180 samples evaluated, 0 failures |

---

## 1. Git Status

### Before
```
modified:   models/PhoASR-whisper-small/inference.py
modified:   run_simulation.py
untracked:  ARIADNE_INTEGRATION_TEST_REPORT.md
untracked:  STT_DATA_REORGANIZATION_REPORT.md
untracked:  src/training/experiments/
```

### After
```
modified:   models/PhoASR-whisper-small/inference.py   (pre-existing, untouched)
modified:   run_simulation.py                          (pre-existing, untouched)
modified:   experiments/results/asr_summary.json       (overwritten by new benchmark run)
modified:   scripts/evaluate_asr.py                    (verification fixes, see §7)
untracked:  experiments/results/asr_benchmark_180_samples.csv
untracked:  STT_GOOGLE_DRIVE_ACCESS_REPORT.md          (this file)
(+ prior untracked files unchanged)
```

`data/raw/` and `data/processed/` are gitignored (`.gitignore` lines 13–14) — audio stays local by design. No commits, no pushes, no resets performed.

---

## 2. Google Drive Access Method

| Method | Result |
|---|---|
| `curl` HEAD/GET on folder URL | HTTP 200 — folder is public ("anyone with link") |
| `gdown --folder --json` (gdown 6.4.2, repo `.venv`) | **Success** — full recursive listing: 18,568 entries |
| No Google API/OAuth/rclone needed | Anonymous access sufficient |

No whole-folder download was performed. Listing was parsed locally; only required audio was downloaded via individual `gdown uc?id=<file_id>` calls.

## 3. Actual Drive Contents (verified by `--json` listing)

| Folder | Files | Verdict |
|---|---|---|
| `benchmark_vision_dataset/` | 18,185 (jpg/txt/json) | **Excluded** — unrelated vision benchmark |
| `Hoàng Tuấn/Nam 20 tuổi/` | 70 `.m4a` | **Speaker A** (male, 20): `A_01..A_30_{r,n}` + `Nam_C01..C10` |
| `Phương Uyên/Nữ 20 tuổi/` | 160 `.m4a` | **Speaker B** (female, 20): `B_01..B_30_{r,n}` + `B_C01..C10_{r,n}`; also `A_C01..C10_{r,n}` and `A_01..A_30_{r,n} (1)` duplicates |
| `Phương Uyên/Trẻ con/Nam 10/` | 25 `.m4a` | **Excluded** — child voices, `_r` only, duplicates of A-script ids |
| `Phương Uyên/Trẻ con/Nữ 10/` | 25 `.m4a` | **Excluded** — child voices, same reasoning |
| `Phương Uyên/Giọng clone/` | 7 (`.m4a`/`.wav`) | **Excluded** — voice-clone samples (Trường Giang / Trần Thành) |
| `Male 30/` | 25 `.m4a` (`Mỡ Nướng *`) | **Excluded** — unrelated naming, not in annotations |
| `Female 30/` | 71 `.m4a` (`F30_*`) | **Excluded** — different speaker schema, not in annotations |

## 4. Downloaded Files → `data/raw/real_voice/`

- **170 files downloaded** (~23 MB), ADTS AAC 48 kHz stereo (voice-recorder `.m4a`).
- **10 files created locally**: `Nu_C01..C10.m4a` — byte-identical copies of `B_Cxx_r.m4a`.
  *Rationale:* `Nu_Cxx` and `B_Cxx_r` are alias records of the same prompt (identical speaker, mode=`r`, and text; see `scripts/parse_annotations.py`). No file literally named `Nu_Cxx` exists anywhere on the Drive; the female speaker uploaded her reading-mode common takes as `B_Cxx_r`. This is a name mapping, not fabricated audio — md5 recorded in the inventory.
- **Skipped intentionally:** `A_01..A_30_{r,n} (1)` duplicate copies in `Nữ 20 tuổi` (canonical A files sourced from `Hoàng Tuấn/Nam 20 tuổi`); all other excluded folders above.
- **Note (provenance caveat):** `A_C01..C10_{r,n}` was found only inside `Phương Uyên/Nữ 20 tuổi/`. Filenames match annotation aliases exactly, but the recordings may be the female voice rather than speaker A. This does not affect WER/CER (ground truth text identical) but is flagged for transparency.

## 5. Annotation Coverage (`data/annotations.json`, 180 records)

| Bucket | Count | Coverage |
|---|---|---|
| `A_01..A_30_{r,n}` | 60 | ✅ exact match (Hoàng Tuấn) |
| `A_C01..C10_{r,n}` | 20 | ✅ exact match (Phương Uyên folder) |
| `B_01..B_30_{r,n}` | 60 | ✅ exact match (Phương Uyên) |
| `B_C01..C10_{r,n}` | 20 | ✅ exact match (Phương Uyên) |
| `Nam_C01..C10` | 10 | ✅ exact match (Hoàng Tuấn) |
| `Nu_C01..C10` | 10 | ⚠️ no literal file — mapped to `B_Cxx_r` (same utterance) |
| **Total** | **180** | **180/180 covered** |

Unmatched/unexpected files: none among downloaded set. Missing: none.

## 6. Integrity & Conversion

- ffprobe: all 170 downloads decodable, duration > 0. Zero corrupt files.
- Spot check: `A_01_r` duration 4.72 s vs prior benchmark's 4.628 s — consistent.
- `scripts/convert_audio.py` (PyAV backend): **180/180 converted** → `data/processed/real_voice/*.wav`.
- Verification via soundfile: all WAVs = **16 kHz, mono, PCM_16**. Total: 854.6 s (14.2 min).
- Durations for all 70 files in the previous benchmark match within 0.5 s → same source dataset confirmed.
- Inventory: `data/processed/real_voice/download_inventory.csv` (file_id, size, md5, duration, Drive source path, mapping note).

## 7. `scripts/evaluate_asr.py` — Review & Minimal Fixes

Verified: GT loaded from `data/annotations.json` by `file_id`; normalization = lowercase + strip punctuation + collapse whitespace (applied uniformly to WER/CER); WER/CER via jiwer (raw + normalized); RTF = inference_time / audio_duration; results → `experiments/results/`.

Fixes applied (verified by `py_compile` + smoke test):
- `Nu_C*` now categorized as `common` (previously fell into `natural`).
- Annotations without audio / audio without annotation now print explicit WARNINGs.
- Per-file failures are caught, logged, collected into `failed_samples` in the summary JSON instead of crashing the run.
- Per-sample CSV written to `asr_benchmark_<N>_samples.csv` — prior 70-sample CSV preserved.
- Removed unused `OUT_CSV` constant.

## 8. Benchmark Results (actually executed — CPU, PhoASR-whisper-small)

Smoke test: 6 files, PASS. Full run: **180/180 files, 0 failures.**

| Category | Samples | Norm WER | Norm CER | Norm. Sentence Acc |
|---|---|---|---|---|
| Reading (_r) | 80 | 8.75% | 5.95% | 61.25% |
| Common (C) | 20 | 10.53% | 6.74% | 70.00% |
| Natural (_n) | 80 | 51.78% | 42.90% | 1.25% |
| **OVERALL** | **180** | **28.73%** | **23.04%** | **35.56%** |

Raw WER 38.42%; mean RTF 0.151× (CPU). High natural-mode WER is expected — `_n` takes intentionally deviate from the script text. Outputs: `experiments/results/asr_benchmark_180_samples.csv`, `asr_summary.json`.

## 9. Remaining Issues / Next Steps

- `Nu_Cxx` audio is shared with `B_Cxx_r` — deduplicate by md5 if unique-utterance accounting is needed (see `download_inventory.csv`).
- Provenance of `A_Cxx` files (female folder) unverifiable without listening; flagged in §4.
- `data/processed/manifest.csv` (Godot voice pipeline, different schema) left untouched — populated by `sim_vision/python/voice/` tooling, not this benchmark.
- `asr_summary.json` now reflects the 180-file run; the previous 70-sample CSV remains as `asr_benchmark_70_samples.csv` (prior summary recoverable via git).
