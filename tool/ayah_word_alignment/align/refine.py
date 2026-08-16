"""Post-process CTC word timings: expand collapses using energy + gaps."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .align_ayah import WordTiming

_WAQF = frozenset("\u06D6\u06D7\u06D8\u06D9\u06DA\u06DB\u06DC")


def has_waqf(text: str) -> bool:
    return any(c in _WAQF for c in text)


def target_min_ms(text: str) -> int:
    """Minimum plausible spoken duration from glyph count (no marks)."""
    letters = sum(1 for c in text if c.isalpha() or ("\u0600" <= c <= "\u06FF"))
    letters = max(1, letters)
    return min(900, max(120, letters * 55))


def _rms_frames(waveform, sample_rate: int = 16000, win_ms: int = 20):
    import numpy as np

    if hasattr(waveform, "detach"):
        x = waveform.detach().float().cpu().numpy().reshape(-1)
    else:
        x = np.asarray(waveform, dtype=np.float32).reshape(-1)
    win = max(1, int(sample_rate * win_ms / 1000))
    n = len(x) // win
    if n <= 0:
        return np.zeros(1, dtype=np.float32), win
    frames = x[: n * win].reshape(n, win)
    rms = np.sqrt(np.mean(frames * frames, axis=1) + 1e-12)
    return rms, win


def _best_window_ms(
    rms,
    win_samples: int,
    sample_rate: int,
    gap_start_ms: int,
    gap_end_ms: int,
    want_ms: int,
) -> tuple[int, int]:
    """Place a window of want_ms inside [gap_start, gap_end] at max energy."""
    import numpy as np

    gap_start_ms = max(0, gap_start_ms)
    gap_end_ms = max(gap_start_ms + 1, gap_end_ms)
    avail = gap_end_ms - gap_start_ms
    want_ms = min(want_ms, avail)
    if want_ms < 40:
        mid = (gap_start_ms + gap_end_ms) // 2
        return gap_start_ms, max(gap_start_ms + 1, mid)

    ms_per_frame = win_samples * 1000.0 / sample_rate
    f0 = int(gap_start_ms / ms_per_frame)
    f1 = int(gap_end_ms / ms_per_frame)
    f0 = max(0, min(f0, len(rms) - 1))
    f1 = max(f0 + 1, min(f1, len(rms)))
    win_frames = max(1, int(want_ms / ms_per_frame))
    if f1 - f0 <= win_frames:
        return gap_start_ms, gap_start_ms + want_ms

    best_i = f0
    best_e = -1.0
    for i in range(f0, f1 - win_frames + 1):
        e = float(np.sum(rms[i : i + win_frames]))
        if e > best_e:
            best_e = e
            best_i = i
    start = int(best_i * ms_per_frame)
    end = start + want_ms
    if end > gap_end_ms:
        end = gap_end_ms
        start = end - want_ms
    start = max(gap_start_ms, start)
    end = min(gap_end_ms, max(start + 1, end))
    return start, end


def refine_word_timings(
    words: list,
    duration_ms: int,
    waveform=None,
    sample_rate: int = 16000,
    short_ms: int = 100,
) -> list:
    """Return a new word list with collapses expanded into neighboring gaps."""
    if not words or duration_ms <= 0:
        return words

    out = [
        replace(w) if hasattr(w, "__dataclass_fields__") else w for w in words
    ]
    # Normalize type: WordTiming dataclass
    n = len(out)
    rms = None
    win_samples = 320
    if waveform is not None:
        rms, win_samples = _rms_frames(waveform, sample_rate)

    # Pass 1: energy-place collapsed words into surrounding silence
    for i in range(n):
        dur = out[i].end_ms - out[i].start_ms
        need = target_min_ms(out[i].text)
        if dur >= short_ms and dur >= need * 0.5:
            continue
        left = 0 if i == 0 else out[i - 1].end_ms
        right = duration_ms if i == n - 1 else out[i + 1].start_ms
        # Prefer the larger adjacent gap (where speech often leaked)
        gap_left = out[i].start_ms - left
        gap_right = right - out[i].end_ms
        if gap_left + gap_right + dur < need:
            # use full span between neighbors
            span0, span1 = left, right
        elif gap_right >= gap_left:
            span0, span1 = out[i].start_ms, right
        else:
            span0, span1 = left, out[i].end_ms
        if span1 - span0 < 40:
            continue
        want = min(need, span1 - span0)
        if rms is not None:
            s, e = _best_window_ms(
                rms, win_samples, sample_rate, span0, span1, want
            )
        else:
            mid = (span0 + span1) // 2
            s = max(span0, mid - want // 2)
            e = min(span1, s + want)
            s = max(span0, e - want)
        out[i].start_ms = s
        out[i].end_ms = max(s + 1, e)

    # Pass 2: expand remaining short words into leftover gaps
    for i in range(n):
        need = target_min_ms(out[i].text)
        dur = out[i].end_ms - out[i].start_ms
        if dur >= need:
            continue
        left = 0 if i == 0 else out[i - 1].end_ms
        right = duration_ms if i == n - 1 else out[i + 1].start_ms
        room_l = out[i].start_ms - left
        room_r = right - out[i].end_ms
        deficit = need - dur
        take_l = min(room_l, deficit // 2)
        take_r = min(room_r, deficit - take_l)
        take_l = min(room_l, deficit - take_r)
        out[i].start_ms -= take_l
        out[i].end_ms += take_r

    # Pass 3: absorb moderate internal gaps (not after waqf) into neighbors
    for i in range(n - 1):
        gap = out[i + 1].start_ms - out[i].end_ms
        if gap <= 250:
            continue
        if has_waqf(out[i].text):
            # keep a pause, but cap extreme holes by trimming pause to 1200ms
            if gap > 1200:
                keep = 900
                extra = gap - keep
                out[i].end_ms += extra // 2
                out[i + 1].start_ms -= extra - extra // 2
            continue
        # split silence into both words
        out[i].end_ms += gap // 2
        out[i + 1].start_ms = out[i].end_ms

    # Pass 4: ensure monotonic non-empty spans
    out[0].start_ms = max(0, out[0].start_ms)
    for i in range(n - 1):
        if out[i].end_ms <= out[i].start_ms:
            out[i].end_ms = out[i].start_ms + 1
        if out[i].end_ms > out[i + 1].start_ms:
            mid = (out[i].end_ms + out[i + 1].start_ms) // 2
            out[i].end_ms = mid
            out[i + 1].start_ms = mid
        if out[i].end_ms <= out[i].start_ms:
            out[i].end_ms = out[i].start_ms + 1
    out[-1].end_ms = max(out[-1].start_ms + 1, min(duration_ms, out[-1].end_ms))
    if out[-1].end_ms < duration_ms and duration_ms - out[-1].end_ms < 800:
        out[-1].end_ms = duration_ms
    return out


def timing_quality(words: list, duration_ms: int) -> float:
    """Higher is better. Used to pick among alignment strategies."""
    if not words or duration_ms <= 0:
        return -1e9
    short = 0
    very_short = 0
    gaps_bad = 0
    covered = 0
    for i, w in enumerate(words):
        dur = w.end_ms - w.start_ms
        covered += max(0, dur)
        need = target_min_ms(w.text)
        if dur < 80:
            very_short += 1
        if dur < need * 0.45:
            short += 1
        if i + 1 < len(words):
            gap = words[i + 1].start_ms - w.end_ms
            if gap > 1500 and not has_waqf(w.text):
                gaps_bad += 1
            elif gap > 2500:
                gaps_bad += 1
    coverage = covered / duration_ms
    scores = [w.score for w in words if getattr(w, "score", None) is not None]
    mean_score = sum(scores) / len(scores) if scores else -5.0
    # mean_score is log-prob sum (negative); closer to 0 is better
    return (
        coverage * 40.0
        - very_short * 8.0
        - short * 3.0
        - gaps_bad * 4.0
        + max(-8.0, mean_score) * 0.5
    )