"""Merge-job fail-rate accounting."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runner.merge_reports import merge_summaries  # noqa: E402


class MergeFailRateTests(unittest.TestCase):
    def test_skipped_ayahs_count_in_denominator(self):
        out = merge_summaries(
            [
                {
                    "attempted": 7,
                    "passed": 0,
                    "failed": 1,
                    "skipped": 6,
                    "failures": [{"surah": 1, "ayah": 1, "reason": "late_start"}],
                }
            ]
        )
        self.assertEqual(out["processed"], 1)
        self.assertAlmostEqual(out["failRate"], 1 / 7)
        self.assertNotAlmostEqual(out["failRate"], 1.0)

    def test_all_skipped_is_zero_fail_rate(self):
        out = merge_summaries(
            [{"attempted": 7, "passed": 0, "failed": 0, "skipped": 7, "failures": []}]
        )
        self.assertEqual(out["failRate"], 0.0)

    def test_exact_threshold_does_not_exceed(self):
        out = merge_summaries(
            [{"attempted": 100, "passed": 95, "failed": 5, "skipped": 0, "failures": []}]
        )
        self.assertAlmostEqual(out["failRate"], 0.05)


if __name__ == "__main__":
    unittest.main()
