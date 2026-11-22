# Uyên Implementation Report - NoSQL Catalog CAP Lab

## 1. Repository Information

- **Repository URL:** https://github.com/moon-1209/nosql-catalog-cap-lab
- **Base branch:** `main` (`de1d1bd`, repo was effectively empty - only
  `README.md`; remote `develop` is identical)
- **Implementation branch:** `feat/uyen-analysis-pipeline`
- **Started:** 2026-11-05 (~19:35 +07)
- **Completed:** 2026-11-05

Audit note: the repository contained no schemas, scripts, notebooks or
infra config, so Uyên's pipeline was built greenfield. The catalog data
model (Schema A/B) her features document is defined in
`src/catalog_analysis/schemas.py` and `docs/schema/` - presented as
design documentation, not deployed DDL (infra/DDL remains with the
infra track).

## 2. Implementation Summary

| STT | Feature | Commit | Status | Test |
|-----|---------|--------|--------|------|
| 1 | Access Patterns | `e09c0c0` | PASS | docs + CQL reviewed, committed |
| 2 | Chebotko Schema A/B | `e71bcf9` | PASS | SVGs valid XML, regenerated via script |
| 3 | Data Seeder | `a5f691b` | PASS | `test_seeder.py` 3 tests ok; determinism verified |
| 4 | Analysis Notebook | `69c247c` | PASS | executed via nbclient, 0 errors, outputs saved |
| 5 | Data Dictionary | `abf161a` | PASS | all CSV fields documented |
| 6 | Top Partitions Analysis | `058ea90` | PASS | `test_top_partitions.py` 4 tests ok; ran on sample |
| 7 | Hot Partition Charts | `ea8a938` | PASS | 3 PNGs rendered and visually verified |
| 8 | Stale Read Analysis | `795e2a5` | PASS | `test_stale_read.py` 5 tests ok incl. edge cases |
| 9 | Consistency Heatmap/Timeline | `4788236` | PASS | 2 PNGs rendered and visually verified |
| 10 | Bootstrap CI 95% | `84f898f` | PASS | `test_bootstrap_ci.py` 5 tests ok |
| 11 | Final Report & Slides | `a273f53` | PASS | report/slides/Q&A written; simulated data labelled |

## 3. Git Summary

- **Total commits on branch:** 12 (1 `chore` scaffold + 11 feature commits)
- **Commit list (oldest first):**
  - `3dbd0d6` chore: scaffold analysis pipeline project structure
  - `e09c0c0` feat(analysis): add access pattern analysis
  - `e71bcf9` feat(schema): add Chebotko schema A and B diagrams
  - `a5f691b` feat(data): add 500k records seeder
  - `69c247c` feat(notebook): add analysis preparation notebook
  - `abf161a` feat(data): add data dictionary
  - `058ea90` feat(analysis): add top partitions analysis
  - `ea8a938` feat(visualization): add hot partition comparison charts
  - `795e2a5` feat(consistency): add stale read analysis
  - `4788236` feat(visualization): add consistency heatmap timeline
  - `84f898f` feat(statistics): add bootstrap confidence interval 95
  - `a273f53` feat(report): add final report slides and Q&A
- **Branch:** `feat/uyen-analysis-pipeline` (single branch, no extra branches)
- **Push status:** pushed to `origin/feat/uyen-analysis-pipeline`
- **GitHub branch:** https://github.com/moon-1209/nosql-catalog-cap-lab/tree/feat/uyen-analysis-pipeline
- **Key files:** `src/catalog_analysis/{schemas,seeder,top_partitions,hot_partition_charts,stale_read,consistency_viz,bootstrap_ci}.py`, `config/seeder.yaml`, `docs/**`, `notebooks/01_analysis_preparation.ipynb`, `tests/`, `data/sample/`, `results/`

## 4. Testing Summary

- **Suite:** `python -m unittest discover -s tests` - **17 tests, all OK**
- Seeder: byte-identical regeneration, key uniqueness, Zipf skew, validation rules
- Top partitions: grouping both schemas, metric correctness, output files
- Stale read: staleness derivation, unverifiable-read exclusion, zero-denominator and empty-log handling, phase labelling
- Bootstrap: determinism by seed, CI brackets estimate, block bootstrap, NaN/small-sample handling
- Notebook: executed end-to-end via nbclient (kernel `python3`), zero errors/warnings
- Figures: 5 PNGs visually inspected (titles, axes, legends, SIMULATED tag)

## 5. Outstanding Issues

- **Real ScyllaDB benchmark data: absent.** All reported numbers are
  marked `SIMULATED`; cluster experiments (deployed DDL, injected
  partition, observed logs) belong to the infra/benchmark track and are
  PENDING. Analysis modules accept real logs with the same columns.
- `pytest` not installed in the environment; tests use stdlib `unittest`.
- `products_by_id` exists as a design/documented table only (same rows
  as `products.csv`) - no separate CSV emitted.
- Full 500k dataset is git-ignored (`data/full/`); regenerate via seeder.

## 6. Final Status

| Feature | Status |
|---|---|
| 1-11 (all) | **COMPLETED** as analysis/documentation deliverables |
| Real-cluster experimental numbers | **PENDING** (needs infra track) |

Everything implemented is tested, reproducible from committed config +
seed, and clearly separates simulated from observed data.
