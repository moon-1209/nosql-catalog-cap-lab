import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.catalog_analysis.stale_read import classify_reads, analyse


def _log(rows):
    return pd.DataFrame(
        rows, columns=["ts", "event", "key", "version",
                       "consistency_level", "node", "network_state"])


BASE = [
    (1, "WRITE", "k1", 1, "ONE", "n1", "NORMAL"),
    (2, "WRITE", "k1", 2, "ONE", "n1", "NORMAL"),
    (3, "READ", "k1", 2, "ONE", "n1", "NORMAL"),    # fresh
    (4, "READ", "k1", 1, "ONE", "n1", "NORMAL"),    # stale (v1 < v2)
    (5, "READ", "k2", 1, "ONE", "n1", "NORMAL"),    # unverifiable
    (6, "WRITE", "k2", 1, "QUORUM", "n2", "PARTITIONED"),
    (7, "READ", "k2", 1, "QUORUM", "n3", "PARTITIONED"),  # fresh
]


class TestStaleRead(unittest.TestCase):
    def test_stale_classification(self):
        reads = classify_reads(_log(BASE)).set_index("ts")
        self.assertFalse(bool(reads.loc[3, "is_stale"]))
        self.assertTrue(bool(reads.loc[4, "is_stale"]))
        self.assertFalse(bool(reads.loc[5, "valid"]))   # no prior write
        self.assertFalse(bool(reads.loc[7, "is_stale"]))

    def test_rate_excludes_unverifiable(self):
        result, _ = analyse(_log(BASE))
        self.assertEqual(result["total_reads"], 4)
        self.assertEqual(result["overall"]["valid_reads"], 3)
        self.assertEqual(result["overall"]["stale_reads"], 1)
        self.assertAlmostEqual(result["overall"]["stale_read_rate_pct"],
                               100 / 3, places=3)

    def test_zero_valid_reads(self):
        log = _log([(1, "READ", "kx", 1, "ONE", "n1", "NORMAL")])
        result, _ = analyse(log)
        self.assertEqual(result["overall"]["valid_reads"], 0)
        self.assertIsNone(result["overall"]["stale_read_rate_pct"])

    def test_empty_log(self):
        result, _ = analyse(_log([]).astype({"ts": "int64"}))
        self.assertEqual(result["total_reads"], 0)
        self.assertIsNone(result["overall"]["stale_read_rate_pct"])

    def test_phase_labels(self):
        reads = classify_reads(_log(BASE)).set_index("ts")
        self.assertEqual(reads.loc[3, "phase"], "PRE_PARTITION")
        self.assertEqual(reads.loc[7, "phase"], "PARTITIONED")


if __name__ == "__main__":
    unittest.main()
