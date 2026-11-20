---
marp: true
theme: default
paginate: true
title: NoSQL Catalog CAP Lab - Final Report
---

# NoSQL Catalog CAP Lab
### Hot partitions, consistency levels & CAP on a product catalog
Uyen - analysis pipeline

---

# Problem & goals

- Catalog browse traffic is **Zipf-skewed** over categories
- Q: does per-category partitioning create hot partitions?
- Q: what does a network partition do to read freshness at each CL?
- Metrics: top-partition load, stale-read rate, latency + 95% bootstrap CI

---

# Schema A vs Schema B

| | Schema A | Schema B |
|---|---|---|
| table | `products_by_category` | `products_bucketed` |
| partition key | `(category_id)` | `(category_id, bucket)` |
| partitions/category | 1 | 16 |
| category read | 1 partition | 16-way fan-out + merge |

Chebotko diagrams: `docs/schema/chebotko/`

---

# Access patterns

- ~90% reads / ~10% writes
- Q2 "browse category, newest first" ~ 40% of traffic = hot path
- Q2/Q3 ride `CLUSTERING ORDER BY (added_at DESC)`
- Q1 point lookup served by `products_by_id` in both schemas

---

# Data & method

- Seeder: 500k products, Zipf a=1.2, seed 42, byte-reproducible
- Simulated access + consistency logs (clearly labelled `SIMULATED`)
- Node partition injected on node3 for 10% of the window
- Stale read = returned version < latest committed version

---

# Hot partitions (SIMULATED sample)

- Schema A: top partition takes **35.4%** of all traffic (5,313 req)
- Schema B: top partition takes **3.0%** (445 req) -> ~12x lower peak
- Max/mean can mislead; absolute peak + top share tell the story

figures: `results/figures/hot_partition_*.png`

---

# Stale reads (SIMULATED sample)

| CL | stale rate |
|---|---|
| ONE | 5.43% |
| QUORUM | 0.39% |

- During partition window: ONE spikes to ~30-40% on the isolated node
- QUORUM stays near zero (minority side cannot serve)

---

# Consistency timeline

`results/figures/consistency_heatmap.png` + `consistency_timeline.png`

- violations cluster strictly inside the disruption window
- CAP in action: availability kept, consistency traded away at CL=ONE

---

# Bootstrap 95% CI (SIMULATED)

- mean latency 9.02 ms [8.95 - 9.10] (moving-block, t-dependent data)
- stale rate ONE 5.43% [4.29 - 6.57]; QUORUM 0.39% [0.13 - 0.71]
- top-partition share A: 0.354 [0.346 - 0.362]
- CI = sampling uncertainty, not causal proof

---

# Evaluation & conclusion

- **Schema B wins** on bounded partition load; A wins on read simplicity
- CL choice is a freshness/availability dial - CAP is visible live
- **Pending**: real ScyllaDB cluster benchmark to validate all numbers

---

# Limitations

- All reported numbers are simulated, not measured
- No bucket-count sweep, single partition scenario, no read repair
- Real-cluster runs are planned next milestone
