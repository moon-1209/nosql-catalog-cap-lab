# Access Pattern Analysis

Analysis of the query workload that the product catalog must serve, and how
each pattern interacts with the two candidate ScyllaDB schemas
(`docs/schema/`). Frequency figures are **design targets** for the
benchmark, to be validated against observed traffic.

## 1. Operation inventory

### Reads

| ID | Operation | Description |
|----|-----------|-------------|
| Q1 | Product detail lookup | Fetch one product by `product_id` |
| Q2 | Category browse (paginated) | Newest products of a category, `LIMIT` + cursor |
| Q3 | Time-window slice | Products of a category added/updated in a range |
| Q4 | In-category brand filter | Category products filtered by `brand` |

### Writes

| ID | Operation | Description |
|----|-----------|-------------|
| W1 | Product insert | New product row (+ `products_by_id` entry) |
| W2 | Price/stock update | Update `price`, `stock` on an existing product |
| W3 | Attribute update | Update `attributes` map, `rating` |

## 2. Query pattern table

| ID | Type | Target share of traffic* | Partitions touched per request (A / B) | Hot-partition risk |
|----|------|--------------------------|----------------------------------------|--------------------|
| Q1 | Read | ~35% | 1 / 1 (`products_by_id`) | Low - uniform over product ids |
| Q2 | Read | ~40% | 1 / `NUM_BUCKETS` | **High** - concentrated on popular categories |
| Q3 | Read | ~10% | 1 / `NUM_BUCKETS` | Medium - popular categories again |
| Q4 | Read | ~5% | 1 / `NUM_BUCKETS` | Medium - plus full-partition scan cost |
| W1 | Write | ~5% | 2 / 2 (lookup + catalog table) | Low - spread by product id |
| W2 | Write | ~4% | 1 / 1 | Medium - tracks category popularity |
| W3 | Write | ~1% | 1 / 1 | Medium - same as W2 |

\* Planned benchmark mix; replace with measured values once the workload
generator runs against the cluster.

## 3. Access-pattern characteristics

- **Read-heavy**: ~90% of requests are reads; category browse (Q2) dominates.
- **Skewed popularity**: in real catalogs a few categories (e.g.
  "Electronics", "Fashion") attract a large share of traffic. The seeder
  models this with a Zipf distribution over `category_id`
  (`config/seeder.yaml`, `category_zipf_alpha`).
- **Clustering-ordered reads**: Q2/Q3 exploit `CLUSTERING ORDER BY
  (added_at DESC)` - newest-first listing is a sequential read, not a sort.
- **Skew amplifies risk in Schema A**: under Schema A every Q2/Q3/Q4 hit on
  the top category lands in *one* CQL partition -> one token range -> one
  replica set. Under Zipf(α≈1) the hottest category can take >10x the mean
  partition load.

## 4. Access pattern -> partition key relationship

| Requirement | Consequence for key design |
|-------------|----------------------------|
| Q2/Q3 read newest-first inside a category | `category_id` must be in the partition key; `added_at` must lead the clustering key |
| Q2 dominates traffic and is category-skewed | Partition key must spread a category's rows -> add `bucket` column (Schema B) |
| W2 writes must reach exactly one partition | `bucket` must be derivable from `product_id` (`hash(product_id) % N`) so writers need no lookup |
| Q1 must stay O(1) | `product_id` cannot lead the catalog table key -> separate `products_by_id` lookup table |

Schema B trades **write simplicity + bounded partition size** for **read
fan-out**: every category-level read touches `NUM_BUCKETS` partitions and
the application merges results. The benchmark quantifies whether that
trade removes the hot partition.

## 5. Benchmark query set

The executable CQL for both schemas is committed next to this document:

- `queries-schema-a.cql` - single-partition reads/writes
- `queries-schema-b.cql` - bucket fan-out reads, single-bucket writes

These statements are the canonical set the benchmark harness should
prepare and parameterise; parameter markers (`?`) match the seeder output
columns in `data/sample/products.csv`.
