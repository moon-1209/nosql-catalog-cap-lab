"""E1a: Zipf Workload tren ScyllaDB (Dung products.csv)."""
import random, math, time, os, csv
from cassandra.cluster import Cluster
from cassandra.policies import AddressTranslator
from data_contract import get_run_id, get_output_dir, init_access_log, write_access_log, write_manifest

class LocalAddressTranslator(AddressTranslator):
    def translate(self, addr): return '127.0.0.1'

def load_products():
    products = []
    with open('products.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(row)
    return products

def zipf_distribution(n, s, num_samples):
    weights = [1.0 / (math.pow(i, s)) for i in range(1, n + 1)]
    total = sum(weights)
    probabilities = [w / total for w in weights]
    return random.choices(range(n), weights=probabilities, k=num_samples)

def run_experiment():
    run_id = get_run_id()
    out_dir = get_output_dir("E1a_ScyllaDB", run_id)
    access_log = init_access_log(out_dir)
    write_manifest(out_dir, run_id, "E1a_Zipf", {"dataset": "products.csv", "num_ops": 1000})
    
    cluster = Cluster(['127.0.0.1'], address_translator=LocalAddressTranslator())
    session = cluster.connect()
    session.execute("CREATE KEYSPACE IF NOT EXISTS catalog WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3}")
    session.execute("DROP TABLE IF EXISTS catalog.product_a")
    session.execute("CREATE TABLE IF NOT EXISTS catalog.product_a (category_id int, product_id int, name text, price double, PRIMARY KEY (category_id, product_id))")
    
    products = load_products()
    keys = zipf_distribution(len(products), 1.2, 1000)
    
    insert_stmt = session.prepare("INSERT INTO catalog.product_a (category_id, product_id, name, price) VALUES (?, ?, ?, ?)")
    select_stmt = session.prepare("SELECT * FROM catalog.product_a WHERE category_id = ? AND product_id = ?")
    
    for i, idx in enumerate(keys):
        p = products[idx]
        op_type = "WRITE" if i % 2 == 0 else "READ"
        cat_id, prod_id = int(p['category_id']), int(p['product_id'])
        
        t0 = time.perf_counter()
        success = True
        error_msg = ""
        try:
            if op_type == "WRITE":
                session.execute(insert_stmt, (cat_id, prod_id, p['name'], float(p['price'])))
            else:
                session.execute(select_stmt, (cat_id, prod_id))
        except Exception as e:
            success = False; error_msg = str(e)
            
        latency = (time.perf_counter() - t0) * 1000
        write_access_log(access_log, run_id, op_type, latency, success, category_id=str(cat_id), product_id=str(prod_id), error=error_msg)
        
    print(f"Done! Logs saved at {out_dir}")
    cluster.shutdown()

if __name__ == "__main__":
    run_experiment()
