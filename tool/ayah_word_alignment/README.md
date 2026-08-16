# Ayah word-level forced alignment (EveryAyah)

Unified architecture for **all** EveryAyah reciters in `kEveryAyahFolders`.

## Identity (one string everywhere)

| Layer | Uses |
|-------|------|
| App picker / `ReelProject.reciterId` | `ar.alafasy`, `ar.alijaber`, `ar.husary`, … |
| EveryAyah audio | `https://everyayah.com/data/{folder}/{SSSAAA}.mp3` |
| Word alignment JSON | `word-alignment/{reciterId}/{surahNumber}/{ayahNumber}.json` |
| Pipeline `reciters.yaml` | same keys as `kEveryAyahFolders` |

Examples:

```text
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
```

Fallback: `raw.githubusercontent.com/.../main/...`

Missing file / unknown reciter → Flutter returns `null` → word-count chunk timing.

## Flutter wiring

- `ReelReciterContract` — shared URLs + normalize for every `ar.*` reciter
- `WordAlignmentService` — per-ayah fetch/cache from the nested path
- Preview + Export both use `project.reciterId`

## Local smoke

```bash
cd tool/ayah_word_alignment
python -m unittest tests.test_tokenize tests.test_refine -v
```

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