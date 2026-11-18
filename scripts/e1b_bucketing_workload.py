"""E1b: Bucketing Workload tren ScyllaDB (Schema B) với CRC32."""
import time
import os
import zlib
from cassandra.cluster import Cluster
from cassandra.policies import AddressTranslator
from data_contract import get_run_id, get_output_dir, init_access_log, write_access_log

class LocalAddressTranslator(AddressTranslator):
    def translate(self, addr):
        return '127.0.0.1'

def setup_schema(session):
    # Xoa bang cu neu co
    session.execute("DROP TABLE IF EXISTS catalog.product_b")
    # Schema B: Partition key la bucket_id, Clustering key la product_id
    session.execute("""
        CREATE TABLE IF NOT EXISTS catalog.product_b (
            bucket_id int,
            product_id int,
            name text,
            price double,
            PRIMARY KEY (bucket_id, product_id)
        )
    """)

def get_bucket(key, num_buckets=16):
    """Băm key bằng CRC32 và map vào đúng 16 bucket (0-15)."""
    crc = zlib.crc32(str(key).encode('utf-8'))
    return crc % num_buckets

def run_experiment():
    run_id = get_run_id()
    out_dir = get_output_dir("E1b_ScyllaDB", run_id)
    access_log_file = init_access_log(out_dir)
    
    print("Connecting to ScyllaDB via 127.0.0.1...")
    cluster = Cluster(['127.0.0.1'], address_translator=LocalAddressTranslator())
    session = cluster.connect()
    
    session.execute("CREATE KEYSPACE IF NOT EXISTS catalog WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3}")
    setup_schema(session)
    
    num_ops = 1000
    print(f"Generating {num_ops} operations with CRC32 Bucketing...")
    
    insert_stmt = session.prepare("INSERT INTO catalog.product_b (bucket_id, product_id, name, price) VALUES (?, ?, ?, ?)")
    select_stmt = session.prepare("SELECT * FROM catalog.product_b WHERE bucket_id = ? AND product_id = ?")
    
    for i in range(1, num_ops + 1):
        op_type = "write" if i % 2 == 0 else "read"
        product_id = i
        bucket_id = get_bucket(product_id) # Dung CRC32
        
        t0 = time.perf_counter()
        success = True
        error_msg = ""
        
        try:
            if op_type == "write":
                session.execute(insert_stmt, (bucket_id, product_id, f"Item {product_id}", 50.0 + product_id))
            else:
                session.execute(select_stmt, (bucket_id, product_id))
        except Exception as e:
            success = False
            error_msg = str(e)
            
        latency = (time.perf_counter() - t0) * 1000
        write_access_log(access_log_file, run_id, op_type, latency, success, 
                         category_id="", product_id=str(product_id), error=error_msg)
        
    print(f"Done! Logs saved at {out_dir}")
    print(f"Bucket check (should only be 0-15): unique buckets = {set(get_bucket(i) for i in range(1, num_ops+1))}")
    cluster.shutdown()

if __name__ == "__main__":
    run_experiment()
