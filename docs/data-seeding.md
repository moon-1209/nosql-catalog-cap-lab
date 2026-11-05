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
| `access_log.csv` | Request stream `ts, request_id, op, category_id, product_id, latency_ms` | **simulated** (Zipf over categories) |
| `consistency_log.csv` | Versioned events `ts, event, key, version, consistency_level, node, network_state` | **simulated** |
| `manifest.json` | Seed, config snapshot, row counts, top-category share | - |

Real benchmark logs can replace the simulated CSVs as long as they keep
the same columns; `manifest.json` `origin` records which is which.

## Guarantees

- **Reproducible** - same seed + config => byte-identical CSVs.
- **No unwanted key duplicates** - `product_id` is UUID5(seed, index);
  validation fails the run on any duplicate Schema-A/B primary key.
- **Hot-partition ready** - category assignment and request routing follow
  a Zipf distribution (`category_zipf_alpha`, `access_zipf_alpha`).
- **Bucket consistent** - `bucket = crc32(product_id) % num_buckets`,
  verified after generation.

The 500k output (`data/full/`) is git-ignored; only `data/sample/` is
committed.
