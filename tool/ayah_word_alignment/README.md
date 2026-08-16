# Ayah word-level forced alignment (EveryAyah)

Offline CTC pipeline for **EveryAyah per-ayah MP3s** (`SSSAAA.mp3`).

Alignment JSON uses the **same stem** and lives in the public **git tree**
(not GitHub Releases).

## Audio source

```text
https://everyayah.com/data/{folder}/{SSSAAA}.mp3
```

## Public distribution (repo files)

```text
word-alignment/{reciterId}/{SSSAAA}.json
```

Example:

```text
word-alignment/ar.alijaber/002255.json
```

CDN URL (app):

```text
https://cdn.jsdelivr.net/gh/Mohamedd-Ashraf/quran-surah-reciter-audio@main/word-alignment/{reciterId}/{SSSAAA}.json
```

Hosted on `Mohamedd-Ashraf/quran-surah-reciter-audio`. Independent of
`surah-reciter-*` packages. Missing files → app falls back to word-count timing.

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
3. `surahs` / `only_ayahs` as needed
4. On success, workflow commits `word-alignment/{reciterId}/*.json` with `[skip ci]`

## Flutter

`WordAlignmentService` GETs each verse JSON from the CDN path above, caches on
disk, and returns `null` on 404 so Reel chunk timing falls back safely.

## Model

`jonatasgrosman/wav2vec2-large-xlsr-53-arabic` via ctc-forced-aligner.
