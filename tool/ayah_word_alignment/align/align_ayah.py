"""CTC forced alignment of one ayah MP3 against known Quran words."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "jonatasgrosman/wav2vec2-large-xlsr-53-arabic"


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

    def to_json_dict(self) -> dict[str, Any]:
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
        }


class AlignmentEngine:
    """Loads the CTC model once and aligns many ayahs."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str | None = None,
        batch_size: int = 4,
    ) -> None:
        import torch
        from ctc_forced_aligner import load_alignment_model

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.model_name = model_name
        self.batch_size = batch_size
        dtype = torch.float16 if device == "cuda" else torch.float32
        logger.info("Loading alignment model %s on %s", model_name, device)
        self.model, self.tokenizer = load_alignment_model(
            device,
            model_path=model_name,
            dtype=dtype,
        )

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
        from ctc_forced_aligner import (
            generate_emissions,
            get_alignments,
            get_spans,
            load_audio,
            postprocess_results,
            preprocess_text,
        )

        from .normalize import join_aligner_words

        audio_path = Path(audio_path)
        audio_file = audio_path.name
        result = AlignResult(
            surah=surah,
            ayah=ayah,
            reciter_id=reciter_id,
            audio_file=audio_file,
            duration_ms=0,
        )
        if not canonical_words:
            result.ok = False
            result.error = "empty_word_list"
            return result

        try:
            waveform = load_audio(str(audio_path), self.model.dtype, self.model.device)
            # waveform is 1-D samples at 16kHz
            import torch

            n_samples = int(waveform.numel()) if hasattr(waveform, "numel") else len(waveform)
            duration_ms = int(round(n_samples / 16000.0 * 1000))
            result.duration_ms = duration_ms

            text = join_aligner_words(canonical_words, keep_diacritics=keep_diacritics)
            emissions, stride = generate_emissions(
                self.model, waveform, batch_size=self.batch_size
            )
            # Native Arabic vocab model — do not romanize
            tokens_starred, text_starred = preprocess_text(
                text,
                romanize=False,
                language="ara",
            )
            segments, scores, blank_token = get_alignments(
                emissions,
                tokens_starred,
                self.tokenizer,
            )
            spans = get_spans(tokens_starred, segments, blank_token)
            word_timestamps = postprocess_results(
                text_starred, spans, stride, scores
            )

            # word_timestamps: list of {text, start, end, score?}
            timed = list(word_timestamps)
            if len(timed) != len(canonical_words):
                # Retry with diacritics flip once
                if not keep_diacritics:
                    return self.align(
                        audio_path,
                        canonical_words,
                        surah=surah,
                        ayah=ayah,
                        reciter_id=reciter_id,
                        keep_diacritics=True,
                    )
                result.ok = False
                result.error = (
                    f"word_count_mismatch aligned={len(timed)} "
                    f"expected={len(canonical_words)}"
                )
                return result

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

            # Fix tiny overlaps
            for i in range(len(words) - 1):
                if words[i].end_ms > words[i + 1].start_ms:
                    mid = (words[i].end_ms + words[i + 1].start_ms) // 2
                    words[i].end_ms = mid
                    words[i + 1].start_ms = mid
                    if words[i].end_ms <= words[i].start_ms:
                        words[i].end_ms = words[i].start_ms + 1

            result.words = words
            result.ok = True
            return result
        except Exception as e:  # noqa: BLE001 — surface as align failure
            logger.exception("align failed %s:%s", surah, ayah)
            result.ok = False
            result.error = f"exception:{type(e).__name__}:{e}"
            return result


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
