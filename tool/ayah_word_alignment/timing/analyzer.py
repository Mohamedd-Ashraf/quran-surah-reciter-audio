"""Per-ayah attach: duration, Madd candidates, stretch, verse stats, extension.

The only feature gate is ``config.enabled``. When False this module must not
be called for work — ``attach_ayah`` still returns the input unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import TimingAnalysisConfig
from .extension import classify_extension, duration_ratio, extension_confidence
from .madd import madd_payload
from .stats import mean_ms, median_ms
from .stretch import stretch_payload

_WORD_EXTRA_KEYS = (
    "durationMs",
    "madd",
    "stretch",
    "baselineMs",
    "baselineSource",
    "durationRatio",
    "extensionLevel",
    "confidence",
)


def word_duration_ms(word: dict[str, Any]) -> int | None:
    if "startMs" not in word or "endMs" not in word:
        return None
    try:
        start = int(word["startMs"])
        end = int(word["endMs"])
    except (TypeError, ValueError):
        return None
    if end > start:
        return end - start
    return None


def _strip_word_analysis(word: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in word.items() if k not in _WORD_EXTRA_KEYS}


def _score_of(word: dict[str, Any]) -> float | None:
    if "score" not in word or word["score"] is None:
        return None
    try:
        return float(word["score"])
    except (TypeError, ValueError):
        return None


def apply_extension(
    word: dict[str, Any],
    *,
    baseline_ms: float | None,
    baseline_source: str | None,
    sample_count: int | None,
    config: TimingAnalysisConfig,
) -> None:
    actual = word.get("durationMs")
    if not isinstance(actual, int):
        actual = word_duration_ms(word)
    ratio = duration_ratio(actual if isinstance(actual, int) else None, baseline_ms)
    has_candidate = bool(word.get("madd", {}).get("hasCandidate")) if isinstance(word.get("madd"), dict) else False
    if baseline_ms is not None:
        word["baselineMs"] = round(float(baseline_ms), 1)
        if baseline_source:
            word["baselineSource"] = baseline_source
    else:
        word.pop("baselineMs", None)
        word.pop("baselineSource", None)
    if ratio is not None:
        word["durationRatio"] = ratio
    else:
        word.pop("durationRatio", None)
    level = classify_extension(ratio, config, has_candidate=has_candidate)
    if level is not None:
        word["extensionLevel"] = level
    else:
        word.pop("extensionLevel", None)
    conf = extension_confidence(
        score=_score_of(word),
        sample_count=sample_count,
        source=baseline_source,
        has_candidate=has_candidate,
        ratio=ratio,
    )
    if conf is not None:
        word["confidence"] = conf
    else:
        word.pop("confidence", None)


def attach_ayah(
    data: dict[str, Any],
    config: TimingAnalysisConfig,
    *,
    baselines: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Add timing/Madd/stretch fields. No-op when ``config.enabled`` is False."""
    if not config.enabled:
        return data

    words_in = data.get("words")
    if not isinstance(words_in, list):
        return data

    out = dict(data)
    new_words: list[dict[str, Any]] = []
    durations: list[int] = []
    duration_by_index: list[int | None] = []

    for raw in words_in:
        if not isinstance(raw, dict):
            new_words.append(raw)
            duration_by_index.append(None)
            continue
        word = _strip_word_analysis(raw)
        dur = word_duration_ms(word)
        if dur is not None:
            word["durationMs"] = dur
            durations.append(dur)
        duration_by_index.append(dur)
        text = str(word.get("text") or "")
        madd = madd_payload(text)
        if madd is not None:
            word["madd"] = madd
        madd_idx = [c["clusterIndex"] for c in (madd or {}).get("candidates", [])]
        stretch = stretch_payload(
            text,
            madd_cluster_indexes=madd_idx,
            max_recommended=config.max_tatweel_per_position,
        )
        if stretch is not None:
            word["stretch"] = stretch
        new_words.append(word)

    verse_avg = mean_ms(durations)
    verse_med = median_ms(durations)
    timing = dict(out.get("timing") or {}) if isinstance(out.get("timing"), dict) else {}
    if verse_avg is not None:
        timing["verseAverageDurationMs"] = verse_avg
    if verse_med is not None:
        timing["verseMedianDurationMs"] = verse_med

    others_needed = config.min_verse_baseline_others
    for i, word in enumerate(new_words):
        if not isinstance(word, dict):
            continue
        others = [d for j, d in enumerate(duration_by_index) if j != i and d is not None]
        baseline = None
        source = None
        sample_n = None
        if baselines:
            # Caller (aggregator) supplies a resolved baseline.
            baseline = baselines.get("per_word", [None] * len(new_words))[i]
            source = (baselines.get("sources") or [None] * len(new_words))[i]
            sample_n = (baselines.get("counts") or [None] * len(new_words))[i]
        elif len(others) >= others_needed:
            baseline = median_ms(others)
            source = "verse"
            sample_n = len(others)
        apply_extension(
            word,
            baseline_ms=baseline,
            baseline_source=source,
            sample_count=sample_n,
            config=config,
        )

    out["words"] = new_words
    if timing:
        out["timing"] = timing
    meta = dict(out.get("meta") or {}) if isinstance(out.get("meta"), dict) else {}
    meta["timingAnalysis"] = {"enabled": True}
    out["meta"] = meta
    return out


def write_json(data: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
