"""Alignment strategy catalog + modes (speed vs quality).

Modes
-----
fast      — MMS-first, early-exit on good quality; best throughput for full mushaf
balanced  — all useful strategies, early-exit on excellent quality (default)
max       — always try every strategy; pick absolute best (slow, research/debug)
"""

from __future__ import annotations

from typing import Any

DEFAULT_MODEL = "jonatasgrosman/wav2vec2-large-xlsr-53-arabic"
MMS_MODEL = "MahmoudAshraf/mms-300m-1130-forced-aligner"

# Historical win order (Ayat al-Kursi + refine quality): MMS edges beat XLSR.
STRATEGY_DEFS: dict[str, dict[str, Any]] = {
    "mms_roman_edges": {
        "model": MMS_MODEL,
        "romanize": True,
        "keep_diacritics": False,
        "star_frequency": "edges",
        "merge_threshold": 0.0,
    },
    "xlsr_nodiac_segment": {
        "model": DEFAULT_MODEL,
        "romanize": False,
        "keep_diacritics": False,
        "star_frequency": "segment",
        "merge_threshold": 0.02,
    },
    "xlsr_nodiac_edges": {
        "model": DEFAULT_MODEL,
        "romanize": False,
        "keep_diacritics": False,
        "star_frequency": "edges",
        "merge_threshold": 0.0,
    },
    "mms_roman_segment": {
        "model": MMS_MODEL,
        "romanize": True,
        "keep_diacritics": False,
        "star_frequency": "segment",
        "merge_threshold": 0.02,
    },
    "xlsr_diac_edges": {
        "model": DEFAULT_MODEL,
        "romanize": False,
        "keep_diacritics": True,
        "star_frequency": "edges",
        "merge_threshold": 0.0,
    },
}

# quality from refine.timing_quality — coverage*40 is ~ceil; Kursi MMS ~38.7
MODE_CONFIG: dict[str, dict[str, Any]] = {
    "fast": {
        "strategy_names": [
            "mms_roman_edges",
            "xlsr_nodiac_segment",
            "xlsr_nodiac_edges",
            "mms_roman_segment",
        ],
        # Good enough to stop; still escalates if quality is mediocre.
        "early_exit_quality": 28.0,
        "warmup_models": [MMS_MODEL, DEFAULT_MODEL],
    },
    "balanced": {
        "strategy_names": [
            "mms_roman_edges",
            "xlsr_nodiac_segment",
            "xlsr_nodiac_edges",
            "mms_roman_segment",
            "xlsr_diac_edges",
        ],
        # Excellent — only skip remaining when timing looks strong.
        "early_exit_quality": 32.0,
        "warmup_models": [MMS_MODEL, DEFAULT_MODEL],
    },
    "max": {
        "strategy_names": [
            "mms_roman_edges",
            "xlsr_nodiac_segment",
            "xlsr_nodiac_edges",
            "mms_roman_segment",
            "xlsr_diac_edges",
        ],
        "early_exit_quality": None,
        "warmup_models": [MMS_MODEL, DEFAULT_MODEL],
    },
}

DEFAULT_ALIGN_MODE = "balanced"


def normalize_align_mode(mode: str | None) -> str:
    m = (mode or DEFAULT_ALIGN_MODE).strip().lower()
    if m not in MODE_CONFIG:
        raise ValueError(
            f"Unknown align_mode={mode!r}; expected one of {sorted(MODE_CONFIG)}"
        )
    return m


def strategies_for_mode(mode: str | None) -> list[dict[str, Any]]:
    """Return ordered strategy dicts (name + params) for the mode."""
    m = normalize_align_mode(mode)
    out: list[dict[str, Any]] = []
    for name in MODE_CONFIG[m]["strategy_names"]:
        base = STRATEGY_DEFS[name]
        out.append({"name": name, **base})
    return out


def early_exit_quality(mode: str | None) -> float | None:
    m = normalize_align_mode(mode)
    return MODE_CONFIG[m]["early_exit_quality"]


def warmup_models(mode: str | None) -> list[str]:
    m = normalize_align_mode(mode)
    return list(MODE_CONFIG[m]["warmup_models"])


def should_early_exit(quality: float, threshold: float | None) -> bool:
    if threshold is None:
        return False
    return quality >= threshold