"""Tests for timing refine (no ML deps)."""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from align.refine import refine_word_timings, timing_quality, target_min_ms  # noqa: E402


@dataclass
class W:
    index: int
    text: str
    start_ms: int
    end_ms: int
    score: float | None = None


class RefineTests(unittest.TestCase):
    def test_expands_collapsed_into_gap(self):
        # Mimic bad CTC: سنة is 60ms with huge surrounding gaps
        words = [
            W(1, "تاخذه", 7740, 8100),
            W(2, "سنه", 9260, 9320),  # collapsed
            W(3, "ولا", 10060, 10320),
        ]
        out = refine_word_timings(words, duration_ms=12000, waveform=None)
        dur = out[1].end_ms - out[1].start_ms
        self.assertGreaterEqual(dur, 120)
        self.assertGreaterEqual(out[1].start_ms, out[0].end_ms - 1)
        self.assertLessEqual(out[1].end_ms, out[2].start_ms + 1)

    def test_quality_prefers_coverage(self):
        bad = [
            W(1, "ا", 0, 50),
            W(2, "ب", 5000, 5050),
            W(3, "ج", 9900, 10000),
        ]
        good = [
            W(1, "ا", 0, 3000),
            W(2, "ب", 3000, 6500),
            W(3, "ج", 6500, 10000),
        ]
        self.assertGreater(timing_quality(good, 10000), timing_quality(bad, 10000))

    def test_target_min_scales(self):
        self.assertGreater(target_min_ms("السموات"), target_min_ms("في"))


if __name__ == "__main__":
    unittest.main()