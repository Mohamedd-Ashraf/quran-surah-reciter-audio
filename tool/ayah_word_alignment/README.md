# Ayah word-level forced alignment (EveryAyah)

Unified architecture for **all** EveryAyah reciters in `kEveryAyahFolders`.

## Identity (one string everywhere)

| Layer | Uses |
|-------|------|
| App picker / `ReelProject.reciterId` | `ar.alafasy`, `ar.alijaber`, … |
| EveryAyah audio | `https://everyayah.com/data/{folder}/{SSSAAA}.mp3` |
| Word alignment JSON | `word-alignment/{reciterId}/{SSSAAA}.json` |
| Pipeline `reciters.yaml` | same keys as `kEveryAyahFolders` |

Keep yaml in sync:

```bash
python tool/ayah_word_alignment/scripts/sync_reciters_from_dart.py
```

## Public distribution (repo tree, not Releases)

```text
word-alignment/{reciterId}/{SSSAAA}.json
```

CDN (app):

```text
https://cdn.jsdelivr.net/gh/Mohamedd-Ashraf/quran-surah-reciter-audio@main/word-alignment/{reciterId}/{SSSAAA}.json
```

Fallback: `raw.githubusercontent.com/.../main/...`

Missing file / unknown reciter → Flutter returns `null` → word-count chunk timing.

## Flutter wiring

- [`ReelReciterContract`](../../lib/features/reel_creator/data/services/reel_reciter_contract.dart) — shared stem + URLs + normalize
- [`WordAlignmentService`](../../lib/features/reel_creator/data/services/word_alignment_service.dart) — per-ayah fetch/cache
- Preview + Export both use `project.reciterId` with chunking gate

## Local smoke

```bash
cd tool/ayah_word_alignment
python -m unittest tests.test_tokenize -v
python runner/run_shard.py --reciter-id ar.alijaber --surahs 2 --only-ayahs 2:255 --dry-run \
  --output-root ../../build/word_alignment/alignment \
  --failed-root ../../build/word_alignment/failed \
  --tmp-dir ../../build/word_alignment/tmp --force-rebuild
```

## GitHub Actions

**Ayah Word Alignment** workflow commits `word-alignment/{reciterId}/*.json` with `[skip ci]`.

## Model

`jonatasgrosman/wav2vec2-large-xlsr-53-arabic` via ctc-forced-aligner.
