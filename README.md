# nosql-catalog-cap-lab

Research lab on NoSQL (ScyllaDB), the CAP theorem, data partitioning,
consistency levels and hot partitions for a product-catalog workload.

## Repository layout

| Path | Contents |
|---|---|
| `docs/` | Access patterns, Chebotko schema diagrams, data dictionary, final report |
| `src/catalog_analysis/` | Seeder and analysis modules (hot partition, stale read, bootstrap CI) |
| `notebooks/` | Analysis preparation notebook |
| `config/` | Seeder / analysis configuration |
| `data/sample/` | Small committed sample datasets |
| `results/` | Analysis outputs (tables, figures) |
| `tests/` | Unit tests |

## Quick start

```bash
pip install -r requirements.txt
python -m src.catalog_analysis.seeder --records 5000 --requests 20000 --out data/sample
python -m unittest discover -s tests -v
```

Analysis features are implemented on branch `feat/uyen-analysis-pipeline`.
