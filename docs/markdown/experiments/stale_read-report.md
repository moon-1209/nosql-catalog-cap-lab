# Stale Read Report

Data origin: **simulated**

Definition: a READ is stale iff `version < latest committed version` for the same key at read time. `stale_read_rate = stale_reads / valid_reads * 100%`.

- total reads: 3,046
- valid reads (decidable): 3,046
- unverifiable reads (no prior write): 0
- stale reads: 87
- **stale read rate: 2.8562%**

## By consistency level

| level | valid | stale | rate % |
|---|---|---|---|
| ONE | 1492 | 81 | 5.429 |
| QUORUM | 1554 | 6 | 0.3861 |

## By phase

| phase | valid | stale | rate % |
|---|---|---|---|
| PARTITIONED | 323 | 61 | 18.8854 |
| POST_PARTITION | 1619 | 17 | 1.05 |
| PRE_PARTITION | 1104 | 9 | 0.8152 |

Note: rates under `simulated` origin reflect the seeder's injected stale probabilities, not real ScyllaDB behaviour.