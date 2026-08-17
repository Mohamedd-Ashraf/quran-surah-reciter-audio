"""Validation rules for ayah word-alignment JSON."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validate.validate_ayah import validate_alignment  # noqa: E402


def _ayah(duration_ms: int, words: list[dict]) -> dict:
    return {
        "schemaVersion": 1,
        "reciterId": "ar.alijaber",
        "surah": 1,
        "ayah": 1,
        "audioFile": "001001.mp3",
        "durationMs": duration_ms,
        "words": words,
    }


class LeadingSilenceTests(unittest.TestCase):
    def test_accepts_intro_silence_when_recitation_reaches_eof(self):
        # Ali Jaber 1:1: ~7.3s intro, four sequential words to EOF.
        data = _ayah(
            13244,
            [
                {"index": 1, "text": "aa", "startMs": 7340, "endMs": 7680},
                {"index": 2, "text": "bb", "startMs": 7800, "endMs": 8460},
                {"index": 3, "text": "cc", "startMs": 8600, "endMs": 9660},
                {"index": 4, "text": "dd", "startMs": 9760, "endMs": 13244},
            ],
        )
        vr = validate_alignment(data, min_mean_score=None)
        self.assertTrue(vr, vr.errors)

    def test_rejects_shifted_midfile_pocket(self):
        data = _ayah(
            13244,
            [
                {"index": 1, "text": "aa", "startMs": 7340, "endMs": 7680},
                {"index": 2, "text": "bb", "startMs": 7800, "endMs": 8460},
                {"index": 3, "text": "cc", "startMs": 8600, "endMs": 9000},
            ],
        )
        vr = validate_alignment(data, min_mean_score=None)
        self.assertFalse(vr)
        self.assertIn("late_start", vr.errors)
        self.assertIn("early_end", vr.errors)


if __name__ == "__main__":
    unittest.main()
