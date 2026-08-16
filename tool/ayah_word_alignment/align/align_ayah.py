"""CTC forced alignment of one ayah MP3 against known Quran words."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .strategies import (
    DEFAULT_ALIGN_MODE,
    DEFAULT_MODEL,
    MMS_MODEL,
    early_exit_quality,
    normalize_align_mode,
    should_early_exit,
    strategies_for_mode,
    warmup_models,
)

logger = logging.getLogger(__name__)

# Re-export for callers / tests
__all__ = [
    "WordTiming",
    "AlignResult",
    "AlignmentEngine",
    "align_ayah_file",
    "write_alignment_json",
    "DEFAULT_MODEL",
    "MMS_MODEL",
]


@dataclass
class WordTiming:
    index: int  # 1-based
    text: str  # canonical
    start_ms: int
    end_ms: int
    score: float | None = None


@dataclass
class AlignResult:
    surah: int
    ayah: int
    reciter_id: str
    audio_file: str
    duration_ms: int
    words: list[WordTiming] = field(default_factory=list)
    ok: bool = True
    error: str | None = None
    strategy: str | None = None
    quality: float | None = None
    align_mode: str | None = None
    strategies_tried: int = 0
    early_exit: bool = False

    def to_json_dict(self) -> dict[str, Any]:
        meta: dict[str, Any] = {}
        if self.strategy:
            meta["strategy"] = self.strategy
            meta["quality"] = (
                round(self.quality, 3) if self.quality is not None else None
            )
            meta["alignMode"] = self.align_mode
            meta["strategiesTried"] = self.strategies_tried
            meta["earlyExit"] = self.early_exit
        return {
            "schemaVersion": 1,
            "reciterId": self.reciter_id,
            "surah": self.surah,
            "ayah": self.ayah,
            "audioFile": self.audio_file,
            "durationMs": self.duration_ms,
            "words": [
                {
                    "index": w.index,
                    "text": w.text,
                    "startMs": w.start_ms,
                    "endMs": w.end_ms,
                    **({"score": round(w.score, 4)} if w.score is not None else {}),
                }
                for w in self.words
            ],
            **({"meta": meta} if meta else {}),
        }


class AlignmentEngine:
    """Loads CTC model(s) and aligns ayahs with mode-aware strategy search."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str | None = None,
        batch_size: int = 4,
        align_mode: str = DEFAULT_ALIGN_MODE,
    ) -> None:
        import torch

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.primary_model_name = model_name
        self.batch_size = batch_size
        self.align_mode = normalize_align_mode(align_mode)
        self._models: dict[str, tuple[Any, Any]] = {}
        # Per-ayah emissions cache: model_name -> (emissions, stride)
        self._emissions: dict[str, tuple[Any, Any]] = {}

    def warmup(self) -> None:
        """Load models used by the current mode once (avoids mid-shard stalls)."""
        for name in warmup_models(self.align_mode):
            self._load_model(name)

    def _load_model(self, model_name: str):
        import torch
        from ctc_forced_aligner import load_alignment_model

        if model_name in self._models:
            return self._models[model_name]
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        logger.info("Loading alignment model %s on %s", model_name, self.device)
        model, tokenizer = load_alignment_model(
            self.device,
            model_path=model_name,
            dtype=dtype,
        )
        self._models[model_name] = (model, tokenizer)
        return model, tokenizer

    def _emissions_for(self, model_name: str, waveform):
        """Cache encoder emissions per model within one ayah (big CPU win)."""
        from ctc_forced_aligner import generate_emissions

        cached = self._emissions.get(model_name)
        if cached is not None:
            return cached
        model, _ = self._load_model(model_name)
        emissions, stride = generate_emissions(
            model, waveform, batch_size=self.batch_size
        )
        self._emissions[model_name] = (emissions, stride)
        return emissions, stride

    def _align_once(
        self,
        waveform,
        canonical_words: list[str],
        *,
        model_name: str,
        romanize: bool,
        keep_diacritics: bool,
        star_frequency: str,
        merge_threshold: float,
    ) -> list[WordTiming] | None:
        from ctc_forced_aligner import (
            get_alignments,
            get_spans,
            postprocess_results,
            preprocess_text,
        )

        from .normalize import join_aligner_words

        _, tokenizer = self._load_model(model_name)
        text = join_aligner_words(canonical_words, keep_diacritics=keep_diacritics)
        emissions, stride = self._emissions_for(model_name, waveform)
        tokens_starred, text_starred = preprocess_text(
            text,
            romanize=romanize,
            language="ara",
            split_size="word",
            star_frequency=star_frequency,
        )
        segments, scores, blank_token = get_alignments(
            emissions,
            tokens_starred,
            tokenizer,
        )
        spans = get_spans(tokens_starred, segments, blank_token)
        word_timestamps = postprocess_results(
            text_starred, spans, stride, scores, merge_threshold
        )
        timed = list(word_timestamps)
        if len(timed) != len(canonical_words):
            return None

        n_samples = int(waveform.numel()) if hasattr(waveform, "numel") else len(waveform)
        duration_ms = int(round(n_samples / 16000.0 * 1000))
        words: list[WordTiming] = []
        for i, (canon, tw) in enumerate(zip(canonical_words, timed)):
            start_s = float(tw.get("start", tw.get("start_time", 0)))
            end_s = float(tw.get("end", tw.get("end_time", 0)))
            score = tw.get("score")
            start_ms = max(0, int(round(start_s * 1000)))
            end_ms = max(start_ms + 1, int(round(end_s * 1000)))
            end_ms = min(end_ms, duration_ms if duration_ms > 0 else end_ms)
            words.append(
                WordTiming(
                    index=i + 1,
                    text=canon,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    score=float(score) if score is not None else None,
                )
            )
        for i in range(len(words) - 1):
            if words[i].end_ms > words[i + 1].start_ms:
                mid = (words[i].end_ms + words[i + 1].start_ms) // 2
                words[i].end_ms = mid
                words[i + 1].start_ms = mid
                if words[i].end_ms <= words[i].start_ms:
                    words[i].end_ms = words[i].start_ms + 1
        return words

    def align(
        self,
        audio_path: str | Path,
        canonical_words: list[str],
        *,
        surah: int,
        ayah: int,
        reciter_id: str,
        keep_diacritics: bool = False,
    ) -> AlignResult:
        from ctc_forced_aligner import load_audio

        from .refine import refine_word_timings, timing_quality

        _ = keep_diacritics  # per-strategy flag wins
        audio_path = Path(audio_path)
        audio_file = audio_path.name
        result = AlignResult(
            surah=surah,
            ayah=ayah,
            reciter_id=reciter_id,
            audio_file=audio_file,
            duration_ms=0,
            align_mode=self.align_mode,
        )
        if not canonical_words:
            result.ok = False
            result.error = "empty_word_list"
            return result

        try:
            # Prefer MMS dtype/device when mode leads with MMS (avoids reload mismatch).
            strategies = strategies_for_mode(self.align_mode)
            lead_model = strategies[0]["model"] if strategies else (
                self.primary_model_name or DEFAULT_MODEL
            )
            model, _ = self._load_model(lead_model)
            waveform = load_audio(str(audio_path), model.dtype, model.device)
            n_samples = (
                int(waveform.numel()) if hasattr(waveform, "numel") else len(waveform)
            )
            duration_ms = int(round(n_samples / 16000.0 * 1000))
            result.duration_ms = duration_ms

            # Fresh emissions cache per ayah
            self._emissions.clear()

            exit_q = early_exit_quality(self.align_mode)
            best_words = None
            best_q = -1e18
            best_name = None
            errors: list[str] = []
            tried = 0
            exited_early = False

            for strat in strategies:
                tried += 1
                try:
                    raw = self._align_once(
                        waveform,
                        canonical_words,
                        model_name=strat["model"],
                        romanize=strat["romanize"],
                        keep_diacritics=strat["keep_diacritics"],
                        star_frequency=strat["star_frequency"],
                        merge_threshold=strat["merge_threshold"],
                    )
                    if raw is None:
                        errors.append(f"{strat['name']}:word_count_mismatch")
                        continue
                    refined = refine_word_timings(
                        raw, duration_ms, waveform=waveform
                    )
                    q = timing_quality(refined, duration_ms)
                    logger.info(
                        "strategy %s quality=%.3f", strat["name"], q
                    )
                    if q > best_q:
                        best_q = q
                        best_words = refined
                        best_name = strat["name"]
                    if should_early_exit(q, exit_q):
                        exited_early = True
                        logger.info(
                            "early-exit %s quality=%.3f threshold=%s",
                            strat["name"],
                            q,
                            exit_q,
                        )
                        break
                except Exception as e:  # noqa: BLE001
                    errors.append(f"{strat['name']}:{type(e).__name__}:{e}")
                    logger.warning("strategy %s failed: %s", strat["name"], e)

            result.strategies_tried = tried
            result.early_exit = exited_early

            if best_words is None:
                result.ok = False
                result.error = "all_strategies_failed:" + ";".join(errors[:5])
                return result

            result.words = best_words
            result.strategy = best_name
            result.quality = best_q
            result.ok = True
            return result
        except Exception as e:  # noqa: BLE001
            logger.exception("align failed %s:%s", surah, ayah)
            result.ok = False
            result.error = f"exception:{type(e).__name__}:{e}"
            return result
        finally:
            self._emissions.clear()


def align_ayah_file(
    audio_path: str | Path,
    canonical_words: list[str],
    *,
    surah: int,
    ayah: int,
    reciter_id: str,
    engine: AlignmentEngine | None = None,
) -> AlignResult:
    eng = engine or AlignmentEngine()
    return eng.align(
        audio_path,
        canonical_words,
        surah=surah,
        ayah=ayah,
        reciter_id=reciter_id,
    )


def write_alignment_json(result: AlignResult, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.to_json_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )