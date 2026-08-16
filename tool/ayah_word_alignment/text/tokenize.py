"""API-word tokenization matching Dart quran_mark_utils.dart."""

from __future__ import annotations

import re

_ARABIC_INDIC_DIGITS = re.compile(r"^[\u0660-\u0669]+$")


def is_hizb_or_sajda_token(token: str) -> bool:
    return "\u06DE" in token or "\u06E9" in token


def is_verse_number_token(token: str) -> bool:
    return bool(_ARABIC_INDIC_DIGITS.match(token))


def api_words_from_line(line: str) -> list[str]:
    tokens = [t for t in re.split(r"\s+", line) if t]
    words: list[str] = []
    for token in tokens:
        if is_hizb_or_sajda_token(token):
            continue
        if is_verse_number_token(token):
            continue
        words.append(token)
    return words


def api_words_from_text(text: str) -> list[str]:
    """Return canonical API words in order (1-based index = i+1)."""
    words: list[str] = []
    for line in text.split("\n"):
        words.extend(api_words_from_line(line))
    return words


def count_api_words(text: str) -> int:
    return len(api_words_from_text(text))
