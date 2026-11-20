# SCRIPT MAPPING AUDIT — review_tool `--set u`

**Date:** 2026-10-27 · **Branch:** `quang-manh` · Data/manifest-only; no training, no deps, no commits.

## 1. Records that HAVE a script (verified source)

| Group | Count | Script source |
|---|---|---|
| Kids `Trẻ con/Nam 10` + `Nữ 10` (`KID_*` ids) | 50 | `data/annotations.json` via exact stem (`A_01..15_r`, `A_C01..10_r`) |
| `Nữ 20 tuổi` "(1)" second takes (`*_dup1`) | 60 | `data/annotations.json` via stem minus " (1)" suffix |
| `Female 30` — `F30_C01..C10_{r,n}` | **20 (fixed)** | `docs/kich_ban_thu_am.md` §5 "Câu chung" C01–C10 texts, mapped by exact code `F30_C0X → C0X`; flagged `annotation_source=…inferred: shared C-code` + reviewer note to verify while listening |
| **Total with script** | **130/206** | |

## 2. Records that truly have NO script

| Group | Count | Reason |
|---|---|---|
| `Female 30` — `F30_T01..T25_{r,n}` (+`F30_T08_n_wrong-order`) | 51 | T-codes = F30's own sentences; no script text exists in `docs/` or annotations |
| `Male 30` — `Mỡ Nướng *` | 25 | Free-speech filenames, no matching code anywhere |

Script fields left empty for these — nothing guessed.

## 3. Why scripts were missing before

No code bug in `review_tool.py` — it prints `row['script_reference']` verbatim. The manifest builder only mapped stems that exactly equal an annotation `file_id`; `F30_C0X_r` ≠ `C0X`/`Nam_C0X`/`B_C0X_r`, so the shared C-code relation was missed. Fixed in the manifest (not the display code).

## 4. Changes

- `datasets/unannotated/metadata.csv`: 20 `F30_C*` rows gained `script_reference` (with inference flag + note). No other manifest/code/annotation/audio touched.
- `review_tool.py`: unchanged (earlier `choices` fix for `--set u` was already applied).

## 5. Tests

| Case | ID | Result |
|---|---|---|
| Has script | `KID_M10_A_01_r` | shows "Chào bạn, cho mình hỏi chỗ đăng ký…" ✔ |
| Inferred mapping | `F30_C01_n` | shows "Cho tôi hỏi khoa tim mạch ở đâu?" (C01) ✔ |
| Second take | `A_01_r_dup1` | shows A_01 script ✔ |
| No script | `Mỡ Nướng 10`, `F30_T01_r` | blank ✔ |

`validate_dataset.py` → **PASS** (386 paths OK, 0 errors; expected warnings: empty supervised splits, 2 speakers).

## 6. Remaining issues

- `F30_C*` script mapping is **code-inferred, not human-verified** — reviewer confirms during listening (flagged per-row).
- `F30_T*`/`Mỡ Nướng` need verbatim transcripts with no script aid — hardest review rows.
- Playback (`afplay`) exercised only in `--no-audio` dry mode; human session still required.
