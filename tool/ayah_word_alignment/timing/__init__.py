"""Optional post-alignment timing, Madd-candidate, and stretch metadata.

This package does **not** certify Tajweed. It emits three separate signals:

1. Madd candidate — orthographic/phonetic possibility in vocalized text
2. Observed extension — word duration vs a reciter baseline
3. Safe stretch positions — visual Tatweel insertion boundaries

Canonical Quranic ``text`` is never rewritten. Gated by one flag:
``TimingAnalysisConfig.enabled`` (``enable_timing_analysis``).
"""

from .config import TimingAnalysisConfig
from .analyzer import attach_ayah, write_json
from .aggregator import enrich_reciter

__all__ = [
    "TimingAnalysisConfig",
    "attach_ayah",
    "write_json",
    "enrich_reciter",
]
