import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.catalog_analysis.contracts import (
    VALID_CONSISTENCY_LEVELS, normalize_success, run_info)
from src.catalog_analysis.seeder import seed
from src.catalog_analysis.stale_read import analyse, classify_reads
from src.catalog_analysis.top_partitions import partition_loads

COLS = ["ts", "event", "key", "version", "consistency_level", "node",
        "network_state", "success", "error", "run_id"]


def _log(rows):
    return pd.DataFrame(rows, columns=COLS)


BASE = [
    (1, "WRITE", "k1", 1, "ONE", "n1", "NORMAL", True, "", "r1"),
    (2, "WRITE", "k1", 2, "ONE", "n1", "NORMAL", True, "", "r1"),
    (3, "READ", "k1", 2, "ONE", "n1", "NORMAL", True, "", "r1"),   # fresh
    (4, "READ", "k1", 1, "ONE", "n1", "NORMAL", True, "", "r1"),   # stale
    (5, "WRITE", "k1", None, "ONE", "n1", "PARTITIONED", False, "unavailable", "r1"),
    (6, "READ", "k1", None, "ONE", "n1", "PARTITIONED", False, "unavailable", "r1"),
]


class TestFailedOps(unittest.TestCase):
    def test_successful_read(self):
        reads = classify_reads(_log(BASE)).set_index("ts")
        self.assertFalse(bool(reads.loc[3, "is_stale"]))
        self.assertTrue(bool(reads.loc[4, "is_stale"]))

    def test_failed_read_excluded(self):
        reads = classify_reads(_log(BASE))
        self.assertNotIn(6, reads["ts"].tolist())

    def test_failed_write_not_committed(self):
        rows = BASE + [(7, "READ", "k1", 2, "ONE", "n1",
                        "PARTITIONED", True, "", "r1")]
        reads = classify_reads(_log(rows)).set_index("ts")
        # latest committed is still v2 (the failed write at ts=5 must not
        # become v3) -> read returning 2 at ts=7 is fresh
        self.assertEqual(int(reads.loc[7, "latest_committed"]), 2)
        self.assertFalse(bool(reads.loc[7, "is_stale"]))

    def test_missing_status_is_legacy_not_silent_success(self):
        legacy = _log(BASE).drop(columns=["success"])
        _, meta = normalize_success(legacy)
        self.assertEqual(meta["status_mode"], "legacy")

    def test_invalid_status_not_success_not_failure(self):
        df = _log(BASE)
        df["success"] = df["success"].astype(object)
        df.loc[0, "success"] = "banana"
        out, meta = normalize_success(df)
        self.assertEqual(meta["unknown_status"], 1)
        self.assertTrue(pd.isna(out["success"].iloc[0]))

    def test_zero_successful_reads(self):
        rows = [(t, e, k, v, l, n, s, False, "unavailable", "r1")
                for (t, e, k, v, l, n, s, *_x) in BASE]
        res, _ = analyse(_log(rows))
        self.assertIsNone(res["overall"]["stale_read_rate_pct"])
        self.assertEqual(res["overall"]["valid_reads"], 0)

    def test_all_reads_failed(self):
        rows = [r for r in BASE if r[1] == "WRITE"]
        res, _ = analyse(_log(rows))
        self.assertEqual(res["overall"]["reads"], 0)

    def test_failure_stats_independent(self):
        res, _ = analyse(_log(BASE))
        self.assertEqual(res["failures"]["failed_reads"], 1)
        self.assertEqual(res["failures"]["failed_writes"], 1)
        self.assertEqual(res["failures"]["by_consistency_level"]["ONE"], 2)

    def test_partition_failures_counted(self):
        df = pd.DataFrame({
            "ts": [1, 2, 3],
            "request_id": ["a", "b", "c"],
            "op": ["READ", "READ", "READ"],
            "category_id": ["hot", "hot", "hot"],
            "product_id": ["p1", "p2", "p3"],
            "latency_ms": [1.0, 1.0, 1.0],
            "success": [True, True, False],
        })
        df, _ = normalize_success(df)
        loads = partition_loads(df, "a", 16)
        self.assertEqual(int(loads.loc["hot", "total"]), 3)   # attempted
        self.assertEqual(int(loads.loc["hot", "failures"]), 1)


