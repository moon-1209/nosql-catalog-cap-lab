import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.catalog_analysis.bootstrap_ci import bootstrap_ci


class TestBootstrapCI(unittest.TestCase):
    def test_ci_brackets_estimate_and_is_deterministic(self):
        rng = np.random.default_rng(1)
        x = rng.normal(10, 2, 500)
        r1 = bootstrap_ci(x, np.mean, n_resamples=500, seed=9)
        r2 = bootstrap_ci(x, np.mean, n_resamples=500, seed=9)
        self.assertEqual(r1, r2)  # seeded => reproducible
        self.assertLessEqual(r1["ci_low"], r1["estimate"])
        self.assertLessEqual(r1["estimate"], r1["ci_high"])
        # CI for the mean of n=500, sd=2 should be narrow around 10
        self.assertAlmostEqual(r1["estimate"], 10, delta=0.3)
        self.assertLess(r1["ci_high"] - r1["ci_low"], 0.6)

    def test_block_method_runs(self):
        x = np.sin(np.linspace(0, 50, 400))  # autocorrelated
        r = bootstrap_ci(x, np.mean, n_resamples=200, seed=3,
                         method="block", block_len=25)
        self.assertIsNotNone(r["ci_low"])
        self.assertEqual(r["method"], "block")

    def test_nan_and_small_sample(self):
        r = bootstrap_ci([1.0, np.nan, 2.0], np.mean, seed=1)
        self.assertIsNone(r["ci_low"])
        self.assertEqual(r["n"], 2)
        self.assertIn("insufficient", r["note"])

    def test_all_nan(self):
        r = bootstrap_ci([np.nan] * 100, np.mean, seed=1)
        self.assertIsNone(r["estimate"])
        self.assertIsNone(r["ci_low"])

    def test_bad_method(self):
        r = bootstrap_ci(np.arange(100.0), np.mean, seed=1, method="nope")
        self.assertIsNone(r["ci_low"])
        self.assertEqual(r["note"], "unknown method")


if __name__ == "__main__":
    unittest.main()
