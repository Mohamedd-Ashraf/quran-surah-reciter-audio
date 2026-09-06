# surah: `ar.minshawi`

- **status:** success
- **rank:** 3
- **runId:** 20260906-014842
- **durationSec:** 1378
- **publish:** https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/tag/surah-reciter-ar.minshawi

## Metrics
```json
{
  "totalSurahs": 114,
  "assetCount": 114,
  "totalBytes": 828008647
}
```

## Log tail
```
  File I/O: 4.3%
Built ar.minshawi :: 114 surahs :: 828008647 bytes
build_summary ok
[02:58:24] Validating manifest SHA-256 + sizes...
validation ok: 114/114 surahs
[02:58:25] Publishing to Mohamedd-Ashraf/quran-surah-reciter-audio tag surah-reciter-ar.minshawi...
[02:58:26] Release surah-reciter-ar.minshawi exists on Mohamedd-Ashraf/quran-surah-reciter-audio; clobbering assets
[03:03:43] Uploaded manifest + 228 audio/timing assets to Mohamedd-Ashraf/quran-surah-reciter-audio
[03:03:43] Public smoke test...
[03:03:43] Waiting for public manifest: https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/download/surah-reciter-ar.minshawi/manifest.json
[03:03:44] manifest fetched after 10s
manifest ok ar.minshawi 114
checking 228 files are live...
all 228 files are live
{
  "edition": "ar.minshawi",
  "baseUrl": "https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/download/surah-reciter-ar.minshawi",
  "sampleSize": 3,
  "allPassed": true,
  "results": [
    {
      "surah": 82,
      "ok": true,
      "bytes": 991234
    },
    {
      "surah": 15,
      "ok": true,
      "bytes": 6839110
    },
    {
      "surah": 4,
      "ok": true,
      "bytes": 41317190
    }
  ]
}
[03:04:40] Smoke PASSED for ar.minshawi
[03:04:40] DONE surah packages for ar.minshawi → https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/tag/surah-reciter-ar.minshawi
[03:04:40] Remember: gcloud compute instances stop surah-packages-worker --zone=us-central1-a --project=quraan-dd543
```
