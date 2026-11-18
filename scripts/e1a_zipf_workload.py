"""E1a: Zipf Workload tren ScyllaDB (Schema A)."""
import random
import math
import time
import os
from cassandra.cluster import Cluster
from cassandra.policies import AddressTranslator
from data_contract import get_run_id, get_output_dir, init_access_log, write_access_log

# Lớp này giúp dịch IP nội bộ của Docker về 127.0.0.1 để Windows kết nối được
class LocalAddressTranslator(AddressTranslator):
    def translate(self, addr):
        return '127.0.0.1'

def setup_schema(session):
    session.execute("DROP TABLE IF EXISTS catalog.product_a")
    session.execute("""
        CREATE TABLE IF NOT EXISTS catalog.product_a (
            category_id int,
            product_id int,
            name text,
            price double,
            PRIMARY KEY (category_id, product_id)
        )
    """)

def zipf_distribution(n, s, num_samples):
    weights = [1.0 / (math.pow(i, s)) for i in range(1, n + 1)]
    total = sum(weights)
    probabilities = [w / total for w in weights]
    return random.choices(range(1, n + 1), weights=probabilities, k=num_samples)

def run_experiment():
    run_id = get_run_id()
    out_dir = get_output_dir("E1a_ScyllaDB", run_id)
    access_log_file = init_access_log(out_dir)
    
    print("Connecting to ScyllaDB via 127.0.0.1...")
    cluster = Cluster(['127.0.0.1'], address_translator=LocalAddressTranslator())
    session = cluster.connect()
    
    session.execute("CREATE KEYSPACE IF NOT EXISTS catalog WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3}")
    setup_schema(session)
    
    num_keys = 1000
    skew = 1.2 
    num_ops = 1000
    
    print(f"Generating {num_ops} operations with Zipf distribution...")
    keys = zipf_distribution(num_keys, skew, num_ops)
    
    insert_stmt = session.prepare("INSERT INTO catalog.product_a (category_id, product_id, name, price) VALUES (?, ?, ?, ?)")
    select_stmt = session.prepare("SELECT * FROM catalog.product_a WHERE category_id = ? AND product_id = ?")
    
    for i, key in enumerate(keys):
        op_type = "write" if i % 2 == 0 else "read"
        category_id = key % 10
        product_id = key
        
        t0 = time.perf_counter()
        success = True
        error_msg = ""
        
        try:
            if op_type == "write":
                session.execute(insert_stmt, (category_id, product_id, f"Prod {key}", 100.0 + key))
            else:
                session.execute(select_stmt, (category_id, product_id))
        except Exception as e:
            success = False
            error_msg = str(e)
            
        latency = (time.perf_counter() - t0) * 1000
        write_access_log(access_log_file, run_id, op_type, latency, success, 
                         category_id=str(category_id), product_id=str(product_id), error=error_msg)
        
    print(f"Done! Logs saved at {out_dir}")
    cluster.shutdown()

if __name__ == "__main__":
    run_experiment()
