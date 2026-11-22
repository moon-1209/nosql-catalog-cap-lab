-- Sample queries - Schema B: products_bucketed
-- PRIMARY KEY ((category_id, bucket), added_at, product_id)
-- Each category is split into NUM_BUCKETS partitions.

-- Q1: point lookup by product id (unchanged)
SELECT * FROM products_by_id WHERE product_id = ?;

-- Q2: newest products in a category - fan-out over all buckets.
-- CQL supports IN on the last partition-key column; the application
-- merges and sorts the per-bucket pages.
SELECT product_id, name, brand, price, stock, added_at
FROM products_bucketed
WHERE category_id = ? AND bucket IN (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15)
LIMIT 20;   -- per-partition LIMIT semantics; app re-sorts by added_at

-- Q2b: same fan-out with a cursor applied to every bucket
SELECT product_id, name, brand, price, stock, added_at
FROM products_bucketed
WHERE category_id = ? AND bucket IN (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15)
  AND (added_at, product_id) < (?, ?);

-- Q3: time-window slice, again per bucket
SELECT product_id, name, price, added_at
FROM products_bucketed
WHERE category_id = ? AND bucket IN (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15)
  AND added_at >= ? AND added_at < ?;

-- Q4: brand filter still scans, now across NUM_BUCKETS partitions
SELECT product_id, name, price
FROM products_bucketed
WHERE category_id = ? AND bucket IN (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15)
  AND brand = ?
ALLOW FILTERING;

-- W1/W2: writes target exactly one bucket partition
INSERT INTO products_bucketed
  (category_id, bucket, added_at, product_id, name, brand, price, currency, stock, rating, attributes)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);

UPDATE products_bucketed SET price = ?, stock = ?
WHERE category_id = ? AND bucket = ? AND added_at = ? AND product_id = ?;
