"""Duration stats, extension levels, and baseline helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from timing.config import TimingAnalysisConfig  # noqa: E402
from timing.extension import (  # noqa: E402
    classify_extension,
    duration_ratio,
    extension_confidence,
)
from timing.stats import leave_one_out_median, mean_ms, median_ms  # noqa: E402


class StatsTests(unittest.TestCase):
    def test_mean_and_median(self):
        vals = [300, 340, 320, 310, 330]
        self.assertEqual(mean_ms(vals), 320.0)
        self.assertEqual(median_ms(vals), 320.0)

    def test_median_robust_to_outlier(self):
        vals = [300, 310, 320, 330, 5000]
        self.assertEqual(median_ms(vals), 320.0)

    def test_empty_is_none(self):
        self.assertIsNone(mean_ms([]))
        self.assertIsNone(median_ms([]))

    def test_leave_one_out(self):
        vals = [100, 200, 300]
        self.assertEqual(leave_one_out_median(vals, 2), 150.0)


class ExtensionTests(unittest.TestCase):
    def setUp(self):
        self.cfg = TimingAnalysisConfig()

    def test_levels(self):
        self.assertEqual(classify_extension(1.0, self.cfg, has_candidate=True), "normal")
        self.assertEqual(
            classify_extension(1.5, self.cfg, has_candidate=True), "slightlyExtended"
        )
        self.assertEqual(classify_extension(2.0, self.cfg, has_candidate=True), "extended")
        self.assertEqual(
            classify_extension(3.0, self.cfg, has_candidate=True), "highlyExtended"
        )

    def test_unknown_without_baseline_or_candidate(self):
        self.assertIsNone(classify_extension(None, self.cfg, has_candidate=True))
        self.assertIsNone(classify_extension(3.0, self.cfg, has_candidate=False))

    def test_ratio(self):
        self.assertEqual(duration_ratio(900, 190), 4.737)
        self.assertIsNone(duration_ratio(900, None))
        self.assertIsNone(duration_ratio(None, 190))
        self.assertIsNone(duration_ratio(900, 0))

    def test_confidence_omitted_without_score(self):
        self.assertIsNone(
            extension_confidence(
                score=None,
                sample_count=10,
                source="word",
                has_candidate=True,
                ratio=2.0,
            )
        )

    def test_confidence_present_with_good_score(self):
        c = extension_confidence(
            score=-0.3,
            sample_count=10,
            source="word",
            has_candidate=True,
            ratio=2.0,
        )
        self.assertIsNotNone(c)
        self.assertGreater(c, 0.5)
        poor = extension_confidence(
            score=-7.5,
            sample_count=3,
            source="reciter",
            has_candidate=True,
            ratio=2.0,
        )
        self.assertLess(poor, c)


if __name__ == "__main__":
    unittest.main()
