"""Unit tests for align mode catalog (no ML deps)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from align.strategies import (  # noqa: E402
    MODE_CONFIG,
    early_exit_quality,
    normalize_align_mode,
    should_early_exit,
    strategies_for_mode,
)


class StrategyModeTests(unittest.TestCase):
    def test_modes_exist(self):
        self.assertEqual(set(MODE_CONFIG), {"fast", "balanced", "max"})

    def test_normalize(self):
        self.assertEqual(normalize_align_mode("Balanced"), "balanced")
        with self.assertRaises(ValueError):
            normalize_align_mode("turbo")

    def test_fast_leads_with_mms(self):
        names = [s["name"] for s in strategies_for_mode("fast")]
        self.assertEqual(names[0], "mms_roman_edges")
        self.assertNotIn("xlsr_diac_edges", names)

    def test_balanced_includes_diac_fallback(self):
        names = [s["name"] for s in strategies_for_mode("balanced")]
        self.assertEqual(names[0], "mms_roman_edges")
        self.assertIn("xlsr_diac_edges", names)

    def test_max_never_early_exits(self):
        self.assertIsNone(early_exit_quality("max"))
        self.assertFalse(should_early_exit(99.0, None))

    def test_early_exit_thresholds(self):
        self.assertTrue(should_early_exit(32.0, early_exit_quality("balanced")))
        self.assertFalse(should_early_exit(31.9, early_exit_quality("balanced")))
        self.assertTrue(should_early_exit(28.0, early_exit_quality("fast")))
        self.assertFalse(should_early_exit(27.9, early_exit_quality("fast")))


if __name__ == "__main__":
    unittest.main()