"""Per-ayah attach and reciter aggregator tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from timing.aggregator import enrich_reciter  # noqa: E402
from timing.analyzer import attach_ayah, word_duration_ms  # noqa: E402
from timing.config import TimingAnalysisConfig  # noqa: E402

IYAKA = "\u0625\u0650\u064a\u0651\u064e\u0627\u0643\u064e"
NAABUDU = "\u0646\u064e\u0639\u06e1\u0628\u064f\u062f\u064f"
NASTAEEN = "\u0646\u064e\u0633\u06e1\u062a\u064e\u0639\u0650\u064a\u0646\u064f"
WA_IYAKA = "\u0648\u064e\u0625\u0650\u064a\u0651\u064e\u0627\u0643\u064e"


def _ayah(words, surah=1, ayah=5):
    return {
        "schemaVersion": 1,
        "reciterId": "ar.alijaber",
        "surah": surah,
        "ayah": ayah,
        "audioFile": f"{surah:03d}{ayah:03d}.mp3",
        "durationMs": words[-1][2] if words else 0,
        "words": [
            {
                "index": i + 1,
                "text": t,
                "startMs": s,
                "endMs": e,
                "score": score,
            }
            for i, (t, s, e, score) in enumerate(words)
        ],
        "meta": {"strategy": "xlsr_nodiac_segment", "quality": 35.0},
    }


FATIHA_15 = _ayah(
    [
        (IYAKA, 800, 1930, -0.3848),
        (NAABUDU, 1930, 2810, -0.5646),
        (WA_IYAKA, 2810, 4420, -0.414),
        (NASTAEEN, 4420, 7758, -0.1831),
    ]
)


class DurationTests(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(word_duration_ms({"startMs": 800, "endMs": 1930}), 1130)

    def test_zero_omitted(self):
        self.assertIsNone(word_duration_ms({"startMs": 100, "endMs": 100}))

    def test_invalid_end_before_start(self):
        self.assertIsNone(word_duration_ms({"startMs": 500, "endMs": 100}))

    def test_missing_timestamps(self):
        self.assertIsNone(word_duration_ms({"startMs": 100}))
        self.assertIsNone(word_duration_ms({"text": "x"}))


class AttachAyahTests(unittest.TestCase):
    def test_fatiha_15_fixture(self):
        cfg = TimingAnalysisConfig()
        out = attach_ayah(json.loads(json.dumps(FATIHA_15)), cfg)
        self.assertEqual(out["schemaVersion"], 1)
        self.assertEqual(out["words"][0]["text"], IYAKA)
        self.assertEqual(out["words"][0]["startMs"], 800)
        self.assertEqual(out["words"][0]["endMs"], 1930)
        self.assertEqual(out["words"][0]["durationMs"], 1130)
        madd = out["words"][0]["madd"]
        self.assertTrue(madd["hasCandidate"])
        types = {c["type"] for c in madd["candidates"]}
        self.assertIn("ya_madd", types)
        self.assertIn("alif_madd", types)
        ya = [c for c in madd["candidates"] if c["type"] == "ya_madd"][0]
        self.assertEqual(ya["clusterIndex"], 1)
        self.assertEqual(ya["reason"], "kasra_before_shadda_ya")
        self.assertIn("stretch", out["words"][0])
        self.assertEqual(out["words"][1].get("madd"), None)
        self.assertIn("timing", out)
        self.assertEqual(out["meta"]["timingAnalysis"], {"enabled": True})
        # Canonical text unchanged
        self.assertEqual([w["text"] for w in out["words"]], [w["text"] for w in FATIHA_15["words"]])

    def test_disabled_is_identity(self):
        cfg = TimingAnalysisConfig(enabled=False)
        src = json.loads(json.dumps(FATIHA_15))
        out = attach_ayah(src, cfg)
        self.assertIs(out, src)
        self.assertNotIn("durationMs", out["words"][0])
        self.assertNotIn("madd", out["words"][0])
        self.assertNotIn("stretch", out["words"][0])
        self.assertNotIn("timing", out)


class AggregatorTests(unittest.TestCase):
    def test_two_pass_word_baseline(self):
        cfg = TimingAnalysisConfig(
            min_word_baseline_samples=3,
            min_surah_baseline_words=8,
            min_verse_baseline_others=2,
            min_reciter_baseline_words=8,
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Same vocalized word with 4 durations; last one is long.
            samples = [300, 340, 320, 1200]
            for i, dur in enumerate(samples, start=1):
                data = _ayah([(IYAKA, 0, dur, -0.2)], surah=1, ayah=i)
                data = attach_ayah(data, cfg)
                (root / "1" / f"{i}.json").parent.mkdir(parents=True, exist_ok=True)
                (root / "1" / f"{i}.json").write_text(
                    json.dumps(data, ensure_ascii=False), encoding="utf-8"
                )
            n = enrich_reciter(root, cfg)
            self.assertEqual(n, 4)
            last = json.loads((root / "1" / "4.json").read_text(encoding="utf-8"))
            w = last["words"][0]
            self.assertEqual(w["baselineSource"], "word")
            self.assertAlmostEqual(w["baselineMs"], 320.0)
            self.assertGreater(w["durationRatio"], 3.0)
            self.assertEqual(w["extensionLevel"], "highlyExtended")

    def test_disabled_writes_nothing(self):
        cfg = TimingAnalysisConfig(enabled=False)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "1").mkdir()
            (root / "1" / "1.json").write_text(json.dumps(FATIHA_15), encoding="utf-8")
            self.assertEqual(enrich_reciter(root, cfg), 0)
            after = json.loads((root / "1" / "1.json").read_text(encoding="utf-8"))
            self.assertNotIn("durationMs", after["words"][0])


if __name__ == "__main__":
    unittest.main()
