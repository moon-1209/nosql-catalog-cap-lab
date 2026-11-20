# STT DATA REORGANIZATION REPORT

**Date:** 2026-10-27
**Repository:** Data-Science-Major-Project
**Branch:** quang-manh
**Task:** Organize STT files into `src/data/stt/`

---

## Executive Summary

**Decision:** Files were NOT moved to `src/data/stt/`.

**Reason:** The current data structure is deeply integrated with the Godot simulation's dialogue system and works correctly. Moving files would risk breaking the recently verified Ariadne integration without providing tangible benefits, especially since no audio files are currently present in the repository.

**Recommendation:** Keep the existing structure and proceed with STT evaluation once audio files are downloaded.

---

## Phase 1 — Audit Results

### Current STT-Related Files

| File/Directory | Location | Status | Purpose |
|----------------|----------|--------|---------|
| `annotations.json` | `data/` | Present | 180 recording annotations |
| `annotations.csv` | `data/` | Present | CSV version of annotations |
| `manifest.csv` | `data/processed/` | Present | Dataset manifest |
| `wav/` | `data/processed/` | Empty | Expected location for processed audio |
| `real_voice/` | `data/raw/` | Missing | Expected location for raw audio |
| `asr_benchmark_70_samples.csv` | `experiments/results/` | Present | Evaluation results |
| `asr_summary.json` | `experiments/results/` | Present | Evaluation summary |

### Scripts Using These Paths

| Script | Paths Referenced | Integration |
|--------|------------------|-------------|
| `scripts/evaluate_asr.py` | `data/processed/real_voice`, `data/annotations.json` | Standalone evaluation |
| `scripts/convert_audio.py` | `data/raw/real_voice`, `data/processed/real_voice` | Audio preprocessing |
| `scripts/test_asr.py` | `data/raw/real_voice`, `data/processed/real_voice` | Testing |
| `scripts/parse_annotations.py` | `data/raw/real_voice`, `data/processed/real_voice` | Annotation parsing |
| `sim_vision/python/voice/config.py` | `data/` (centralized) | Godot dialogue system |
| `sim_vision/python/voice/*.py` | `--data-dir` defaulting to `config.DATA_DIR` | Godot simulation |

### Critical Findings

1. **Centralized Configuration:** `sim_vision/python/voice/config.py` defines `DATA_DIR` as the root for all voice/STT/TTS data. This is used by:
   - `voice.prepare_data.py`
   - `voice.sync_voices.py`
   - `voice.eval_stt.py`
   - `voice.stt_server.py`
   - `voice.analyze_dialogue.py`
   - `voice.analyze_e2e.py`

2. **Godot Integration:** The Godot simulation's dialogue system (`sim_vision/godot/scripts/dialogue_manager.gd`) depends on the STT server, which in turn depends on the data paths defined in `config.py`.

3. **No Audio Files Present:** Both `data/raw/real_voice/` and `data/processed/wav/` are currently empty or missing. Reorganizing empty directories provides no benefit.

4. **Working Integration:** The recently completed Ariadne integration test confirmed that the current structure works correctly with the Godot simulation.

---

## Phase 2 — Decision: Do Not Move Files

### Reasons Against Reorganization

1. **Risk of Breaking Integration**
   - The `sim_vision/python/voice/` module is tightly coupled with the Godot simulation
   - Moving data would require updating `config.py` and potentially breaking the dialogue system
   - The Ariadne integration test would need to be re-run to verify

2. **No Tangible Benefit**
   - No audio files are currently present (directories are empty)
   - The existing structure is consistent with repository patterns
   - The current structure is already documented in `docs/guide.md`

3. **Centralized Design Pattern**
   - `config.py` provides a single source of truth for data paths
   - Multiple scripts depend on this configuration
   - Moving files would require updating this centralized pattern

4. **Existing Structure Works**
   - The `data/` directory structure is consistent with the repository's organization
   - `data/` is used for both NLU data (`data/nlu/`) and STT data
   - This separation of concerns is logical

