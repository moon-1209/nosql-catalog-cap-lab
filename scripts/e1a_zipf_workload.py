"""E1a: workload that tren ScyllaDB - Schema A (products_by_category).

PRIMARY KEY ((category_id), added_at, product_id) - 1 partition / category.

Khac ban cu:
  * Dung products.csv + access_log.csv cua Uyen lam input (cung dataset voi E1b
    -> so sanh duoc). Khong con key % 10.
  * Log theo Data Contract v2: op READ/WRITE (uppercase), ts epoch ms,
    manifest.json day du provenance.

Chay: python scripts/e1a_zipf_workload.py [--limit N]
Can cluster ScyllaDB (docker/scylla.yml hoac compose/ cua Lam).
"""
import os
import sys
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_contract import (
    get_run_id, get_output_dir, init_access_log, write_access_log,
    new_manifest, finalize_manifest,
)
from product_catalog import load_products, load_workload_ops

from lab_connect import connect, ensure_keyspace


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--products", default="data/sample/products.csv")
    ap.add_argument("--ops", default="data/sample/access_log.csv")
    ap.add_argument("--limit", type=int, default=2000)
    ap.add_argument("--keyspace", default="catalog")
    args = ap.parse_args()

    run_id = get_run_id()
    out_dir = get_output_dir("E1a_ScyllaDB", run_id)
    access_log_file = init_access_log(out_dir)
    manifest = new_manifest(run_id, "E1a", "hot_partition_schema_a", config={
        "keyspace": args.keyspace, "schema": "products_by_category",
        "products": args.products, "workload": args.ops, "limit": args.limit,
    })

    products = load_products(args.products)
    by_pid = {p["product_id"]: p for p in products}
    ops = load_workload_ops(args.ops, limit=args.limit)
    print(f"Loaded {len(products)} products, replaying {len(ops)} ops")

    cluster, session = connect()
    ensure_keyspace(session, args.keyspace)
    session.execute("""
        CREATE TABLE IF NOT EXISTS products_by_category (
            category_id text, added_at bigint, product_id text,
            name text, brand text, price double, currency text,
            stock int, rating double, attributes text,
            PRIMARY KEY ((category_id), added_at, product_id)
        )""")

    insert_stmt = session.prepare(
        "INSERT INTO products_by_category (category_id, added_at, product_id, "
        "name, brand, price, currency, stock, rating, attributes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
    read_stmt = session.prepare(
        "SELECT product_id FROM products_by_category "
        "WHERE category_id = ? AND added_at = ? AND product_id = ?")

    print("Seeding products ...")
    for p in products:
        session.execute(insert_stmt, tuple(p[k] for k in (
            "category_id", "added_at", "product_id", "name", "brand",
            "price", "currency", "stock", "rating", "attributes")))

    op_count = 0
    for op, category_id, product_id in ops:
        p = by_pid.get(product_id)
        if p is None or p["category_id"] != category_id:
            continue
        t0 = time.perf_counter()
        success, error_msg = True, ""
        try:
            if op == "WRITE":
                session.execute(insert_stmt, tuple(p[k] for k in (
                    "category_id", "added_at", "product_id", "name", "brand",
                    "price", "currency", "stock", "rating", "attributes")))
            else:
                session.execute(read_stmt,
                                (category_id, p["added_at"], product_id))
        except Exception as e:
            success, error_msg = False, str(e)[:120]
        latency = (time.perf_counter() - t0) * 1000
        write_access_log(access_log_file, run_id, op, latency, success,
                         category_id=category_id, product_id=product_id,
                         error=error_msg)
        op_count += 1

    finalize_manifest(out_dir, manifest, op_count=op_count)
    print(f"Done! {op_count} ops -> {out_dir}")
    cluster.shutdown()


if __name__ == "__main__":
    main()
