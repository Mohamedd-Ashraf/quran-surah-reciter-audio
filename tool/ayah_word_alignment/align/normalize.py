"""Normalize Arabic for CTC aligner input; keep canonical text for publish."""

from __future__ import annotations

import re
import unicodedata

# Quranic annotation / pause marks that confuse CTC vocab
_STRIP_MARKS = re.compile(
    r"[\u06D6-\u06ED\u06DE\u06E9\u064B-\u065F\u0670\u0640]"
)

_ALEF_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ة": "ه",
    }
)


def normalize_for_aligner(word: str, *, keep_diacritics: bool = False) -> str:
    """Produce a CTC-friendly token while preserving length as a word unit."""
    text = unicodedata.normalize("NFC", word)
    # Drop format chars
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    if not keep_diacritics:
        text = _STRIP_MARKS.sub("", text)
    else:
        # Still strip waqf / annotation marks
        text = re.sub(r"[\u06D6-\u06ED\u06DE\u06E9]", "", text)
    text = text.translate(_ALEF_MAP)
    text = text.strip()
    if not text:
        # Never drop a word from the reference sequence
        return "ا"
    return text


def join_aligner_words(words: list[str], *, keep_diacritics: bool = False) -> str:
    return " ".join(normalize_for_aligner(w, keep_diacritics=keep_diacritics) for w in words)
