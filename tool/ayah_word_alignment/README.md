# Ayah word-level forced alignment (EveryAyah)

Offline CTC pipeline for **EveryAyah per-ayah MP3s** (`SSSAAA.mp3`).

This dataset is **independent** of surah-reciter packages (`001.mp3` / `001.timings.json`).
Any reciter in `kEveryAyahFolders` / `reciters.yaml` can be aligned — including
`ar.alijaber` (علي عبد الله جابر) who has no surah-reciter release.

## Audio source

```text
https://everyayah.com/data/{folder}/{SSS}{AAA}.mp3
```

## Public distribution (alignment packs only)

```text
Release tag:  word-alignment-{reciterId}
Example:      word-alignment-ar.alijaber
Asset:        word-alignment-002.zip
URL:          …/releases/download/word-alignment-ar.alijaber/word-alignment-002.zip
```

Hosted on `Mohamedd-Ashraf/quran-surah-reciter-audio` as a **separate tag family** —
does not modify existing `surah-reciter-*` releases.

## Local smoke

```bash
cd tool/ayah_word_alignment
python -m unittest tests.test_tokenize -v

python runner/run_shard.py --reciter-id ar.alijaber --surahs 2 --only-ayahs 2:255 --dry-run \
  --output-root ../../build/word_alignment/alignment \
  --failed-root ../../build/word_alignment/failed \
  --tmp-dir ../../build/word_alignment/tmp --force-rebuild
```

## GitHub Actions (real CTC)

1. **Ayah Word Alignment** → Run workflow
2. `reciter_id` = `ar.alijaber` (any EveryAyah id from `reciters.yaml`)
3. `surahs` = `2`
4. `only_ayahs` = `2:255` (optional; empty = whole surah range)
5. Download artifact → publish:

```bash
PUBLIC_PAT=… bash scripts/publish_packs.sh ar.alijaber /path/to/packs
```

## Flutter

`WordAlignmentService` loads packs from `word-alignment-{reciterId}` tags.
Reel audio stays EveryAyah; enable **Word-aligned timing** in reel settings.

## Model

`jonatasgrosman/wav2vec2-large-xlsr-53-arabic` via ctc-forced-aligner (forced alignment).