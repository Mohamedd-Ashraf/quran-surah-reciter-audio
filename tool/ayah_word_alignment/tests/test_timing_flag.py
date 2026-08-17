"""Feature flag: disabled path must skip Madd, stretch, stats, and extra fields."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from timing.aggregator import enrich_reciter  # noqa: E402
from timing.analyzer import attach_ayah  # noqa: E402
from timing.config import TimingAnalysisConfig  # noqa: E402

SAMPLE = {
    "schemaVersion": 1,
    "reciterId": "ar.alijaber",
    "surah": 1,
    "ayah": 5,
    "audioFile": "001005.mp3",
    "durationMs": 7758,
    "words": [
        {
            "index": 1,
            "text": "\u0625\u0650\u064a\u0651\u064e\u0627\u0643\u064e",
            "startMs": 800,
            "endMs": 1930,
            "score": -0.3848,
        }
    ],
    "meta": {"strategy": "xlsr_nodiac_segment"},
}


class FlagTests(unittest.TestCase):
    def test_disabled_does_not_call_detectors(self):
        cfg = TimingAnalysisConfig(enabled=False)
        with (
            patch("timing.analyzer.madd_payload") as madd,
            patch("timing.analyzer.stretch_payload") as stretch,
        ):
            out = attach_ayah(json.loads(json.dumps(SAMPLE)), cfg)
            madd.assert_not_called()
            stretch.assert_not_called()
        self.assertEqual(out["words"][0].keys(), SAMPLE["words"][0].keys())
        self.assertNotIn("timingAnalysis", (out.get("meta") or {}))

    def test_enabled_does_call_detectors(self):
        cfg = TimingAnalysisConfig(enabled=True)
        out = attach_ayah(json.loads(json.dumps(SAMPLE)), cfg)
        self.assertIn("durationMs", out["words"][0])
        self.assertIn("madd", out["words"][0])
        self.assertEqual(out["meta"]["timingAnalysis"]["enabled"], True)

    def test_from_mapping_yaml_shape(self):
        cfg = TimingAnalysisConfig.from_mapping(
            {
                "enable_timing_analysis": False,
                "timing_analysis": {"max_tatweel_per_position": 2},
            }
        )
        self.assertFalse(cfg.enabled)
        self.assertEqual(cfg.max_tatweel_per_position, 2)

    def test_default_enabled(self):
        self.assertTrue(TimingAnalysisConfig.from_mapping({}).enabled)
        self.assertTrue(TimingAnalysisConfig().enabled)

    def test_enrich_disabled_skips_tree(self):
        cfg = TimingAnalysisConfig(enabled=False)
        with patch("timing.aggregator._iter_ayah_files", return_value=[]):
            self.assertEqual(enrich_reciter(".", cfg), 0)


if __name__ == "__main__":
    unittest.main()
