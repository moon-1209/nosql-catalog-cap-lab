# STT DATA DOWNLOAD REPORT

**Date:** 2026-10-27
**Repository:** `/Users/pickapu/Documents/PyCharmMiscProject/Data-Science-Major-Project`
**Branch:** `quang-manh`
**Source:** https://drive.google.com/drive/folders/1tnp8mY7TyFq7wpwCVWtgLCmTOJipJhW0

---

## 1. Discovered Source Hierarchy

Full recursive enumeration via `gdown --folder --json` (gdown 6.4.2, public "anyone with link" access — no OAuth required): **18,568 entries total**, of which the voice dataset subtree contains **383 files** across **10 directories**:

```
<Drive root>/
├── Female 30/                          71 .m4a  (F30_T01..T25_{r,n}, F30_C01..C10_{r,n}, F30_T08_n_wrong-order)
├── Male 30/                            25 .m4a  ("Mỡ Nướng …" free-speech takes)
├── Hoàng Tuấn/
│   └── Nam 20 tuổi/                    70 .m4a  (A_01..A_30_{r,n}, Nam_C01..C10)
├── Phương Uyên/
│   ├── Nữ 20 tuổi/                    160 .m4a  (B_01..B_30_{r,n}, B_C01..C10_{r,n},
│   │                                          A_C01..C10_{r,n}, A_01..A_30_{r,n} "(1)" dups)
│   ├── Trẻ con/Nam 10/                 25 .m4a  (A_01..A_15_r, A_C01..C10_r — child voice)
│   ├── Trẻ con/Nữ 10/                  25 .m4a  (A_01..A_15_r, A_C01..C10_r — child voice)
│   └── Giọng clone/                     7 files (voice-clone samples, .m4a + .wav)
└── benchmark_vision_dataset/        18,185 files — NOT voice data; intentionally excluded
                                      (images/labels for the vision benchmark)
```

## 2. Download Results

| Metric | Count |
|---|---|
| Voice-tree files discovered | 383 |
| Downloaded to `data/raw/real_voice/` | **383 / 383 (100%)** |
| Failed / inaccessible | **0** |
| Local-derived additions | 10 (`Nu_C01..C10.m4a` — see §4) |
| Total local files under `data/raw/real_voice/` | **393** (~34 MB) |
| Empty files | 0 |
| Undecodable files (ffprobe) | 0 |

**Method:** per-file `curl "uc?export=download&id=<file_id>"` preserving full relative paths (spaces and Vietnamese names kept verbatim). The gdown per-file endpoint became rate-limited after ~340 requests; the plain `uc?export=download` endpoint worked for the remainder. No whole-folder download was attempted.

**Manifest:** `src/data/stt/manifests/download_manifest.csv` — every file: Drive relative path, local path, extension, size (bytes), duration, local **md5**, download status, verification status.
*Limitation:* the public listing does not expose remote file sizes or md5s, so remote↔local comparison was verified by path coverage + non-zero size + audio readability (ffprobe) rather than checksum equality.

## 3. Local Hierarchy Verification

```
data/raw/real_voice/
├── Female 30/                  71 files   ✔ matches Drive
├── Male 30/                    25 files   ✔ matches Drive
├── Hoàng Tuấn/Nam 20 tuổi/     70 files   ✔ matches Drive
├── Phương Uyên/
│   ├── Nữ 20 tuổi/            160 files   ✔ matches Drive
│   ├── Trẻ con/Nam 10/         25 files   ✔ matches Drive
│   ├── Trẻ con/Nữ 10/          25 files   ✔ matches Drive
│   └── Giọng clone/             7 files   ✔ matches Drive
└── Nu_C01..C10.m4a             10 files   (local-derived, not on Drive)
```

- 170 files already downloaded in the prior session were **moved** into their provenance folders (per `download_inventory.csv` drive_source) instead of re-downloaded.
- 213 remaining files downloaded this session; 0 overwrites of identical content (moved files were relocated, not copied).
- Filename collisions: none on disk. `Trường Giang.m4a` + `Trường Giang.wav` (and `Trần Thành.*` pair) share stems — handled in conversion (§5).

## 4. Known Gaps / Anomalies (documented, not blocking)

- **`Nu_C01..C10.m4a` does not exist on Drive.** `Nu_Cxx` and `B_Cxx_r` are alias records for the same prompt (same speaker/mode/text per `parse_annotations.py`). Local root-level `Nu_Cxx.m4a` are byte-identical copies of `Phương Uyên/Nữ 20 tuổi/B_Cxx_r.m4a` — flagged `local-derived` in the manifest.
- `A_C01..C10_{r,n}` and the `A_*_(1)` duplicates live inside the **female** speaker's folder — provenance ambiguous (speaker-A script recorded by her, or misplaced uploads). Noted in manifest; benchmark uses them as annotated.
- `benchmark_vision_dataset/` (18,185 image/label files) excluded as non-voice; can be fetched later if needed.

## 5. Processed Dataset — `src/data/stt/`

```
src/data/stt/
├── processed/real_voice/wav/   393 wavs, mirrors raw hierarchy, 16 kHz mono PCM_16
├── manifests/
│   ├── download_manifest.csv       (393 rows — remote→local verification)
│   └── stt_dataset_manifest.csv    (393 rows — file_id/speaker/mode/in_benchmark)
└── evaluation/
    ├── predictions/asr_predictions_180_samples.csv
    ├── metrics/asr_summary.json
    └── error_analysis/error_analysis_180_samples.csv
```

