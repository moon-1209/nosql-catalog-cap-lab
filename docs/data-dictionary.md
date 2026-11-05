# Data Dictionary

Field-level documentation for every dataset produced by
`src/catalog_analysis/seeder.py`. Types are given as (CSV storage /
CQL type). See `docs/schema/schema-design.md` for key layouts.

## 1. `products.csv` - catalog rows

One row per product; the physical row stored by both Schema A
(`products_by_category`) and Schema B (`products_bucketed`).

| Field | CSV / CQL type | Business meaning | Constraints / valid values | Key role |
|-------|----------------|------------------|----------------------------|----------|
| `category_id` | text / `text` | Product category (browse taxonomy node) | One of the 20 names in `config/seeder.yaml` | **Partition key (A & B)** |
| `bucket` | int / `smallint` | Hash bucket spreading a category across partitions | `crc32(product_id) % num_buckets`, `0..15` | **Partition key (B only)** |
| `added_at` | int64 epoch ms / `timestamp` | When the product entered the catalog | `>= 0`; clustering order DESC | **Clustering col, 1st (A & B)** |
| `product_id` | text uuid / `uuid` | Unique product identifier | UUID5(seed, row index); unique | **Clustering col, 2nd (A & B)**; PK of `products_by_id` |
| `name` | text / `text` | Display name | non-empty | payload |
| `brand` | text / `text` | Brand label | `brand-000`..`brand-199` | payload (Q4 filter) |
| `price` | decimal / `decimal` | Unit price | `5.00 <= p <= 4999.00`, 2 dp | payload |
| `currency` | text / `text` | ISO 4217 currency | `USD` | payload |
| `stock` | int / `int` | Units available | `0 <= s <= 2000` | payload |
| `rating` | float / `float` | Average customer rating | `1.0 <= r <= 5.0`, 1 dp | payload |
| `attributes` | json text / `map<text,text>` | Variant attributes (color, size) | JSON object | payload |

Primary keys: Schema A `(category_id, added_at, product_id)`; Schema B
`(category_id, bucket, added_at, product_id)`; both verified duplicate-free
by `seeder.validate()`.

## 2. `access_log.csv` - request stream (SIMULATED)

| Field | Type | Meaning | Valid values |
|-------|------|---------|--------------|
| `ts` | int64 epoch ms | Request timestamp, sorted ascending | within 30-day window |
| `request_id` | text | Unique request id | `req-%07d`, unique |
| `op` | text | Operation kind | `READ` (~90%) / `WRITE` (~10%) |
| `category_id` | text | Category routed to = Schema-A partition | 20 categories, Zipf-weighted |
| `product_id` | text uuid | Product accessed; derives `bucket` for Schema B | must exist in `products.csv` |
| `latency_ms` | float | End-to-end request latency | `> 0` (lognormal, median ~8 ms) |

## 3. `consistency_log.csv` - versioned events (SIMULATED)

| Field | Type | Meaning | Valid values |
|-------|------|---------|--------------|
| `ts` | int64 epoch ms | Event timestamp, sorted | within 30-day window |
| `event` | text | `WRITE` commits a new version; `READ` returns a committed version | `WRITE` / `READ` |
| `key` | text uuid | Product key under version control | subset of `products.product_id` |
| `version` | int | For WRITE: newly committed version; for READ: version returned | `>= 1`, monotonically increasing per key for WRITEs |
| `consistency_level` | text | CQL consistency used | `ONE` / `QUORUM` |
| `node` | text | Coordinator node | `node1`..`node5` |
| `network_state` | text | Cluster phase at `ts` | `NORMAL` / `PARTITIONED` (`node3` isolated during the window in `config/seeder.yaml`) |

A READ is **stale** iff `version < max(write.version)` over WRITEs of the
same `key` with `write.ts <= read.ts` - derived by `stale_read.py`, never
pre-labelled.

## 4. Schema notes

- `added_at` leads the clustering key so Q2 "newest first" reads are
  sequential; `product_id` trailing guarantees key uniqueness.
- `bucket` is write-computable (`crc32(product_id) % 16`): writers need no
  read to place a row in Schema B.
- `products_by_id` carries the same payload columns keyed by
  `product_id` alone; it is implied by `products.csv` (same rows).
