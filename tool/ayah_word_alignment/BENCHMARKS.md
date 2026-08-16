# Benchmarks

Measured on GitHub Actions (`ubuntu-latest`, CPU, Python 3.11) unless noted.

## Calibration (2026-08-16)

| Case | Notes | Wall |
|------|-------|------|
| `ar.alijaber` 2:255 only (pre-opt, 5 strategies) | Align step ~2 min after setup | ~6 min total job |
| Per-strategy on ~51s ayah | ~20 s CPU each | — |

## Optimized EST (post early-exit + emissions cache)

| Scope | Mode | Shards | EST wall |
|-------|------|--------|----------|
| Short ayah | balanced (1 strategy if q≥32) | — | ~3–8 s |
| Long ayah (2:255) | balanced early-exit | — | ~25–45 s |
| Full mushaf (6236 ayahs) | **balanced** | **19** | **~45–90 min** |
| Full mushaf | **fast** | **19** | **~30–60 min** |
| Full mushaf | max (no early-exit) | 19 | ~2–4 h |
| Full mushaf | balanced | 4 | ~3–6 h (timeout risk) |

Assumes HF model cache hits and resume skips existing JSON.

## Recommended full-Quran dispatch

```
reciter_id: ar.alafasy   # or any EveryAyah id
surahs: 1-114
shard_count: 19
align_mode: balanced     # or fast for throughput
force_rebuild: false
```

## How to re-measure

On GHA, run `only_ayahs: 2:255` with `align_mode: balanced` and record:
- strategies tried / early-exit from logs
- wall time of the **Run shard** step