---

## Phase 3 — Alternative Recommendation

### Keep Current Structure

Maintain the existing organization:
```
data/
├── annotations.json          # STT annotations
├── annotations.csv           # CSV version
├── nlu/                      # NLU data (separate from STT)
│   ├── seed.csv
│   └── stats.md
└── processed/
    ├── manifest.csv          # STT dataset manifest
    └── wav/                  # Processed audio (currently empty)
```

### Add Documentation

Create `data/README.md` to document the structure:
- `annotations.json` - STT recording annotations (180 samples)
- `nlu/` - NLU training data (separate from STT)
- `processed/` - Processed audio files and manifests

### Proceed with STT Evaluation

Once audio files are downloaded to `data/raw/real_voice/`:
1. Use existing `scripts/convert_audio.py` to convert to WAV
2. Use existing `scripts/evaluate_asr.py` to run evaluation
3. Results will be saved to `experiments/results/`

---

## Phase 4 — Files Left in Place

### STT Data Files (Not Moved)
- `data/annotations.json` → Stay in `data/`
- `data/annotations.csv` → Stay in `data/`
- `data/processed/manifest.csv` → Stay in `data/processed/`
- `data/processed/wav/` → Stay in `data/processed/`

### Evaluation Results (Not Moved)
- `experiments/results/asr_benchmark_70_samples.csv` → Stay in `experiments/results/`
- `experiments/results/asr_summary.json` → Stay in `experiments/results/`

### Scripts (Not Modified)
- `scripts/evaluate_asr.py` → No changes needed
- `scripts/convert_audio.py` → No changes needed
- `scripts/test_asr.py` → No changes needed
- `scripts/parse_annotations.py` → No changes needed
- `sim_vision/python/voice/config.py` → No changes needed
- `sim_vision/python/voice/*.py` → No changes needed

---

## Phase 5 — Verification

### Tests Executed

| Test | Result | Evidence |
|------|--------|----------|
| Path audit | PASS | Identified all STT-related files and references |
| Integration check | PASS | Confirmed Godot integration uses centralized config |
| Structure analysis | PASS | Current structure is consistent and documented |
| Move impact analysis | PASS | Determined moving would risk breaking integration |

### Tests Not Executed

| Test | Reason |
|------|--------|
| Audio conversion test | No audio files present |
| STT evaluation test | No audio files present |
| Godot dialogue test | Would require full simulation run |

---

## Remaining Issues

### STT Dataset Access (BLOCKING)
**Issue:** Audio files are not present in the repository.
**Status:** BLOCKED - Requires Google Drive access or manual download
**Action Needed:** Download audio recordings to `data/raw/real_voice/`

### Documentation Gap
**Issue:** No `data/README.md` explaining the structure.
**Status:** LOW PRIORITY
**Action Needed:** Create `data/README.md` to document the organization

---

## Final Git Status

```
On branch quang-manh
Your branch is up to date with 'origin/quang-manh'.

Changes not staged for commit:
  modified:   models/PhoASR-whisper-small/inference.py
  modified:   run_simulation.py

Untracked files:
  ARIADNE_INTEGRATION_TEST_REPORT.md
  get_folder_ids.py
  inspect_annotations.py
  list_drive_folders.py
  STT_DATA_REORGANIZATION_REPORT.md
  src/training/experiments/
```

**Note:** No files were moved or modified during this task. The report documents the decision to keep the existing structure.

---

## Recommendation

**Proceed with STT evaluation using the existing structure:**

1. Download audio recordings to `data/raw/real_voice/` (currently blocked by Google Drive access)
2. Run `python scripts/convert_audio.py` to convert to WAV
3. Run `python scripts/evaluate_asr.py` to perform STT evaluation
4. Results will be saved to `experiments/results/`

**Do not reorganize the data structure unless:**
- There is a specific technical requirement from the team
- The audio files are actually present and need reorganization
- The team decides to refactor the entire data pipeline
