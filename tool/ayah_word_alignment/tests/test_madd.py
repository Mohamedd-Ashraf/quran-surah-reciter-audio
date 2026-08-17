"""Madd candidate tests — expected logical interpretation of vocalized words.

These cases document Unicode clusters vs phonetic Madd vs stretch anchors.
They are not Tajweed certification.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from timing.clusters import clusterize  # noqa: E402
from timing.madd import detect_madd_candidates  # noqa: E402
from timing.stretch import detect_stretch_positions, insert_tatweel  # noqa: E402

# Fully vocalized Hafs tokens (same as quran_ayahs.json / golden_words.json).
IYAKA = "\u0625\u0650\u064a\u0651\u064e\u0627\u0643\u064e"
WA_IYAKA = "\u0648\u064e\u0625\u0650\u064a\u0651\u064e\u0627\u0643\u064e"
NAABUDU = "\u0646\u064e\u0639\u06e1\u0628\u064f\u062f\u064f"
NASTAEEN = "\u0646\u064e\u0633\u06e1\u062a\u064e\u0639\u0650\u064a\u0646\u064f"
RAHMAN = "\u0671\u0644\u0631\u0651\u064e\u062d\u06e1\u0645\u064e\u0670\u0646\u0650"
DALLEEN = (
    "\u0671\u0644\u0636\u0651\u064e\u0627\u0653\u0644\u0651\u0650\u064a\u0646\u064e"
)
WALA = "\u0648\u064e\u0644\u064e\u0627"
ALAYHIM = "\u0639\u064e\u0644\u064e\u064a\u06e1\u0647\u0650\u0645\u06e1"
MAGHDOOBI = (
    "\u0671\u0644\u06e1\u0645\u064e\u063a\u06e1\u0636\u064f\u0648\u0628\u0650"
)


def _cluster_texts(word: str) -> list[str]:
    return [c.text for c in clusterize(word)]


def _types_at(word: str) -> list[tuple[str, int, str]]:
    return [(c["type"], c["clusterIndex"], c["reason"]) for c in detect_madd_candidates(word)]


class ClusterModelTests(unittest.TestCase):
    def test_iyyaka_four_clusters_shadda_stays_on_yeh(self):
        texts = _cluster_texts(IYAKA)
        self.assertEqual(len(texts), 4)
        self.assertEqual(texts[0], "\u0625\u0650")
        self.assertEqual(texts[1], "\u064a\u0651\u064e")
        self.assertEqual(texts[2], "\u0627")
        self.assertEqual(texts[3], "\u0643\u064e")
        yeh = clusterize(IYAKA)[1]
        self.assertTrue(yeh.has_shadda())
        self.assertTrue(yeh.has_fatha())
        self.assertEqual(yeh.joining, "dual")

    def test_nastaeen_bare_yeh_after_kasra(self):
        texts = _cluster_texts(NASTAEEN)
        self.assertEqual(texts[3], "\u0639\u0650")
        self.assertEqual(texts[4], "\u064a")
        self.assertFalse(clusterize(NASTAEEN)[4].has_shadda())

    def test_rahman_dagger_alif_on_meem(self):
        clusters = clusterize(RAHMAN)
        meem = [c for c in clusters if c.base == "\u0645"][0]
        self.assertTrue(meem.has_dagger_alif())
        self.assertTrue(meem.has_fatha())

    def test_dalleen_maddah_on_alef(self):
        clusters = clusterize(DALLEEN)
        alef = [c for c in clusters if c.base == "\u0627"][0]
        self.assertTrue(alef.has_maddah())


class IyyakaMaddTests(unittest.TestCase):
    """Shadda-yeh after kasra is ya_madd; following alef is also alif_madd."""

    def test_iyyaka_has_ya_madd_on_shadda_cluster(self):
        types = _types_at(IYAKA)
        ya = [t for t in types if t[0] == "ya_madd"]
        self.assertEqual(len(ya), 1, types)
        self.assertEqual(ya[0][1], 1)
        self.assertEqual(ya[0][2], "kasra_before_shadda_ya")

    def test_iyyaka_also_has_alif_madd(self):
        types = _types_at(IYAKA)
        alif = [t for t in types if t[0] == "alif_madd"]
        self.assertEqual(len(alif), 1, types)
        self.assertEqual(alif[0][1], 2)
        self.assertEqual(alif[0][2], "fatha_alif")

    def test_iyyaka_does_not_reject_yeh_merely_because_of_shadda(self):
        types = {t[0] for t in _types_at(IYAKA)}
        self.assertIn("ya_madd", types)

    def test_wa_iyyaka_same_shadda_pattern_shifted_by_waw(self):
        types = _types_at(WA_IYAKA)
        ya = [t for t in types if t[0] == "ya_madd"]
        alif = [t for t in types if t[0] == "alif_madd"]
        self.assertEqual(ya[0][1], 2)
        self.assertEqual(ya[0][2], "kasra_before_shadda_ya")
        self.assertEqual(alif[0][1], 3)
        waw_madds = [t for t in types if t[0] == "waw_madd"]
        self.assertEqual(waw_madds, [])


class OrdinaryMaddTests(unittest.TestCase):
    def test_naabudu_has_no_candidate(self):
        self.assertEqual(detect_madd_candidates(NAABUDU), [])

    def test_nastaeen_ya_madd_on_bare_yeh(self):
        types = _types_at(NASTAEEN)
        self.assertEqual(types, [("ya_madd", 4, "kasra_ya")])

    def test_rahman_dagger_alif(self):
        types = _types_at(RAHMAN)
        self.assertTrue(any(t == ("alif_madd", 4, "dagger_alif") for t in types), types)

    def test_dalleen_maddah_and_ya_madd(self):
        types = _types_at(DALLEEN)
        self.assertIn(("alif_madd", 3, "maddah"), types)
        self.assertIn(("ya_madd", 5, "kasra_ya"), types)

    def test_wala_alif_madd_not_waw_madd(self):
        types = _types_at(WALA)
        self.assertEqual([t[0] for t in types], ["alif_madd"])
        self.assertEqual(types[0][1], 2)

    def test_alayhim_is_madd_lin_not_ya_madd(self):
        types = _types_at(ALAYHIM)
        self.assertEqual(types, [("ya_lin", 2, "madd_lin")])

    def test_maghdoobi_waw_madd(self):
        types = _types_at(MAGHDOOBI)
        waw = [t for t in types if t[0] == "waw_madd"]
        self.assertEqual(len(waw), 1, types)
        self.assertEqual(waw[0][2], "damma_waw")

    def test_hamza_carriers_are_not_alif_madd(self):
        for word in ("\u0623\u064e", "\u0625\u0650", "\u0671"):
            types = [t[0] for t in _types_at(word)]
            self.assertNotIn("alif_madd", types, word)


class StretchAroundMaddTests(unittest.TestCase):
    def test_iyyaka_stretch_is_yeh_to_alef_not_forced_equal_to_madd(self):
        madd_idx = [c["clusterIndex"] for c in detect_madd_candidates(IYAKA)]
        pos = detect_stretch_positions(IYAKA, madd_cluster_indexes=madd_idx)
        indexes = [p["afterClusterIndex"] for p in pos]
        self.assertEqual(indexes, [1])
        self.assertIn(1, madd_idx)
        self.assertNotEqual(set(indexes), set(madd_idx))

    def test_nastaeen_prefers_boundaries_adjacent_to_yeh(self):
        madd_idx = [c["clusterIndex"] for c in detect_madd_candidates(NASTAEEN)]
        pos = detect_stretch_positions(NASTAEEN, madd_cluster_indexes=madd_idx)
        self.assertGreaterEqual(len(pos), 2)
        self.assertEqual(pos[0]["priority"], 1)
        adjacent = {p["afterClusterIndex"] for p in pos if p["priority"] == 1}
        self.assertEqual(adjacent, {3, 4})

    def test_reconstruction_never_splits_shadda_cluster(self):
        stretched = insert_tatweel(IYAKA, 1, 2)
        yeh_at = stretched.index("\u064a")
        self.assertEqual(stretched[yeh_at : yeh_at + 3], "\u064a\u0651\u064e")
        self.assertIn("\u0640\u0640", stretched)


if __name__ == "__main__":
    unittest.main()
