# Final Report - NoSQL Catalog CAP Lab

**Status legend:** `SIMULATED` = produced by the seeded synthetic workload
in this repository; `PENDING` = requires the real ScyllaDB cluster
benchmark (owned by the infra/benchmark track) - not yet run.

## 1. Problem

A product catalog must serve category-browse traffic on ScyllaDB.
Category popularity is Zipf-skewed, so naive per-category partitioning
risks hot partitions; at the same time a network partition probes the
consistency/availability trade-off predicted by CAP.

## 2. Research goals

1. Quantify hot-partition exposure of per-category partitioning
   (Schema A) vs bucketed partitioning (Schema B).
2. Measure stale-read rates at CL=ONE vs CL=QUORUM, in normal operation
   and during a node network partition.
3. Attach 95% bootstrap confidence intervals to the benchmark metrics.

## 3. Schema design

Chebotko diagrams: `docs/schema/chebotko/schema-a.svg`, `schema-b.svg`;
comparison: `docs/schema/schema-design.md`.

- **Schema A** `products_by_category`: PK `((category_id), added_at,
  product_id)` - one partition per category.
- **Schema B** `products_bucketed`: PK `((category_id, bucket),
  added_at, product_id)`, `bucket = crc32(product_id) % 16` - each
  category spread over 16 partitions; category reads fan out.

## 4. Access patterns

`docs/access-patterns/access-patterns.md`. ~90% reads; category browse
(Q2) ~40% of traffic is the hot-path driving the key design.

## 5. Data generation

`src/catalog_analysis/seeder.py` + `config/seeder.yaml`: 500k products
(configurable), UUID5 keys, Zipf(a=1.2) category skew, seeded and
byte-reproducible; emits simulated `access_log` and `consistency_log`.

## 6. Environment

- Lab cluster (3+ node ScyllaDB): **PENDING** - infra track.
- Analysis pipeline: Python 3.14, `requirements.txt`; runs fully on
  committed `data/sample/` (5k rows) for CI/regeneration.

## 7. Benchmark method

1. Seed `data/full/` (500k rows, seed 42).
2. Replay `access_log` against both schemas (or analyse the request
   stream directly for partition-load metrics, as done here).
3. Inject node3 network partition for 10% of the window.
4. Record per-partition load, latency, read staleness.

## 8. Hot-partition results (`SIMULATED` sample, 15k requests)

| Metric | Schema A | Schema B |
|---|---|---|
| partitions | 20 | 318 |
| max partition load | 5,313 req | 445 req |
| top-partition traffic share | **35.4%** | **3.0%** |
| mean load | 750 | 47.2 |
| max/mean ratio | 7.08 | 9.43 |

Figures: `results/figures/hot_partition_*.png`.

Reading: bucketing cuts the hottest partition's absolute load ~12x.
Max/mean alone is misleading - Schema B's mean is small because many
buckets are cold; the operational risk (peak partition load, top share)
is what drops. Real-cluster numbers: **PENDING**.

## 9. Stale-read results (`SIMULATED` sample, 3,046 reads)

| CL | valid reads | stale | rate |
|---|---|---|---|
| ONE | 1,492 | 81 | **5.43%** |
| QUORUM | 1,554 | 6 | **0.39%** |

During the partition window the ONE rate spikes (rolling window ~30-40%
on the isolated node); QUORUM rises slightly. See
`results/figures/consistency_heatmap.png`, `consistency_timeline.png`.
Real-cluster numbers: **PENDING**.

## 10. Consistency under network partition

Heatmap shows violations concentrate inside the disruption window,
heaviest on the partitioned node at CL=ONE - matching CAP: the
minority side keeps serving (A) at the cost of staleness (C).
Definition and rates: `src/catalog_analysis/stale_read.py`,
`results/stale_read/report.md`.

## 11. Bootstrap CI 95% (`SIMULATED` sample)

| Metric | Estimate | 95% CI | Method |
|---|---|---|---|
| mean latency | 9.02 ms | [8.95, 9.10] | moving-block (t-dependence) |
| p95 latency | 18.27 ms | [17.99, 18.60] | iid |
| top-partition share (A) | 0.354 | [0.346, 0.362] | iid over requests |
| stale rate ONE | 5.43% | [4.29, 6.57] | iid |
| stale rate QUORUM | 0.39% | [0.13, 0.71] | iid |

CIs quantify sampling uncertainty only - not causal proof. Method:
`src/catalog_analysis/bootstrap_ci.py`.

## 12. Schema evaluation

| Criterion | Winner | Evidence |
|---|---|---|
| Peak partition load | **B** | 445 vs 5,313 req (SIMULATED) |
| Category-read cost | **A** | 1 partition vs 16-way fan-out |
| Write cost | tie | single partition write both ways |
| Tail latency under skew | **B** (expected) | bounded partition size |
| Implementation complexity | **A** | no merge logic |

Recommendation: Schema B where category skew is real and category
browses dominate; keep `products_by_id` for point reads in both.

## 13. Conclusions & limitations

- Bucketing is effective at bounding per-partition load under Zipf
  traffic (simulated evidence; cluster validation pending).
- CL=ONE trades freshness for availability during partitions; QUORUM
  bounds staleness at the cost of minority-side unavailability.
- **Limitations**: all numbers above are simulated - the injected stale
  probabilities and lognormal latencies are assumptions, not
  measurements; bucket count (16) was not swept; single partition
  window only; no repair/read-repair modelling.

## Reproduce

```bash
pip install -r requirements.txt
python -m src.catalog_analysis.seeder --out data/full          # 500k
python -m src.catalog_analysis.top_partitions --data data/full
python -m src.catalog_analysis.hot_partition_charts --data data/full
python -m src.catalog_analysis.stale_read --data data/full
python -m src.catalog_analysis.consistency_viz --data data/full
python -m src.catalog_analysis.bootstrap_ci --data data/full
```
