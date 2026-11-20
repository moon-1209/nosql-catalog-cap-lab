# Ariadne Dataset — Download & Usage Guide

The complete Ariadne voice dataset (raw audio, ZIP archives, processed WAVs,
manifests and audit reports) is published on the **`feat/data`** branch via
Git LFS. Development branches (`main`, `quang-manh`, other `feat/*`) do **not**
contain the audio — switch to `feat/data` whenever you need the data.

## 1. Prerequisites — Git LFS

Audio/ZIP assets are stored as Git LFS objects. Install LFS **before** cloning
(or run `git lfs pull` afterwards).

**macOS**
```bash
brew install git-lfs
git lfs install        # once per machine
```

**Windows**
```powershell
winget install GitHub.GitLFS
# or download from https://git-lfs.com and run the installer
git lfs install        # once per machine
```

## 2. Get the dataset

**Fresh clone (recommended)**
```bash
git clone --branch feat/data https://github.com/QuangManhAI/Data-Science-Major-Project.git
cd Data-Science-Major-Project
git lfs pull           # downloads all LFS audio objects
```

**Existing clone — switch to the data branch**
```bash
git fetch origin
git switch feat/data
git pull origin feat/data
git lfs pull
```

Verify LFS content (should list audio files, no `*` missing markers):
```bash
git lfs ls-files | head
```

## 3. Dataset layout

```
data/
  annotations.json / annotations.csv      # canonical prompt/intent ground truth
  raw/
    archives/                             # original ZIP exports (untouched)
      Lê Hà/{Nam 20,Nam 30,Nữ 20,Nữ 30}/*.zip
    real_voice/                           # extracted raw audio per batch
      Lê Hà/<group>/<batch>/              # e.g. Nam 20/{A,A2,A3,A4}, Nữ 20/{B..B3,B7,B8}
        metadata.json                     # speaker info (self-reported)
        *.wav                             # NOTE: Lê Hà raws are WebM/Opus 48 kHz
                                          # mono mislabeled .wav (known anomaly)
      Hoàng Tuấn/…, Phương Uyên/…, Female 30/, Male 30/
    _backup_f30_reimport_2026-10-30/      # audit-trail copies (kept intentionally)
src/data/stt/
  processed/real_voice/wav/<mirrored groups>/   # NORMALIZED audio:
                                                # WAV PCM-16, 16 kHz, mono
  manifests/
    download_manifest.csv                 # provenance: zip member → raw file, md5
    stt_dataset_manifest.csv              # processed wavs: duration/sr/ch
  finetuning/datasets/
    unannotated/metadata.csv              # sample_id, paths, speaker_id, intent,
                                          # script_reference, transcript_status
    pending_review|pending_transcripts|train|validation|test|excluded/
  finetuning/scripts/validate_dataset.py  # read-only dataset validator
```

## 4. Raw vs processed — which to use

- **Training/eval pipelines** → use `src/data/stt/processed/**` (16 kHz mono
  PCM-16 WAV) + `finetuning/datasets/*/metadata.csv`.
- **Re-processing or auditing** → use `data/raw/real_voice/**`; decode raws
  with ffmpeg/PyAV (see `scripts/convert_audio.py`, `scripts/stt_paths.py`).
- **Original exports** → `data/raw/archives/**` (provenance only).

Conversion spec (already applied to everything under `processed/`):
`WAV RIFF · PCM 16-bit · 16,000 Hz · mono` via `scripts/convert_audio.py`.

## 5. Validate your copy

```bash
python src/data/stt/finetuning/scripts/validate_dataset.py
```
Expected: `RESULT: PASS` (a warning about empty supervised splits is a known,
pre-existing state — not an error).

## 6. Known dataset issues (do not "fix" silently)

- **A4 (`Lê Hà/Nam 20/A4`)** — incomplete session: only 1/80 prompts recorded.
- **B7/B8 (`Lê Hà/Nữ 20/B7`, `B8`)** — raw audio + archives present, but
  processed WAVs and manifest rows are **not yet generated** (pending import).
- **F30_05 (`Lê Hà/Nữ 30/F30_05`)** — storage-only by design: raw + archive
  exist, no processed WAVs / dataset records (withdrawn subject — decision pending).
- **`Giọng clone/`** — synthetic voice data, intentionally separate from the
  real-voice pool. Do not mix into training data.
- WebM/Opus-in-`.wav` naming anomaly affects all Lê Hà raw batches — decode by
  content, not extension.

See `REPORT DATA.md`, `STT_NAM_U20_IMPORT_REPORT.md` and
`GITHUB_DATA_BRANCH_REPORT.md` for full audits.