- Conversion: `scripts/convert_audio.py` now recurses and mirrors relative paths; same-stem `.m4a`+`.wav` pairs keep `<name>.m4a.wav` for the m4a variant (Unicode-NFC-aware collision check — APFS normalizes filenames).
- All 393 outputs verified 16 kHz / mono / PCM_16.
- `stt_dataset_manifest.csv` marks `in_benchmark=1` for the 180 canonical wavs (all 180 annotation `file_id`s covered) and preserves speaker folder metadata for every other recording.
- Old flat copies `data/processed/real_voice/*.wav` removed after byte-identical verification (md5) against the new set. `data/processed/manifest.csv` + `data/processed/wav/` (Godot voice pipeline) untouched.
- Ground truth remains at `data/annotations.json` / `data/annotations.csv` — unchanged, not duplicated.

## 6. Script/Config Path Updates

| File | Change |
|---|---|
| `scripts/stt_paths.py` | **New** — centralized repo-root-relative paths (`RAW_DIR`, `ANNOTATIONS_FILE`, `PROCESSED_WAV_DIR`, `MANIFESTS_DIR`, `EVAL_*`, `BENCHMARK_SOURCE_DIRS`). |
| `scripts/convert_audio.py` | Uses `stt_paths`; `rglob` recursion; mirrors hierarchy into `src/data/stt/processed/real_voice/wav/`; collision-safe naming. |
| `scripts/evaluate_asr.py` | Uses `stt_paths`; recursive wav discovery; evaluates only annotation-mapped wavs, one per `file_id`, preferring canonical speaker folders (`Hoàng Tuấn/Nam 20 tuổi`, `Phương Uyên/Nữ 20 tuổi`, root for `Nu_C`); `Nu_C*` categorized `common`; warnings for missing/unannotated audio; per-file failure tolerance; outputs → `src/data/stt/evaluation/{predictions,metrics,error_analysis}/`. |
| `scripts/test_asr.py` | Uses `stt_paths`; default sample → `Hoàng Tuấn/Nam 20 tuổi/A_01_n` (raw + processed). |
| `scripts/parse_annotations.py` | **Unchanged** — writes `data/annotations.{json,csv}` (originals stay canonical). |
| `sim_vision/python/voice/config.py` | **Unchanged** — serves the Godot dialogue pipeline (`data/processed/wav/` + `manifest.csv` schema); intentionally separate from the STT benchmark layout. |
| `sim_vision/python/voice/prepare_data.py` | `iterdir()` → `rglob("*")` so the Godot pipeline still sees audio now that `real_voice/` is hierarchical; duplicate/unparseable names still land in `skipped.csv`. |
| `experiments/results/` | Prior outputs **preserved** (`asr_benchmark_70_samples.csv`, `asr_benchmark_180_samples.csv`, `asr_summary.json`). New eval writes exclusively to `src/data/stt/evaluation/`. |

## 7. Tests Performed

| Test | Result |
|---|---|
| Drive enumeration (`gdown --folder --json`) | PASS — 18,568 entries listed |
| Download completeness (remote paths ↔ local files) | PASS — 383/383, 0 failures, 0 empty |
| Audio readability (ffprobe, all 393) | PASS — all decodable |
| Conversion to 16 kHz mono (393 files) | PASS — 393/393 outputs |
| `stt_dataset_manifest.csv` coverage | PASS — 180/180 annotation ids have canonical wavs |
| `py_compile` on all edited scripts | PASS |
| `scripts/test_asr.py` (model smoke test, new paths) | PASS — transcribes `A_01_n.wav`, shows GT |
| Full benchmark `scripts/evaluate_asr.py` | PASS — **180/180 samples, 0 failed** |

**Benchmark metrics (real run, CPU):** Overall norm WER **28.73%**, norm CER 23.04%, RTF 0.143× — reading 8.75% / common 10.53% / natural 51.78%. Consistent with the previous run (natural-mode deviation from script is expected).

## 8. Git Status

```
 M .gitignore                              (+ /src/data/stt/processed/ exclusion)
 M experiments/results/asr_summary.json    (previous run — pre-existing change)
 M models/PhoASR-whisper-small/inference.py (pre-existing, untouched)
 M run_simulation.py                        (pre-existing, untouched)
 M scripts/convert_audio.py
 M scripts/evaluate_asr.py
 M scripts/test_asr.py
 M sim_vision/python/voice/prepare_data.py
?? scripts/stt_paths.py
?? src/data/stt/   (manifests + evaluation tracked; processed wavs ignored)
?? STT_DATA_DOWNLOAD_REPORT.md  (+ prior session reports)
```

`data/raw/`, `data/processed/`, and `src/data/stt/processed/` are gitignored per repo policy (data stays local). No commits/pushes; no branches switched; all pre-existing user changes preserved.

## 9. Manual Action Required

- None for the STT benchmark itself.
- Optional: if `benchmark_vision_dataset/` is also needed locally, it must be downloaded separately (~18k image/label files).
- Optional: the `Nu_Cxx` alias copies can be deduplicated at analysis time via manifest md5s.
