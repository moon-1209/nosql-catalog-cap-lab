# Stale Read Report

Data origin: **synthetic**
run_id: `20261120054801_0bdd8fba` (log/manifest consistency: ok)
status mode: ok

Definition: a READ is stale iff `version < latest committed version` for the same key at read time. `stale_read_rate = stale_reads / valid_reads * 100%`. Failed reads/writes are excluded from both numerator and denominator and reported separately.

- total reads: 3 (2 successful, 1 failed)
- valid reads (decidable): 2
- unverifiable reads (no prior write): 0
- stale reads: 1
- **stale read rate: 50.0%**

## By consistency level

| level | valid | stale | rate % |
|---|---|---|---|
| ONE | 2 | 1 | 50.0 |

## By phase

| phase | valid | stale | rate % |
|---|---|---|---|
| PRE_PARTITION | 2 | 1 | 50.0 |

## Failed operations (excluded from stale rates)

| kind | count |
|---|---|
| failed reads | 1 |
| failed writes | 0 |

- ALL: 1 failed ops

Note: rates under `simulated` origin reflect the seeder's injected stale probabilities, not real ScyllaDB behaviour.