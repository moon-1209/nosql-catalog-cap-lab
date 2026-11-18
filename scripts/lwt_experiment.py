"""LWT: Lightweight Transactions tren ScyllaDB."""
import time
import concurrent.futures
from cassandra.cluster import Cluster
from cassandra.policies import AddressTranslator
from cassandra import ConsistencyLevel
from data_contract import get_run_id, get_output_dir, init_access_log, write_access_log

class LocalAddressTranslator(AddressTranslator):
    def translate(self, addr): return '127.0.0.1'

def run_experiment():
    run_id = get_run_id()
    out_dir = get_output_dir("LWT", run_id)
    access_log = init_access_log(out_dir)

    cluster = Cluster(['127.0.0.1'], address_translator=LocalAddressTranslator())
    session = cluster.connect()
    session.execute("CREATE KEYSPACE IF NOT EXISTS catalog WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3}")
    session.execute("DROP TABLE IF EXISTS catalog.lwt_test")
    session.execute("CREATE TABLE IF NOT EXISTS catalog.lwt_test (id int PRIMARY KEY, owner text)")

    session.execute("INSERT INTO catalog.lwt_test (id, owner) VALUES (1, 'Nobody')", timeout=10.0)

    def try_buy(ticket):
        stmt = session.prepare("UPDATE catalog.lwt_test SET owner = ? WHERE id = 1 IF owner = 'Nobody'")
        stmt.consistency_level = ConsistencyLevel.QUORUM
        
        t0 = time.perf_counter()
        success = False
        err_msg = ""
        try:
            result = session.execute(stmt, (f'User_{ticket}',))
            if result.was_applied:
                success = True
        except Exception as e:
            err_msg = str(e)[:50]
            
        lat = (time.perf_counter() - t0) * 1000
        write_access_log(access_log, run_id, "lwt_buy", lat, success, product_id="1", error=err_msg)
        return success

    print("Bat dau 50 luong tranh mua 1 mon hang bang LWT...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(try_buy, range(1, 51)))
        
    print(f"Tong so luong: 50. Mua thanh cong: {sum(results)} (Chi duoc phep la 1)")
    print(f"Logs saved at {out_dir}")
    cluster.shutdown()

if __name__ == "__main__":
    run_experiment()
