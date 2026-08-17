# Ayah word-level forced alignment (EveryAyah)

Unified architecture for **all** EveryAyah reciters in `kEveryAyahFolders`.

## Identity (one string everywhere)

| Layer | Uses |
|-------|------|
| App picker / `ReelProject.reciterId` | `ar.alafasy`, `ar.alijaber`, `ar.husary`, … |
| EveryAyah audio | `https://everyayah.com/data/{folder}/{SSSAAA}.mp3` |
| Word alignment JSON | `word-alignment/{reciterId}/{surahNumber}/{ayahNumber}.json` |
| Availability catalog | `word-alignment/_index.json` (one file; rebuilt on every sync) |
| Pipeline `reciters.yaml` | same keys as `kEveryAyahFolders` |

Examples:

```text
word-alignment/_index.json
word-alignment/ar.alijaber/2/255.json
word-alignment/ar.husary/1/1.json
word-alignment/ar.minshawi/114/6.json
```

Keep yaml in sync:

```bash
python tool/ayah_word_alignment/scripts/sync_reciters_from_dart.py
```

## Public distribution (repo tree, not Releases)

CDN (app):

```text
https://cdn.jsdelivr.net/gh/Mohamedd-Ashraf/quran-surah-reciter-audio@main/word-alignment/{reciterId}/{surahNumber}/{ayahNumber}.json
https://cdn.jsdelivr.net/gh/Mohamedd-Ashraf/quran-surah-reciter-audio@main/word-alignment/_index.json
```

Fallback: `raw.githubusercontent.com/.../main/...`

`_index.json` shape:

```json
{
  "schemaVersion": 1,
  "reciters": [
    { "reciterId": "ar.alijaber", "ayahJsonCount": 1234 }
  ]
}
```

Missing ayah file / unknown reciter → Flutter returns `null` → word-count chunk timing (reels) or an honest WBW error (mushaf).

## Flutter wiring

- `lib/core/audio/word_alignment/` — shared by reel creator + mushaf WBW
- `ReelReciterContract` — shared URLs + normalize for every `ar.*` reciter
- `WordAlignmentService` — per-ayah fetch/cache + cached `listAvailableReciters()`
- Preview + Export both use `project.reciterId`
- Mushaf WBW can use legacy QuranCDN Mishary clips or an alignment reciter from `_index.json`

## Local smoke

```bash
cd tool/ayah_word_alignment
python -m unittest tests.test_tokenize tests.test_refine tests.test_strategies \
  tests.test_madd tests.test_stretch tests.test_timing_stats \
  tests.test_timing_analyzer tests.test_timing_flag \
  tests.test_validate tests.test_merge_reports -v
```

## Optional timing / Madd / stretch analysis

Gated by **one** flag: `enable_timing_analysis` (yaml + `--enable-timing-analysis` / `--no-timing-analysis`, GHA input, **default on**).

When **disabled**, ayah JSON is unchanged: `{index, text, startMs, endMs, score?}`. No Madd, stretch, stats, or extra artifacts.

When **enabled**, the shard attaches lightweight metadata after CTC (no extra model, no VAD, no audio re-decode). The merge job then computes reciter/word/surah baselines in two passes over already-written JSON (~seconds vs 45–90 min alignment).

Three separate concepts (not Tajweed certification):

| Field | Meaning |
|-------|---------|
| `madd.candidates[]` | Orthographic/phonetic Madd *possibility* in vocalized text (`clusterIndex` + `reason`) |
| `durationRatio` / `extensionLevel` | Observed timing vs the best available baseline |
| `stretch.positions[]` | Safe Tatweel (`U+0640`) insertion after a grapheme cluster (`afterClusterIndex`) |

Canonical `text` is never rewritten. Shadda-yeh after kasra (e.g. iyyaka) is `ya_madd` with reason `kasra_before_shadda_ya` — Unicode keeps one cluster; the detector models the doubled consonant phonetically.

`afterClusterIndex` is 0-based and always a complete grapheme cluster (base + combining marks). The Reels renderer should apply Tatweel only in Unicode/stylized fonts, not QCF mushaf glyphs.

**Silence:** published `startMs`/`endMs` absorb most gaps in `refine.py`. Pause fields are not emitted.

**schemaVersion** stays `1` (additive fields). Flutter currently ignores unknown keys.

Disable: GHA `enable_timing_analysis: false` or `python runner/run_shard.py ... --no-timing-analysis`.

## GitHub Actions

**Ayah Word Alignment** workflow commits nested JSON under `word-alignment/{reciterId}/` with `[skip ci]`.

## Model

`jonatasgrosman/wav2vec2-large-xlsr-53-arabic` + MMS multi-strategy via ctc-forced-aligner.


## Align modes (speed vs quality)

| Mode | Behavior | Full mushaf @ 19 shards |
|------|----------|-------------------------|
| `balanced` (default) | MMS-first + early-exit at excellent quality; emissions cached per model | ~45–90 min |
| `fast` | Same order, earlier exit threshold; skips rare diacritic strategy | ~30–60 min |
| `max` | Try every strategy every ayah (no early-exit) | ~2–4 h |

Optimizations: best-first strategy order, quality early-exit, encoder emissions cache across strategies, model warmup at shard start.

Dispatch tip: `surahs=1-114`, `shard_count=19`, `align_mode=balanced`, `force_rebuild=false`.