class TestConsistencyLevels(unittest.TestCase):
    def _cfg(self, **kw):
        c = yaml.safe_load(Path("config/seeder.yaml").read_text())
        c["records"], c["requests"], c["consistency_events"] = 500, 500, 400
        c["consistency"]["hot_keys"] = 50
        c.update(kw)
        return c

    def test_all_three_levels_accepted(self):
        cfg = self._cfg()
        self.assertEqual(set(cfg["consistency"]["levels"]),
                         {"ONE", "QUORUM", "ALL"})
        with tempfile.TemporaryDirectory() as d:
            seed(cfg, Path(d), run_id="t")
            log = pd.read_csv(Path(d) / "consistency_log.csv")
            self.assertIn("ALL", set(log["consistency_level"]))

    def test_invalid_level_rejected(self):
        cfg = self._cfg()
        cfg["consistency"]["levels"] = ["ONE", "TWO"]
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                seed(cfg, Path(d))

    def test_stale_prob_missing_level_rejected(self):
        cfg = self._cfg()
        cfg["consistency"]["levels"] = ["ONE", "QUORUM", "ALL"]
        del cfg["consistency"]["stale_probability"]["ALL"]
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                seed(cfg, Path(d))

    def test_all_failures_not_stale(self):
        cfg = self._cfg()
        with tempfile.TemporaryDirectory() as d:
            seed(cfg, Path(d), run_id="t")
            log = pd.read_csv(Path(d) / "consistency_log.csv")
            res, _ = analyse(log)
            # ALL never returns stale versions in this model
            self.assertEqual(
                res["by_consistency_level"]["ALL"]["stale_reads"], 0)

    def test_all_healthy_vs_partitioned_state(self):
        # Regression: ALL must succeed in the healthy state and only fail
        # under partition conditions - never unconditionally.
        cfg = self._cfg()
        with tempfile.TemporaryDirectory() as d:
            seed(cfg, Path(d), run_id="t")
            log = pd.read_csv(Path(d) / "consistency_log.csv")
            a = log[log.consistency_level == "ALL"]
            normal = a[a.network_state == "NORMAL"]
            part = a[a.network_state == "PARTITIONED"]
            self.assertGreater((normal.success == True).mean(), 0.9)
            self.assertGreater((part.success == False).mean(), 0.3)
            self.assertLess((part.success == False).mean(), 1.0)


class TestRunProvenance(unittest.TestCase):
    def test_run_id_shared_and_manifest_fields(self):
        cfg = yaml.safe_load(Path("config/seeder.yaml").read_text())
        cfg["records"], cfg["requests"], cfg["consistency_events"] = 300, 300, 200
        cfg["consistency"]["hot_keys"] = 30
        with tempfile.TemporaryDirectory() as d:
            m = seed(cfg, Path(d), run_id="run-xyz")
            for k in ("run_id", "seed", "origin", "git_sha", "config",
                      "created_at"):
                self.assertIn(k, m)
            self.assertEqual(m["run_id"], "run-xyz")
            for f in ("access_log.csv", "consistency_log.csv"):
                df = pd.read_csv(Path(d) / f)
                self.assertTrue((df["run_id"] == "run-xyz").all())
                self.assertEqual(run_info(Path(d), df)["consistency"], "ok")

    def test_overwrite_guard(self):
        cfg = yaml.safe_load(Path("config/seeder.yaml").read_text())
        cfg["records"], cfg["requests"], cfg["consistency_events"] = 100, 100, 100
        cfg["consistency"]["hot_keys"] = 10
        with tempfile.TemporaryDirectory() as d:
            seed(cfg, Path(d))
            with self.assertRaises(FileExistsError):
                seed(cfg, Path(d))
            seed(cfg, Path(d), overwrite=True)

    def test_simulated_origin_preserved(self):
        cfg = yaml.safe_load(Path("config/seeder.yaml").read_text())
        cfg["records"], cfg["requests"], cfg["consistency_events"] = 100, 100, 100
        cfg["consistency"]["hot_keys"] = 10
        with tempfile.TemporaryDirectory() as d:
            m = seed(cfg, Path(d))
            self.assertEqual(m["origin"], "simulated")


if __name__ == "__main__":
    unittest.main()
