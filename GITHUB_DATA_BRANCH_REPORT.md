# feat/data — Ariadne Dataset Branch Publication Report

**Date:** 2026-11-05 · **Repo:** `QuangManhAI/Data-Science-Major-Project`
**Branch:** https://github.com/QuangManhAI/Data-Science-Major-Project/tree/feat/data
**Result:** ✅ Published — 3,249 files, 3,136 Git LFS assets (448 MB), validator PASS.

---

## A. Git Branch Audit

| Item | Value |
|---|---|
| Branches before | local: `main`, `quang-manh` — remote: `main`, `quang-manh`, `feat/hospital-env`, `feat/hospital-vision-dataset`, `feat/vision-eval-benchmark`, `fix/camera-views` |
| `feat/data` existed remotely? | No → created fresh |
| Source commit | `483037a` (`origin/quang-manh`, verified in-sync before branch) |
| New branch commit | **`d79e4d6`** `feat(data): publish complete Ariadne datasets` |
| Push | `git push -u origin feat/data` → `[new branch]`, tracking set |
| Remote ref after push | `d79e4d60abf4…` == local `feat/data` ✓ |
| Other branches | `main` `f00b81b`, `quang-manh` `483037a`, all `feat/*` — **unchanged** |
| Working tree | All prior uncommitted changes + untracked files preserved, none committed (verified: staged set = dataset + reports only) |

`.gitignore` note: dev branches keep dataset-local rules. `feat/data` adds a clearly-marked un-ignore block for `data/raw`, `data/processed`, `src/data/stt` (+ explicit `!/src/data/stt/processed/` — parent-dir exclusion required it). The user's pending `.gitignore` edit (`/src/data/stt/processed/`) is preserved in the block above it.

## B. Dataset Inventory (published on feat/data)

| Category | Files | Size |
|---|---|---|
| Raw audio (`data/raw/real_voice/`) | 1,533 (+16 metadata.json) | 129.4 MB |
| ZIP archives (`data/raw/archives/`) | 16 | 93.1 MB |
| Audit-trail backup (`data/raw/_backup_f30_reimport_2026-10-30/`) | 280 audio + 3 zips + manifests | 77.3 MB |
| Processed audio (`src/data/stt/processed/`) | 1,304 WAV (PCM-16·16kHz·mono) | 173.5 MB |
| Manifests (`src/data/stt/manifests/`, `finetuning/datasets/`) | ~45 csv/md | ~8.5 MB |
| Metadata & reports (`annotations.*`, `REPORT DATA.md`, `STT_*`, `audio_inventory.csv`, guides) | ~15 | ~2 MB |
| **Total staged this commit** | **3,249** | **~484 MB** |

## C. Git LFS Statistics

| Metric | Value |
|---|---|
| LFS patterns (`.gitattributes`) | `*.wav *.m4a *.aac *.mp3 *.webm *.flac *.ogg *.zip` |
| LFS pointers on `origin/feat/data` | **3,136** (100% of staged binaries verified as 3-line pointers) |
| Unique LFS objects uploaded | **2,905 / 2,905 — 448 MB** (content dedup: 231 backup copies share OIDs) |
| Largest objects | `Bản sao của F30.zip` (11.0 MB), `F30_02.zip` (11.0 MB), `B7.zip` (8.9 MB) |
| Upload status | complete at ~474 KB/s; no quota error |
| Quota check | not queryable without admin API — upload succeeded fully |

Not uploaded (correctly): `.venv/`, `__pycache__`, `.pytest_cache`, `.DS_Store`, `.idea`, experiment checkpoints/DBs, model weights (still gitignored), unrelated WIP code changes.

## D. Data Integrity

| Check | Result |
|---|---|
| LFS pointers = 3-line `oid sha256:` blobs | ✅ 3,136/3,136, zero raw binaries committed |
| SHA-256 spot checks (remote oid vs local file) | ✅ A2.zip `c3edf79e…`, A3.zip `106aa6db…`, A2/A3 processed WAVs — all match |
| ZIP integrity (source audit) | ✅ 3/3 new zips `unzip -t` clean |
| Duplicate content | 231 duplicate *paths* (backup audit trail — intentional), 0 unexplained |
| Raw↔processed consistency | ✅ validated: every manifest path exists, 16 kHz mono verified |
| `validate_dataset.py` | ✅ **PASS** — 0 broken audio paths, 1,117 unannotated rows, unique sample_ids (1 pre-existing warning: empty supervised splits) |
| File counts remote vs local audit | ✅ real_voice 1,549 entries, processed 1,304, zips 19 (16+3 backup) |

## E. Known Issues (documented, not hidden)

1. **A4 (`Lê Hà/Nam 20/A4`)** — incomplete session, 1/80 prompts.
2. **B7/B8 (`Lê Hà/Nữ 20/`)** — raw + archive published; processed WAVs & manifest rows pending import (`audio_inventory.csv` marks them `in_manifest=False`).
3. **F30_05** — storage-only by design (no processed/records).
4. **`REPORT DATA.md`** — 2026-11-01 snapshot, predates B7/B8/A2-A4; superseded by regenerated `audio_inventory.csv` (4,469 rows, probed 2026-11-05) + this report + `STT_NAM_U20_IMPORT_REPORT.md`.
5. `Giọng clone/` synthetic voices — published but segregated; exclude from training.

## F. Team Instructions

```bash
# one-time
brew install git-lfs        # macOS   (Windows: winget install GitHub.GitLFS)
git lfs install

# get the dataset
git clone --branch feat/data https://github.com/QuangManhAI/Data-Science-Major-Project.git
cd Data-Science-Major-Project && git lfs pull

# or from an existing clone
git fetch origin && git switch feat/data && git lfs pull
```

Full guide: **`DATASET_DOWNLOAD_GUIDE.md`** (on this branch).

## G. Final Status

| Item | Status |
|---|---|
| `feat/data` exists on GitHub at `d79e4d6` | **PASS** |
| Existing branches untouched | **PASS** |
| All approved dataset dirs present | **PASS** |
| LFS objects uploaded (2,905/2,905) | **PASS** |
| No legitimate dataset file silently omitted | **PASS** (junk/caches/secrets excluded by design) |
| Dataset integrity (hashes, validator) | **PASS** |
| Team download guide | **PASS** |
| LFS remaining quota | **NOT VERIFIED** — needs GitHub admin/API; upload itself succeeded |
| B7/B8 processed+manifest rows | **WARNING** — known gap, not generated (documented) |
| A4 incomplete session | **WARNING** — 1/80 prompts, documented |
