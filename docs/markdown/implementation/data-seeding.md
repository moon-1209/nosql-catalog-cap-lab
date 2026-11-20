# Data Seeder

`src/catalog_analysis/seeder.py` generates the catalog dataset and the
simulated workload logs used by the analysis pipeline. Everything is
driven by `config/seeder.yaml` + a seed - no hardcoded counts or skew.

## Run

```bash
# full 500k experiment dataset
python -m src.catalog_analysis.seeder --config config/seeder.yaml --out data/full

# small sample (committed under data/sample/)
python -m src.catalog_analysis.seeder --records 5000 --requests 20000 \
    --seed 42 --out data/sample
```

CLI flags override the YAML: `--records`, `--requests`, `--seed`.

## Outputs

| File | Contents | Origin |
|------|----------|--------|
| `products.csv` | Catalog rows: `category_id, bucket, added_at, product_id` + payload (`name, brand, price, currency, stock, rating, attributes`) | generated |
| `access_log.csv` | Request stream `ts, request_id, op, category_id, product_id, latency_ms, success, error, run_id` | **simulated** (Zipf over categories) |
| `consistency_log.csv` | Versioned events `ts, event, key, version, consistency_level, node, network_state, success, error, run_id` | **simulated** |
| `manifest.json` | `contract_version`, `run_id`, seed, `git_sha`, effective config, `created_at` (UTC), row counts, top-category share | - |

Real benchmark logs can replace the simulated CSVs as long as they keep
the same columns; `manifest.json` `origin` records which is which
(`observed` for real runs - never re-label simulated output as observed).

Contract notes (v2):
- `success`/`error`: failed ops are recorded, not dropped - failed reads
  stay out of stale-read rates, failed writes never become committed
  versions. Datasets predating these columns are handled as `legacy`.
- `consistency.levels` accepts `ONE`, `QUORUM`, `ALL`; anything else is
  rejected at generation time, and every level needs a
  `stale_probability` entry (`failure_probability` defaults to zero).
- `run_id`: one id per run, shared by every log row and the manifest;
  use `--run-id` to set it explicitly. The seeder will not overwrite an
  existing run directory unless `--overwrite` is given.

## Guarantees

- **Reproducible** - same seed + config => byte-identical CSVs.
- **No unwanted key duplicates** - `product_id` is UUID5(seed, index);
  validation fails the run on any duplicate Schema-A/B primary key.
- **Hot-partition ready** - category assignment and request routing follow
  a Zipf distribution (`category_zipf_alpha`, `access_zipf_alpha`).
- **Bucket consistent** - `bucket = crc32(product_id) % num_buckets`,
  verified after generation.
- **Run-consistent** - every log row carries the run's `run_id`; analysis
  modules cross-check it against `manifest.json`.

The 500k output (`data/full/`) is git-ignored; only `data/sample/` is
committed.
