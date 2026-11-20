"""Shared catalog data model: Schema A and Schema B definitions.

These constants are the single source of truth for the two candidate
ScyllaDB table layouts compared in this lab.  Both schemas store the
same business attributes; they differ only in partition granularity.

Schema A ``products_by_category``
    PRIMARY KEY ((category_id), added_at, product_id)
    One CQL partition per category -> cheapest single-category reads,
    but a hot category concentrates load on one partition.

Schema B ``products_bucketed``
    PRIMARY KEY ((category_id, bucket), added_at, product_id)
    Each category is split into ``NUM_BUCKETS`` partitions by
    ``bucket = hash(product_id) % NUM_BUCKETS`` -> spreads the load,
    at the cost of fan-out reads across all buckets of a category.
"""

# Business attributes shared by both schemas (payload columns).
PAYLOAD_COLUMNS = [
    "name",
    "brand",
    "price",
    "currency",
    "stock",
    "rating",
    "attributes",
]

SCHEMA_A = {
    "name": "products_by_category",
    "partition_key": ("category_id",),
    "clustering_columns": ("added_at", "product_id"),
    "clustering_order": {"added_at": "DESC", "product_id": "ASC"},
}

NUM_BUCKETS = 16  # Schema B buckets per category.

SCHEMA_B = {
    "name": "products_bucketed",
    "partition_key": ("category_id", "bucket"),
    "clustering_columns": ("added_at", "product_id"),
    "clustering_order": {"added_at": "DESC", "product_id": "ASC"},
    "num_buckets": NUM_BUCKETS,
}
