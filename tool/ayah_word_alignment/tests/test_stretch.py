"""Arabic joining and Tatweel reconstruction tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from timing.clusters import JOIN_DUAL, JOIN_RIGHT, clusterize, joining_type  # noqa: E402
from timing.stretch import (  # noqa: E402
    detect_stretch_positions,
    insert_tatweel,
    safe_boundaries,
)

# Dual + dual (noon + seen)
NOON_SEEN = "\u0646\u0633"
# Right-joining alef then dual beh: must NOT be a stretch boundary
ALEF_BEH = "\u0627\u0628"
# Dual noon then right-joining alef: IS a stretch boundary (noon kashida into alef)
NOON_ALEF = "\u0646\u0627"
# Dal (right) then beh (dual): not safe
DAL_BEH = "\u062f\u0628"
# Isolated hamza
HAMZA = "\u0621\u0628"

IYAKA = "\u0625\u0650\u064a\u0651\u064e\u0627\u0643\u064e"
NASTAEEN = "\u0646\u064e\u0633\u06e1\u062a\u064e\u0639\u0650\u064a\u0646\u064f"
DALLEEN = (
    "\u0671\u0644\u0636\u0651\u064e\u0627\u0653\u0644\u0651\u0650\u064a\u0646\u064e"
)


class JoiningClassTests(unittest.TestCase):
    def test_right_joining_letters(self):
        for cp in (0x0627, 0x062F, 0x0630, 0x0631, 0x0632, 0x0648, 0x0649, 0x0671):
            self.assertEqual(joining_type(cp), JOIN_RIGHT, hex(cp))

    def test_dual_joining_letters(self):
        for cp in (0x0628, 0x0646, 0x0633, 0x064A, 0x0644, 0x0645):
            self.assertEqual(joining_type(cp), JOIN_DUAL, hex(cp))

    def test_hamza_nonjoining(self):
        self.assertEqual(joining_type(0x0621), "nonjoining")


class SafeBoundaryTests(unittest.TestCase):
    def test_noon_seen_is_safe(self):
        self.assertEqual(safe_boundaries(clusterize(NOON_SEEN)), [0])

    def test_alef_beh_is_not_safe(self):
        self.assertEqual(safe_boundaries(clusterize(ALEF_BEH)), [])

    def test_noon_alef_is_safe(self):
        self.assertEqual(safe_boundaries(clusterize(NOON_ALEF)), [0])

    def test_dal_beh_is_not_safe(self):
        self.assertEqual(safe_boundaries(clusterize(DAL_BEH)), [])

    def test_empty_when_no_boundary(self):
        self.assertEqual(detect_stretch_positions("\u0627"), [])

    def test_combining_marks_do_not_create_fake_boundaries(self):
        # noon+fatha + seen+sukun: still one boundary between the two bases
        word = "\u0646\u064e\u0633\u06e1"
        clusters = clusterize(word)
        self.assertEqual(len(clusters), 2)
        self.assertEqual(safe_boundaries(clusters), [0])

    def test_quranic_marks_attach_not_split(self):
        clusters = clusterize(DALLEEN)
        alef = [c for c in clusters if c.has_maddah()][0]
        self.assertEqual(alef.base, "\u0627")
        self.assertIn("\u0653", alef.marks)

    def test_iyyaka_only_yeh_alef_boundary(self):
        pos = detect_stretch_positions(IYAKA)
        self.assertEqual([p["afterClusterIndex"] for p in pos], [1])

    def test_priority_orders_deterministically(self):
        pos = detect_stretch_positions(
            NASTAEEN, madd_cluster_indexes=[4]
        )
        indexes = [p["afterClusterIndex"] for p in pos]
        self.assertEqual(indexes, sorted(indexes, key=lambda i: (
            0 if i in (3, 4) else 1,
            i,
        )))
        self.assertTrue(all(pos[i]["priority"] <= pos[i + 1]["priority"] for i in range(len(pos) - 1)))


class ReconstructionTests(unittest.TestCase):
    def test_insert_between_clusters_keeps_marks(self):
        original = IYAKA
        out = insert_tatweel(original, 1, 3)
        clusters_in = clusterize(original)
        prefix = "".join(c.text for c in clusters_in[:2])
        suffix = "".join(c.text for c in clusters_in[2:])
        self.assertEqual(out, prefix + "\u0640" * 3 + suffix)
        # Yeh still adjacent to shadda
        self.assertIn("\u064a\u0651\u064e", out)
        self.assertNotIn("\u064a\u0640", out)

    def test_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            insert_tatweel(IYAKA, 99)
        with self.assertRaises(ValueError):
            insert_tatweel(IYAKA, 3)  # last cluster — no following letter

    def test_every_reported_position_reconstructs(self):
        for word in (IYAKA, NASTAEEN, DALLEEN, NOON_SEEN, NOON_ALEF):
            for p in detect_stretch_positions(word):
                out = insert_tatweel(word, p["afterClusterIndex"], 1)
                self.assertIn("\u0640", out)
                # All original codepoints remain, in order, with tatweel inserted.
                stripped = out.replace("\u0640", "")
                self.assertEqual(stripped, word)


if __name__ == "__main__":
    unittest.main()
