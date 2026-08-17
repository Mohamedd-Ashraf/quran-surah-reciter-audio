"""Single configuration object for the optional timing/Madd/stretch layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DEFAULT_EXTENSION_RATIOS = {
    "slightlyExtended": 1.4,
    "extended": 1.8,
    "highlyExtended": 2.5,
}


@dataclass(frozen=True)
class TimingAnalysisConfig:
    """One gate: ``enabled``. When False, callers must skip all analysis."""

    enabled: bool = True
    min_word_baseline_samples: int = 3
    min_surah_baseline_words: int = 8
    min_verse_baseline_others: int = 2
    min_reciter_baseline_words: int = 8
    extension_ratios: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_EXTENSION_RATIOS)
    )
    max_tatweel_per_position: int = 4

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> TimingAnalysisConfig:
        data = raw or {}
        nested = data.get("timing_analysis") if isinstance(data.get("timing_analysis"), dict) else {}
        enabled = data.get("enable_timing_analysis")
        if enabled is None:
            enabled = nested.get("enabled", True)
        ratios = dict(DEFAULT_EXTENSION_RATIOS)
        src_ratios = nested.get("extension_ratios") or data.get("extension_ratios")
        if isinstance(src_ratios, dict):
            for k, v in src_ratios.items():
                try:
                    ratios[str(k)] = float(v)
                except (TypeError, ValueError):
                    continue
        return cls(
            enabled=bool(enabled),
            min_word_baseline_samples=int(
                nested.get("min_word_baseline_samples", cls.min_word_baseline_samples)
            ),
            min_surah_baseline_words=int(
                nested.get("min_surah_baseline_words", cls.min_surah_baseline_words)
            ),
            min_verse_baseline_others=int(
                nested.get("min_verse_baseline_others", cls.min_verse_baseline_others)
            ),
            min_reciter_baseline_words=int(
                nested.get("min_reciter_baseline_words", cls.min_reciter_baseline_words)
            ),
            extension_ratios=ratios,
            max_tatweel_per_position=int(
                nested.get("max_tatweel_per_position", cls.max_tatweel_per_position)
            ),
        )

    def with_enabled(self, enabled: bool) -> TimingAnalysisConfig:
        return TimingAnalysisConfig(
            enabled=enabled,
            min_word_baseline_samples=self.min_word_baseline_samples,
            min_surah_baseline_words=self.min_surah_baseline_words,
            min_verse_baseline_others=self.min_verse_baseline_others,
            min_reciter_baseline_words=self.min_reciter_baseline_words,
            extension_ratios=dict(self.extension_ratios),
            max_tatweel_per_position=self.max_tatweel_per_position,
        )
