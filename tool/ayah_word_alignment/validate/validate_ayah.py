"""Validate one ayah word-alignment JSON before publish."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
    min_mean_score: float | None = 0.05,
    max_word_ms: int = 12000,
    min_word_ms: int = 30,
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
        if dur < min_word_ms:
            errors.append(f"too_short at {idx}: {dur}ms")
        if dur > max_word_ms:
            errors.append(f"too_long at {idx}: {dur}ms")
        prev_end = end
        if "score" in w and w["score"] is not None:
            scores.append(float(w["score"]))

    if words:
        first_start = int(words[0]["startMs"])
        last_end = int(words[-1]["endMs"])
        if duration > 0 and first_start > max(3000, int(duration * 0.25)):
            errors.append("late_start")
        if duration > 0 and last_end < duration - max(3000, int(duration * 0.25)):
            errors.append("early_end")

    if min_mean_score is not None and scores:
        mean = sum(scores) / len(scores)
        if mean < min_mean_score:
            errors.append(f"low_mean_score:{mean:.4f}")

    return ValidationResult(len(errors) == 0, errors)
