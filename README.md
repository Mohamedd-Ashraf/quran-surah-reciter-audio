# Quran Surah-Reciter Audio Packages

Pre-built **per-surah** recitation audio packages (64 kbps MP3 + per-ayah timings JSON) for the [Noor Al-Imaan](https://github.com/Mohamedd-Ashraf/Noor-Al-Imaan) app. Each release tag corresponds to one reciter (edition) and contains the full 114-surah package set.

## Editions

| Release tag | Reciter |
|---|---|
| `surah-reciter-ar.husary` | Mahmoud Khalil Al-Husary (Murattal) |
| `surah-reciter-ar.afasy` | Mishary Rashid Alafasy |
| `surah-reciter-ar.abdurrahaansudais` | Abdur-Rahman As-Sudais |
| `surah-reciter-ar.saoodshuraym` | Saud Ash-Shuraym |
| `surah-reciter-ar.minshawi` | Mohamed Siddiq El-Minshawi (Murattal) |
| `surah-reciter-ar.minshawimujawwad` | Mohamed Siddiq El-Minshawi (Mujawwad) |
| `surah-reciter-ar.abdulsamad` | Abdul Basit Abdus-Samad (Murattal) |
| `surah-reciter-ar.abdulbasitmujawwad` | Abdul Basit Abdus-Samad (Mujawwad) |

## Structure (per release tag)

```
surah-reciter-ar.husary/            ← release tag = edition
├── manifest.json                   — 114 entries with SHA-256 checksums + provenance
├── 001.mp3                         — Surah Al-Fatiha (full surah, one file)
├── 001.timings.json                — per-ayah start/end ms
├── 002.mp3
├── 002.timings.json
├── ...
├── 114.mp3
├── 114.timings.json
├── build_report.json               — build pipeline statistics
└── validation_report.json          — post-build integrity verification
```

## Usage

### Base URL pattern

```
https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/download/surah-reciter-<editionId>/{filename}
```

### Example

```dart
final edition = 'ar.husary';
final base = 'https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/download/surah-reciter-$edition';

// Fetch manifest
final manifest = await http.get(Uri.parse('$base/manifest.json'));

// Download a surah package
final surah1 = await http.get(Uri.parse('$base/001.mp3'));

// Load per-ayah timings
final timings = await http.get(Uri.parse('$base/001.timings.json'));
```

### Manifest format

```json
{
  "version": 1,
  "kind": "surah_reciter",
  "editionId": "ar.husary",
  "generatedAt": "2026-07-31T10:00:00Z",
  "sourceBaseUrl": "https://everyayah.com/data/Husary_128kbps",
  "entries": [
    {
      "surahNumber": 1,
      "audioFile": "001.mp3",
      "checksum": "sha256-of-mp3",
      "bytes": 524288,
      "timingFile": "001.timings.json",
      "timingChecksum": "sha256-of-timings"
    }
  ]
}
```

### Timings JSON format

```json
{
  "surah": 1,
  "ayahs": [
    { "ayah": 1, "startMs": 0, "endMs": 1234 },
    { "ayah": 2, "startMs": 1234, "endMs": 5678 }
  ]
}
```

## Integrity

Every MP3 and timings file is SHA-256 verified at download time against the manifest. Consumers should refuse any file whose checksum does not match.

## License

The audio content belongs to the respective reciters and is publicly available via [everyayah.com](https://everyayah.com) and [mp3quran.net](https://mp3quran.net). This repository is a redistributable packaging format for app integration. Please respect the reciters' licenses and attribution requirements.

## Build

Packages are built by the [Noor Al-Imaan](https://github.com/Mohamedd-Ashraf/Noor-Al-Imaan) CI pipeline (`tool/build_surah_reciter_packages.dart`): per-ayah MP3s are downloaded from the upstream source, concatenated per surah with ffmpeg, transcoded to 64 kbps mono, and verified before publishing. This repository is an automated mirror of the source repo's releases.

## Word alignment (repo tree)

Per-ayah CTC word timestamps live **in this repository** (not Releases). Layout is unified for every EveryAyah reciter id (`ar.alijaber`, `ar.husary`, `ar.minshawi`, …):

```
word-alignment/{reciterId}/{surahNumber}/{ayahNumber}.json
```

Examples:

```
word-alignment/ar.alijaber/2/255.json
word-alignment/ar.husary/1/1.json
word-alignment/ar.minshawi/114/6.json
```

CDN:

```
https://cdn.jsdelivr.net/gh/Mohamedd-Ashraf/quran-surah-reciter-audio@main/word-alignment/{reciterId}/{surahNumber}/{ayahNumber}.json
```

Fallback: `raw.githubusercontent.com/.../main/...`

Missing files: the app falls back to word-count chunk timing.

Build via Actions workflow **Ayah Word Alignment** (commits into `word-alignment/`).
