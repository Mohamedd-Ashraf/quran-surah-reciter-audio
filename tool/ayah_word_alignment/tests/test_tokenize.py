"""Unit tests for API-word tokenization (no ML deps)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from text.load_quran import ayah_entry, load_quran_index  # noqa: E402
from text.tokenize import api_words_from_text, count_api_words  # noqa: E402
from validate.validate_ayah import validate_alignment  # noqa: E402


class TokenizeTests(unittest.TestCase):
    def test_fatiha_1_word_count(self):
        entry = ayah_entry(1, 1)
        words = api_words_from_text(entry["aya_text"])
        # بسم الله الرحمن الرحيم  (verse number stripped)
        self.assertEqual(len(words), 4)
        self.assertTrue(words[0].startswith("ب"))

    def test_fatiha_7_word_count(self):
        entry = ayah_entry(1, 7)
        words = api_words_from_text(entry["aya_text"])
        self.assertGreaterEqual(len(words), 8)

    def test_waqf_stays_on_same_word(self):
        plain = "كَلِمَةٌ\u06D6 كَلِمَةٌ"
        words = api_words_from_text(plain)
        self.assertEqual(len(words), 2)
        self.assertTrue(words[0].endswith("\u06D6"))

    def test_skips_hizb(self):
        plain = "كلمة \u06DE كلمة"
        words = api_words_from_text(plain)
        self.assertEqual(len(words), 2)

    def test_ayat_kursi_exists(self):
        entry = ayah_entry(2, 255)
        words = api_words_from_text(entry["aya_text"])
        self.assertGreater(len(words), 40)

    def test_quran_index_size(self):
        idx = load_quran_index()
        self.assertGreaterEqual(len(idx), 6230)


class ValidateTests(unittest.TestCase):
    def test_valid_minimal(self):
        data = {
            "schemaVersion": 1,
            "reciterId": "ar.alafasy",
            "surah": 1,
            "ayah": 1,
            "audioFile": "001001.mp3",
            "durationMs": 5000,
            "words": [
                {"index": 1, "text": "ا", "startMs": 100, "endMs": 800},
                {"index": 2, "text": "ب", "startMs": 900, "endMs": 1500},
                {"index": 3, "text": "ج", "startMs": 1600, "endMs": 2200},
                {"index": 4, "text": "د", "startMs": 2300, "endMs": 4800},
            ],
        }
        vr = validate_alignment(
            data, expected_words=["ا", "ب", "ج", "د"], min_mean_score=None
        )
        self.assertTrue(vr, vr.errors)

    def test_rejects_bad_index(self):
        data = {
            "schemaVersion": 1,
            "reciterId": "ar.alafasy",
            "surah": 1,
            "ayah": 1,
            "audioFile": "001001.mp3",
            "durationMs": 3000,
            "words": [
                {"index": 2, "text": "ا", "startMs": 0, "endMs": 500},
            ],
        }
        vr = validate_alignment(data, expected_words=["ا"], min_mean_score=None)
        self.assertFalse(vr)


class GoldenExport(unittest.TestCase):
    """Write golden word lists for Dart parity checks."""

    def test_export_golden(self):
        keys = [(1, 1), (1, 7), (2, 255), (112, 1), (112, 4), (114, 6)]
        golden = {}
        for s, a in keys:
            entry = ayah_entry(s, a)
            words = api_words_from_text(entry["aya_text"])
            golden[f"{s}:{a}"] = {
                "wordCount": len(words),
                "words": words,
            }
        out = ROOT / "testdata" / "golden_words.json"
        out.write_text(json.dumps(golden, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(out.is_file())


if __name__ == "__main__":
    unittest.main()
