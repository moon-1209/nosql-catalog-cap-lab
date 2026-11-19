"""E1b: Bucketing Workload tren ScyllaDB (Giu category_id)."""
import time, os, zlib, csv
from cassandra.cluster import Cluster
from cassandra.policies import AddressTranslator
from data_contract import get_run_id, get_output_dir, init_access_log, write_access_log, write_manifest

class LocalAddressTranslator(AddressTranslator):
    def translate(self, addr): return ("127.0.0.1", 9042)

def load_products():
    with open('products.csv', 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def get_bucket(key, num_buckets=16):
    return zlib.crc32(str(key).encode('utf-8')) % num_buckets

def run_experiment():
    run_id = get_run_id()
    out_dir = get_output_dir("E1b_ScyllaDB", run_id)
    access_log = init_access_log(out_dir)
    write_manifest(out_dir, run_id, "E1b_Bucketing", {"dataset": "products.csv", "buckets": 16})
    
    cluster = Cluster(['127.0.0.1'], address_translator=LocalAddressTranslator())
    session = cluster.connect()
    session.execute("CREATE KEYSPACE IF NOT EXISTS catalog WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3}")
    session.execute("DROP TABLE IF EXISTS catalog.product_b")
    # Schema B moi: Partition key gom (bucket_id, category_id) de giu chieu category
    session.execute("CREATE TABLE IF NOT EXISTS catalog.product_b (bucket_id int, category_id int, product_id int, name text, price double, PRIMARY KEY ((bucket_id, category_id), product_id))")
    
    products = load_products()
    insert_stmt = session.prepare("INSERT INTO catalog.product_b (bucket_id, category_id, product_id, name, price) VALUES (?, ?, ?, ?, ?)")
    select_stmt = session.prepare("SELECT * FROM catalog.product_b WHERE bucket_id = ? AND category_id = ? AND product_id = ?")
    
    for i in range(1, 1001): # Gia lap 1000 ops
        p = products[i % len(products)]
        op_type = "WRITE" if i % 2 == 0 else "READ"
        cat_id, prod_id = int(p['category_id']), int(p['product_id'])
        bucket_id = get_bucket(prod_id)
        
        t0 = time.perf_counter()
        success, error_msg = True, ""
        try:
            if op_type == "WRITE":
                session.execute(insert_stmt, (bucket_id, cat_id, prod_id, p['name'], float(p['price'])))
            else:
                session.execute(select_stmt, (bucket_id, cat_id, prod_id))
        except Exception as e:
            success = False; error_msg = str(e)
            
        latency = (time.perf_counter() - t0) * 1000
        write_access_log(access_log, run_id, op_type, latency, success, category_id=str(cat_id), product_id=str(prod_id), error=error_msg)
        
    print(f"Done! Logs saved at {out_dir}")
    cluster.shutdown()

if __name__ == "__main__":
    run_experiment()
