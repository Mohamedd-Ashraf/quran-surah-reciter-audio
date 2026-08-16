# Benchmarks

Fill these from real CTC runs on GitHub Actions (Python 3.11, CPU ubuntu-latest).

## Placeholder estimates (pre-measurement)

| Scope | Estimate |
|-------|----------|
| Short ayah (1:1) | 1-3 s |
| Long ayah (2:255) | 10-40 s |
| Surah 112-114 | a few minutes |
| Test set 1,2,112-114 @ 4 shards | tens of minutes wall |
| Full Quran @ 19 Juz shards | ~25-45 min wall / reciter |

## How to measure

On GHA or local Python 3.11 + ffmpeg + torch, run `run_shard.py` on surah 1 with `--max-ayahs 3` and record wall time from logs into this file.