"""Loader cho products.csv (dataset chung cua team, nguon: Uyen seeder).

Dam bao E1a/E1b dung CUNG mot tap san pham that thay vi key % 10.
bucket = crc32(product_id) % 16 - giong cong thuc trong schemas.py cua Uyen.
"""
import binascii
import csv

NUM_BUCKETS = 16


def bucket_of(product_id, num_buckets=NUM_BUCKETS):
    return binascii.crc32(str(product_id).encode("utf-8")) % num_buckets


def load_products(path):
    """Doc products.csv -> list[dict] giu nguyen kieu du lieu can thiet cho CQL."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "category_id": r["category_id"],
                "bucket": int(r["bucket"]),
                "added_at": int(r["added_at"]),
                "product_id": r["product_id"],
                "name": r["name"],
                "brand": r["brand"],
                "price": float(r["price"]),
                "currency": r["currency"],
                "stock": int(r["stock"]),
                "rating": float(r["rating"]),
                "attributes": r["attributes"],
            })
    return rows


def load_workload_ops(path, limit=None):
    """Doc access_log.csv cua Uyen -> list (op, category_id, product_id).

    Chi lay op + khoa; latency/success cua file mo phong bi bo qua -
    ta do lai tren cluster that.
    """
    ops = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            op = r["op"].strip().upper()
            if op not in ("READ", "WRITE"):
                continue
            ops.append((op, r["category_id"], r["product_id"]))
            if limit and len(ops) >= limit:
                break
    return ops
