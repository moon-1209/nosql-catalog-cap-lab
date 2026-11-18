"""Counter: Native Counter tren ScyllaDB."""
import time
import concurrent.futures
from cassandra.cluster import Cluster
from cassandra.policies import AddressTranslator
from data_contract import get_run_id, get_output_dir, init_access_log, write_access_log

class LocalAddressTranslator(AddressTranslator):
    def translate(self, addr): return '127.0.0.1'

def run_experiment():
    run_id = get_run_id()
    out_dir = get_output_dir("Counter", run_id)
    access_log = init_access_log(out_dir)

    cluster = Cluster(['127.0.0.1'], address_translator=LocalAddressTranslator())
    session = cluster.connect()
    session.execute("CREATE KEYSPACE IF NOT EXISTS catalog WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3}")
    session.execute("DROP TABLE IF EXISTS catalog.counter_test")
    session.execute("CREATE TABLE IF NOT EXISTS catalog.counter_test (id int PRIMARY KEY, views counter)")
    
    session.execute("UPDATE catalog.counter_test SET views = views + 0 WHERE id = 1")

    def increment(ticket):
        stmt = session.prepare("UPDATE catalog.counter_test SET views = views + 1 WHERE id = 1")
        t0 = time.perf_counter()
        success = True
        err_msg = ""
        try:
            session.execute(stmt, timeout=10.0)
        except Exception as e:
            success = False
            err_msg = str(e)[:50]
            
        lat = (time.perf_counter() - t0) * 1000
        write_access_log(access_log, run_id, "counter_inc", lat, success, product_id="1", error=err_msg)

    print("Bat dau 100 luong tang bien dem dong thoi...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        list(executor.map(increment, range(1, 101)))
        
    final_val = session.execute("SELECT views FROM catalog.counter_test WHERE id = 1").one()[0]
    print(f"Tong so lan tang: 100. Gia tri Counter cuoi cung: {final_val} (Phai bang 100)")
    print(f"Logs saved at {out_dir}")
    cluster.shutdown()

if __name__ == "__main__":
    run_experiment()
