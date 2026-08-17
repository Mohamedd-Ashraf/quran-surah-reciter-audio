"""Reciter-level two-pass baseline enrichment.

Collect durations once, then rewrite each ayah JSON. Does not rescan the
dataset per word and does not touch audio or models.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .analyzer import attach_ayah, write_json
from .clusters import baseline_key
from .config import TimingAnalysisConfig
from .stats import mean_ms, median_ms


def _iter_ayah_files(root: Path) -> list[Path]:
    files = [
        p
        for p in sorted(root.rglob("*.json"))
        if p.name != "_meta.json" and not p.name.startswith("_")
    ]
    return files


def _load(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return None
    return raw if isinstance(raw, dict) else None


def enrich_reciter(
    alignment_root: str | Path,
    config: TimingAnalysisConfig,
) -> int:
    """Enrich all ayah JSON under ``alignment_root``. Returns files written.

    No-op when ``config.enabled`` is False.
    """
    if not config.enabled:
        return 0

    root = Path(alignment_root)
    if not root.is_dir():
        return 0

    files = _iter_ayah_files(root)
    loaded: list[tuple[Path, dict[str, Any]]] = []
    by_key: dict[str, list[int]] = defaultdict(list)
    by_surah: dict[int, list[int]] = defaultdict(list)
    global_durs: list[int] = []

    for path in files:
        data = _load(path)
        if data is None:
            continue
        if not (data.get("meta") or {}).get("timingAnalysis", {}).get("enabled"):
            data = attach_ayah(data, config)
        loaded.append((path, data))
        surah = int(data.get("surah") or 0)
        for w in data.get("words") or []:
            if not isinstance(w, dict):
                continue
            dur = w.get("durationMs")
            if not isinstance(dur, int):
                continue
            key = baseline_key(str(w.get("text") or ""))
            by_key[key].append(dur)
            if surah:
                by_surah[surah].append(dur)
            global_durs.append(dur)

    global_med = (
        median_ms(global_durs)
        if len(global_durs) >= config.min_reciter_baseline_words
        else None
    )
    surah_stats: dict[int, tuple[float | None, float | None]] = {}
    for s, vals in by_surah.items():
        if len(vals) >= config.min_surah_baseline_words:
            surah_stats[s] = (mean_ms(vals), median_ms(vals))
        else:
            surah_stats[s] = (None, None)

    written = 0
    min_word = config.min_word_baseline_samples
    for path, data in loaded:
        surah = int(data.get("surah") or 0)
        words = data.get("words") or []
        per_word: list[float | None] = []
        sources: list[str | None] = []
        counts: list[int | None] = []

        for i, w in enumerate(words):
            if not isinstance(w, dict) or not isinstance(w.get("durationMs"), int):
                per_word.append(None)
                sources.append(None)
                counts.append(None)
                continue
            key = baseline_key(str(w.get("text") or ""))
            same = list(by_key.get(key) or [])
            # Leave-one-out: drop one copy of this duration.
            others = list(same)
            try:
                others.remove(w["durationMs"])
            except ValueError:
                pass
            baseline: float | None = None
            source: str | None = None
            n: int | None = None
            if len(others) >= min_word:
                baseline = median_ms(others)
                source = "word"
                n = len(others)
            else:
                verse_others = [
                    d
                    for j, ww in enumerate(words)
                    if j != i
                    and isinstance(ww, dict)
                    and isinstance(ww.get("durationMs"), int)
                    for d in [ww["durationMs"]]
                ]
                if len(verse_others) >= config.min_verse_baseline_others:
                    baseline = median_ms(verse_others)
                    source = "verse"
                    n = len(verse_others)
                else:
                    s_avg, s_med = surah_stats.get(surah, (None, None))
                    if s_med is not None:
                        baseline = s_med
                        source = "surah"
                        n = len(by_surah.get(surah) or [])
                    elif global_med is not None:
                        baseline = global_med
                        source = "reciter"
                        n = len(global_durs)
            per_word.append(baseline)
            sources.append(source)
            counts.append(n)

        data = attach_ayah(
            data,
            config,
            baselines={
                "per_word": per_word,
                "sources": sources,
                "counts": counts,
            },
        )
        s_avg, s_med = surah_stats.get(surah, (None, None))
        timing = dict(data.get("timing") or {})
        if s_avg is not None:
            timing["surahAverageDurationMs"] = s_avg
        if s_med is not None:
            timing["surahMedianDurationMs"] = s_med
        if timing:
            data["timing"] = timing
        write_json(data, path)
        written += 1
    return written
