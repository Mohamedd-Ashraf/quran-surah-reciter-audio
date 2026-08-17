"""Validate one ayah word-alignment JSON before publish."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_WAQF = frozenset("\u06D6\u06D7\u06D8\u06D9\u06DA\u06DB\u06DC")


def _has_waqf(text: str) -> bool:
    return any(c in _WAQF for c in text)


def _letter_count(text: str) -> int:
    return max(1, sum(1 for c in text if c.isalpha() or ("\u0600" <= c <= "\u06FF")))


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]

    def __bool__(self) -> bool:
        return self.ok


def validate_alignment(
    data: dict[str, Any],
    *,
    expected_words: list[str] | None = None,
    min_mean_score: float | None = -20.0,
    max_word_ms: int = 15000,
    min_word_ms: int = 80,
    max_very_short_frac: float = 0.08,
    min_coverage: float = 0.48,
    max_non_waqf_gap_ms: int = 1600,
) -> ValidationResult:
    errors: list[str] = []

    for key in ("schemaVersion", "reciterId", "surah", "ayah", "audioFile", "durationMs", "words"):
        if key not in data:
            errors.append(f"missing_field:{key}")

    if errors:
        return ValidationResult(False, errors)

    duration = int(data["durationMs"])
    words = data["words"]
    if not isinstance(words, list) or not words:
        return ValidationResult(False, ["empty_words"])

    if expected_words is not None and len(words) != len(expected_words):
        errors.append(
            f"word_count expected={len(expected_words)} got={len(words)}"
        )

    prev_end = -1
    scores: list[float] = []
    very_short = 0
    covered = 0
    for i, w in enumerate(words):
        idx = int(w.get("index", -1))
        if idx != i + 1:
            errors.append(f"index_order at {i}: got {idx}")
        text = w.get("text", "")
        if expected_words is not None and text != expected_words[i]:
            errors.append(f"text_mismatch at {idx}")
        start = int(w["startMs"])
        end = int(w["endMs"])
        if start < 0 or end < 0:
            errors.append(f"negative_ts at {idx}")
        if start >= end:
            errors.append(f"start_ge_end at {idx}")
        if end > duration + 50:
            errors.append(f"end_past_duration at {idx}: {end}>{duration}")
        if start < prev_end - 30:
            errors.append(f"overlap at {idx}")
        dur = end - start
        covered += max(0, dur)
        soft_min = min(min_word_ms, max(60, _letter_count(text) * 40))
        if dur < soft_min:
            very_short += 1
            if dur < 40:
                errors.append(f"collapsed at {idx}: {dur}ms")
        if dur > max_word_ms:
            errors.append(f"too_long at {idx}: {dur}ms")
        if prev_end >= 0:
            gap = start - prev_end
            prev_text = words[i - 1].get("text", "")
            if gap > max_non_waqf_gap_ms and not _has_waqf(prev_text):
                errors.append(f"large_gap before {idx}: {gap}ms")
            elif gap > 2800:
                errors.append(f"huge_gap before {idx}: {gap}ms")
        prev_end = end
        if "score" in w and w["score"] is not None:
            scores.append(float(w["score"]))

    first_start = int(words[0]["startMs"]) if words else 0
    last_end = int(words[-1]["endMs"]) if words else 0
    if words and duration > 0:
        edge = max(3000, int(duration * 0.25))
        leading = first_start
        trailing = max(0, duration - last_end)
        # Leading silence alone is common (Bismillah intros). Flag a shifted
        # pocket only when the alignment is also cut off before the end.
        if leading > edge and trailing > edge:
            errors.append("late_start")
        if last_end < duration - edge:
            errors.append("early_end")

    frac_short = very_short / max(len(words), 1)
    if frac_short > max_very_short_frac:
        errors.append(f"too_many_short:{very_short}/{len(words)}")

    # Measure coverage of the aligned span so file-level intro/outro silence
    # does not fail a tight, sequential word timeline.
    span = max(last_end - first_start, 1) if words else 1
    coverage = covered / span
    if coverage < min_coverage:
        errors.append(f"low_coverage:{coverage:.3f}")

    if min_mean_score is not None and scores:
        mean = sum(scores) / len(scores)
        if mean < min_mean_score:
            errors.append(f"low_mean_score:{mean:.4f}")

    return ValidationResult(len(errors) == 0, errors)