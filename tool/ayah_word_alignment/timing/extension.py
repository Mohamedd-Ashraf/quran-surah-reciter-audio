"""Observed timing-extension classification.

This is a duration-ratio signal for Reels styling, not Tajweed Madd detection.
"""

from __future__ import annotations

from .config import TimingAnalysisConfig

_SOURCE_WEIGHT = {
    "word": 1.0,
    "verse": 0.7,
    "surah": 0.5,
    "reciter": 0.35,
}


def duration_ratio(actual_ms: int | None, baseline_ms: float | None) -> float | None:
    if actual_ms is None or baseline_ms is None or baseline_ms <= 0:
        return None
    return round(actual_ms / baseline_ms, 3)


def classify_extension(
    ratio: float | None,
    config: TimingAnalysisConfig,
    *,
    has_candidate: bool,
) -> str | None:
    if ratio is None or not has_candidate:
        return None
    slightly = config.extension_ratios.get("slightlyExtended", 1.4)
    extended = config.extension_ratios.get("extended", 1.8)
    highly = config.extension_ratios.get("highlyExtended", 2.5)
    if ratio < slightly:
        return "normal"
    if ratio < extended:
        return "slightlyExtended"
    if ratio < highly:
        return "extended"
    return "highlyExtended"


def extension_confidence(
    *,
    score: float | None,
    sample_count: int | None,
    source: str | None,
    has_candidate: bool,
    ratio: float | None,
) -> float | None:
    if not has_candidate or ratio is None or score is None or source is None:
        return None
    # CTC log-prob: closer to 0 is better. Clamp typical range [-8, 0] → [0, 1].
    score_c = max(0.0, min(1.0, (float(score) + 8.0) / 8.0))
    source_c = _SOURCE_WEIGHT.get(source, 0.3)
    n = 0 if sample_count is None else max(0, int(sample_count))
    sample_c = min(1.0, n / 8.0)
    return round(0.4 * score_c + 0.35 * source_c + 0.25 * sample_c, 3)
