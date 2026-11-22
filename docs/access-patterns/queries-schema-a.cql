-- Sample queries - Schema A: products_by_category
-- PRIMARY KEY ((category_id), added_at, product_id)
-- One CQL partition per category.

-- Q1: point lookup by product id (shared lookup table, identical in A and B)
SELECT * FROM products_by_id WHERE product_id = ?;

-- Q2: newest products in a category, page 1 (single-partition read)
SELECT product_id, name, brand, price, stock
FROM products_by_category
WHERE category_id = ?
LIMIT 20;

-- Q2b: paging forward uses the last seen clustering key as cursor
SELECT product_id, name, brand, price, stock
FROM products_by_category
WHERE category_id = ?
  AND (added_at, product_id) < (?, ?)
LIMIT 20;

-- Q3: products of a category added in a time window (clustering slice)
SELECT product_id, name, price, added_at
FROM products_by_category
WHERE category_id = ?
  AND added_at >= ? AND added_at < ?;

-- Q4: browse a category filtered by brand (in-partition filter)
SELECT product_id, name, price
FROM products_by_category
WHERE category_id = ? AND brand = ?
ALLOW FILTERING;  -- brand is not part of the key: full partition scan

-- W1/W2: insert / update require the full primary key
INSERT INTO products_by_category
  (category_id, added_at, product_id, name, brand, price, currency, stock, rating, attributes)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);

UPDATE products_by_category SET price = ?, stock = ?
WHERE category_id = ? AND added_at = ? AND product_id = ?;
