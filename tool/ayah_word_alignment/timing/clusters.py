"""Grapheme clusters + Arabic joining types for vocalized Quranic words.

A cluster is one base letter plus its combining marks. Shadda stays on the
same Unicode cluster as its base (e.g. ``يَّ`` is one cluster). Madd analysis
may interpret that cluster as more than one phonetic component, but must not
split the stored string.

``afterClusterIndex`` / ``clusterIndex`` are 0-based indexes into this list.
"""

from __future__ import annotations

from dataclasses import dataclass

# Combining / Quranic marks that attach to the preceding base letter.
# Ranges aligned with tajweed_parser.dart combining detection (copied, not imported).
_COMBINING_RANGES = (
    (0x0610, 0x061A),
    (0x064B, 0x065F),  # harakat, shadda, sukun, maddah, hamza above/below
    (0x06D6, 0x06DC),  # waqf
    (0x06DF, 0x06E8),  # small high signs, madda, small waw/yeh
    (0x06EA, 0x06ED),
)
_DAGGER_ALIF = 0x0670
_TATWEEL = 0x0640
_HAMZA = 0x0621

# Unicode Arabic joining group Right_Joining (does not join to the *following* letter).
_RIGHT_JOINING = frozenset(
    {
        0x0622,  # ALEF WITH MADDA ABOVE
        0x0623,  # ALEF WITH HAMZA ABOVE
        0x0624,  # WAW WITH HAMZA ABOVE
        0x0625,  # ALEF WITH HAMZA BELOW
        0x0627,  # ALEF
        0x0629,  # TEH MARBUTA
        0x062F,  # DAL
        0x0630,  # THAL
        0x0631,  # REH
        0x0632,  # ZAIN
        0x0648,  # WAW
        0x0649,  # ALEF MAKSURA
        0x0671,  # ALEF WASLA
        0x06C0,  # HEH WITH YEH ABOVE
        0x06D2,  # YEH BARREE
        0x06D3,  # YEH BARREE WITH HAMZA ABOVE
    }
)

JOIN_DUAL = "dual"
JOIN_RIGHT = "right"
JOIN_NON = "nonjoining"

FATHA = 0x064E
DAMMA = 0x064F
KASRA = 0x0650
SHADDA = 0x0651
SUKUN = 0x0652
QURANIC_SUKUN = 0x06E1  # small high dotless head of khah
MADDAH = 0x0653
SMALL_HIGH_MADDA = 0x06E4
DAGGER_ALIF = _DAGGER_ALIF
SMALL_WAW = 0x06E5
SMALL_YEH = 0x06E6
FATHATAN = 0x064B
DAMMATAN = 0x064C
KASRATAN = 0x064D

_VOWELS = frozenset({FATHA, DAMMA, KASRA, FATHATAN, DAMMATAN, KASRATAN})
_SUKUNS = frozenset({SUKUN, QURANIC_SUKUN})
_MADDAHS = frozenset({MADDAH, SMALL_HIGH_MADDA})

WAQF_RANGE = range(0x06D6, 0x06DD)
_STRIP_FOR_KEY = frozenset({0x06DE, 0x06E9, _TATWEEL}) | set(WAQF_RANGE)


def is_combining(cp: int) -> bool:
    if cp == _DAGGER_ALIF:
        return True
    for a, b in _COMBINING_RANGES:
        if a <= cp <= b:
            return True
    return False


def joining_type(base_cp: int) -> str:
    """Arabic joining class of a base letter (Unicode ArabicShaping, subset)."""
    if base_cp == _HAMZA:
        return JOIN_NON
    if base_cp == _TATWEEL:
        return JOIN_DUAL
    if base_cp in _RIGHT_JOINING:
        return JOIN_RIGHT
    if 0x0620 <= base_cp <= 0x06FF:
        return JOIN_DUAL
    return JOIN_NON


@dataclass(frozen=True)
class Cluster:
    index: int
    kind: str  # base | tatweel | other
    base_cp: int
    text: str
    start: int  # codepoint offset in original
    marks: str
    joining: str

    @property
    def base(self) -> str:
        return chr(self.base_cp) if self.base_cp >= 0 else ""

    def has_mark(self, *cps: int) -> bool:
        return any(ord(m) in cps for m in self.marks)

    def has_fatha(self) -> bool:
        return self.has_mark(FATHA)

    def has_damma(self) -> bool:
        return self.has_mark(DAMMA)

    def has_kasra(self) -> bool:
        return self.has_mark(KASRA)

    def has_shadda(self) -> bool:
        return self.has_mark(SHADDA)

    def has_sukun(self) -> bool:
        return any(ord(m) in _SUKUNS for m in self.marks)

    def has_vowel(self) -> bool:
        return any(ord(m) in _VOWELS for m in self.marks)

    def has_maddah(self) -> bool:
        return any(ord(m) in _MADDAHS for m in self.marks)

    def has_dagger_alif(self) -> bool:
        return self.has_mark(DAGGER_ALIF)

    def has_small_waw(self) -> bool:
        return self.has_mark(SMALL_WAW) or self.base_cp == SMALL_WAW

    def has_small_yeh(self) -> bool:
        return self.has_mark(SMALL_YEH) or self.base_cp == SMALL_YEH


def clusterize(text: str) -> list[Cluster]:
    """Split vocalized ``text`` into base+marks clusters. Never splits a mark off."""
    if not text:
        return []
    clusters: list[Cluster] = []
    i = 0
    chars = list(text)
    n = len(chars)
    while i < n:
        cp = ord(chars[i])
        start = i
        if is_combining(cp):
            # Orphan mark: attach to previous cluster if any, else skip as other.
            if clusters:
                prev = clusters[-1]
                clusters[-1] = Cluster(
                    index=prev.index,
                    kind=prev.kind,
                    base_cp=prev.base_cp,
                    text=prev.text + chars[i],
                    start=prev.start,
                    marks=prev.marks + chars[i],
                    joining=prev.joining,
                )
            else:
                clusters.append(
                    Cluster(
                        index=len(clusters),
                        kind="other",
                        base_cp=cp,
                        text=chars[i],
                        start=start,
                        marks="",
                        joining=JOIN_NON,
                    )
                )
            i += 1
            continue
        marks = []
        j = i + 1
        while j < n and is_combining(ord(chars[j])):
            marks.append(chars[j])
            j += 1
        mark_str = "".join(marks)
        if cp == _TATWEEL:
            kind = "tatweel"
        elif 0x0600 <= cp <= 0x06FF:
            kind = "base"
        else:
            kind = "other"
        clusters.append(
            Cluster(
                index=len(clusters),
                kind=kind,
                base_cp=cp,
                text=chars[i] + mark_str,
                start=start,
                marks=mark_str,
                joining=joining_type(cp),
            )
        )
        i = j
    return clusters


def baseline_key(text: str) -> str:
    """Identity for reciter/word baselines: vocalized text minus waqf/hizb/tatweel."""
    return "".join(
        c for c in text if ord(c) not in _STRIP_FOR_KEY
    )


def joins_forward(cluster: Cluster) -> bool:
    """True if Tatweel after this cluster can connect from the left letter."""
    return cluster.kind in {"base", "tatweel"} and cluster.joining == JOIN_DUAL


def joins_backward(cluster: Cluster) -> bool:
    """True if Tatweel before this cluster can connect into the right letter."""
    return cluster.kind in {"base", "tatweel"} and cluster.joining in {
        JOIN_DUAL,
        JOIN_RIGHT,
    }
