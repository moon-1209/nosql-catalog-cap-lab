import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.catalog_analysis.seeder import seed

CFG = {
    "seed": 7,
    "records": 2000,
    "categories": ["electronics", "fashion", "books", "toys"],
    "category_zipf_alpha": 1.2,
    "num_buckets": 16,
    "brands": 20,
    "price": {"min": 5.0, "max": 500.0},
    "stock": {"max": 500},
    "requests": 5000,
    "read_ratio": 0.9,
    "access_zipf_alpha": 1.2,
    "consistency_events": 2000,
    "consistency": {
        "levels": ["ONE", "QUORUM"],
        "hot_keys": 100,
        "nodes": ["node1", "node2", "node3"],
        "partition_node": "node3",
        "partition_start_frac": 0.4,
        "partition_duration_frac": 0.1,
        "stale_probability": {
            "ONE": {"normal": 0.05, "partitioned": 0.3, "on_partition_node": 0.6},
            "QUORUM": {"normal": 0.01, "partitioned": 0.05, "on_partition_node": 0.1},
        },
    },
}


class TestSeeder(unittest.TestCase):
    def test_deterministic_and_valid(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            m1 = seed(dict(CFG), Path(d1))
            m2 = seed(dict(CFG), Path(d2))
            self.assertEqual(
                (Path(d1) / "products.csv").read_bytes(),
                (Path(d2) / "products.csv").read_bytes(),
                "same seed must produce byte-identical products.csv",
            )
            df = pd.read_csv(Path(d1) / "products.csv")
            self.assertEqual(len(df), CFG["records"])
            self.assertFalse(df["product_id"].duplicated().any())
            self.assertTrue(df["bucket"].between(0, CFG["num_buckets"] - 1).all())
            self.assertEqual(m1["origin"], "simulated")
            self.assertEqual(m1["rows"]["products"], CFG["records"])

    def test_zipf_creates_skew(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as d:
            seed(dict(CFG), Path(d))
            df = pd.read_csv(Path(d) / "products.csv")
            shares = df["category_id"].value_counts(normalize=True)
            # Zipf a=1.2 over 4 categories: the top category must hold a
            # clearly above-uniform (>25%) share of rows.
            self.assertGreater(shares.iloc[0], 0.35)

    def test_consistency_log_has_both_events(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as d:
            seed(dict(CFG), Path(d))
            log = pd.read_csv(Path(d) / "consistency_log.csv")
            self.assertIn("WRITE", set(log["event"]))
            self.assertIn("READ", set(log["event"]))
            self.assertIn("PARTITIONED", set(log["network_state"]))
            json.loads((Path(d) / "manifest.json").read_text())


if __name__ == "__main__":
    unittest.main()
