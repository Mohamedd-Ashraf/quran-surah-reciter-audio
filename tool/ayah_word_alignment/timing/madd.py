"""Madd *candidate* detection from vocalized Quranic clusters.

A candidate means the word contains a plausible elongation position. It does
**not** mean the reciter elongated it, and it is not Tajweed certification.

Shadda on ي/و after kasra/damma is modeled phonetically: Unicode stores one
``يَّ`` cluster, but the first half of the doubled consonant is a madd letter.
The cluster is never split in the stored text.
"""

from __future__ import annotations

from .clusters import Cluster, clusterize

_HAMZA_CARRIERS = frozenset("أإؤئٱ")
_PLAIN_ALEF = "ا"
_ALEF_MADDA = "آ"
_YEH = "ي"
_WAW = "و"
_ALEF_MAKSURA = "ى"


def detect_madd_candidates(text: str) -> list[dict]:
    """Return Madd candidates with ``type``, ``clusterIndex``, and ``reason``.

    ``clusterIndex`` is the 0-based grapheme cluster that bears the candidate.
    """
    clusters = clusterize(text)
    found: list[dict] = []
    seen: set[tuple[str, int]] = set()

    def add(kind: str, index: int, reason: str) -> None:
        key = (kind, index)
        if key in seen:
            return
        seen.add(key)
        found.append({"type": kind, "clusterIndex": index, "reason": reason})

    for i, c in enumerate(clusters):
        if c.kind != "base":
            continue
        prev: Cluster | None = clusters[i - 1] if i else None

        if c.base == _ALEF_MADDA:
            add("alif_madd", i, "alef_madda")

        if c.has_dagger_alif():
            add("alif_madd", i, "dagger_alif")

        if c.has_maddah():
            add("alif_madd", i, "maddah")

        if c.has_small_waw():
            add("waw_madd", i, "sila_waw")
        if c.has_small_yeh():
            add("ya_madd", i, "sila_yeh")

        if c.base == _PLAIN_ALEF and c.base not in _HAMZA_CARRIERS:
            if prev is not None and prev.has_fatha():
                add("alif_madd", i, "fatha_alif")

        if c.base == _ALEF_MAKSURA and prev is not None and prev.has_fatha():
            add("alif_madd", i, "fatha_alef_maksura")

        if c.base == _YEH and prev is not None:
            if prev.has_kasra():
                if c.has_shadda():
                    add("ya_madd", i, "kasra_before_shadda_ya")
                elif not c.has_vowel():
                    add("ya_madd", i, "kasra_ya")
            elif prev.has_fatha() and c.has_sukun() and not c.has_shadda():
                add("ya_lin", i, "madd_lin")

        if c.base == _WAW and prev is not None:
            if prev.has_damma():
                if c.has_shadda():
                    add("waw_madd", i, "damma_before_shadda_waw")
                elif not c.has_vowel():
                    add("waw_madd", i, "damma_waw")
            elif prev.has_fatha() and c.has_sukun() and not c.has_shadda():
                add("waw_lin", i, "madd_lin")

    return found


def madd_payload(text: str) -> dict | None:
    """Compact JSON object, or None when there is no candidate."""
    candidates = detect_madd_candidates(text)
    if not candidates:
        return None
    return {
        "hasCandidate": True,
        "candidates": candidates,
    }
