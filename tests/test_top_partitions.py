import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.catalog_analysis.top_partitions import partition_loads, summarise, run


def _access(rows=300):
    import numpy as np
    rng = np.random.default_rng(0)
    cats = rng.choice(["hot", "cold1", "cold2"], size=rows, p=[0.8, 0.1, 0.1])
    return pd.DataFrame({
        "ts": range(rows),
        "request_id": [f"r{i}" for i in range(rows)],
        "op": rng.choice(["READ", "WRITE"], size=rows, p=[0.9, 0.1]),
        "category_id": cats,
        "product_id": [f"p{i:05d}" for i in rng.integers(0, 500, rows)],
        "latency_ms": 10.0,
    })


class TestTopPartitions(unittest.TestCase):
    def test_schema_a_groups_by_category(self):
        loads = partition_loads(_access(), "a", 16)
        self.assertEqual(len(loads), 3)
        self.assertEqual(loads["total"].sum(), 300)
        self.assertEqual(loads.index[0], "hot")
        self.assertTrue((loads["reads"] + loads["writes"] == loads["total"]).all())

    def test_schema_b_splits_into_buckets(self):
        loads = partition_loads(_access(), "b", 16)
        self.assertGreater(len(loads), 3)  # more partitions than categories
        self.assertEqual(loads["total"].sum(), 300)

    def test_summary_metrics(self):
        s = summarise(partition_loads(_access(), "a", 16))
        self.assertEqual(s["total_requests"], 300)
        self.assertEqual(s["max_requests"], loads_max(s))
        self.assertAlmostEqual(s["mean_requests"], 100.0)
        self.assertGreater(s["max_mean_ratio"], 2.0)

    def test_run_writes_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            data = Path(d) / "data"; data.mkdir()
            _access().to_csv(data / "access_log.csv", index=False)
            (data / "manifest.json").write_text('{"origin": "simulated"}')
            out = Path(d) / "out"
            res = run(data, out, top_n=2)
            self.assertTrue((out / "partition_loads_schema_a.csv").exists())
            self.assertTrue((out / "report.md").exists())
            self.assertIn("simulated", (out / "report.md").read_text())
            self.assertEqual(len(res["schemas"]["a"]["top"]), 2)


def loads_max(s):
    return int(s["mean_requests"] * s["max_mean_ratio"])


if __name__ == "__main__":
    unittest.main()
