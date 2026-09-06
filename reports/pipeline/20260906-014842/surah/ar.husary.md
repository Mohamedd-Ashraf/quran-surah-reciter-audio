# surah: `ar.husary`

- **status:** success
- **rank:** 6
- **runId:** 20260906-014842
- **durationSec:** 1717
- **publish:** https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/tag/surah-reciter-ar.husary

## Metrics
```json
{
  "totalSurahs": 114,
  "assetCount": 114,
  "totalBytes": 1223433347
}
```

## Log tail
```
  File I/O: 4.1%
Built ar.husary :: 114 surahs :: 1223433347 bytes
build_summary ok
[04:27:59] Validating manifest SHA-256 + sizes...
validation ok: 114/114 surahs
[04:28:04] Publishing to Mohamedd-Ashraf/quran-surah-reciter-audio tag surah-reciter-ar.husary...
[04:28:04] Release surah-reciter-ar.husary exists on Mohamedd-Ashraf/quran-surah-reciter-audio; clobbering assets
[04:33:24] Uploaded manifest + 228 audio/timing assets to Mohamedd-Ashraf/quran-surah-reciter-audio
[04:33:24] Public smoke test...
[04:33:24] Waiting for public manifest: https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/download/surah-reciter-ar.husary/manifest.json
[04:33:24] manifest fetched after 10s
manifest ok ar.husary 114
checking 228 files are live...
all 228 files are live
{
  "edition": "ar.husary",
  "baseUrl": "https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/download/surah-reciter-ar.husary",
  "sampleSize": 3,
  "allPassed": true,
  "results": [
    {
      "surah": 82,
      "ok": true,
      "bytes": 1362590
    },
    {
      "surah": 15,
      "ok": true,
      "bytes": 10752879
    },
    {
      "surah": 4,
      "ok": true,
      "bytes": 55143906
    }
  ]
}
[04:34:21] Smoke PASSED for ar.husary
[04:34:21] DONE surah packages for ar.husary → https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/tag/surah-reciter-ar.husary
[04:34:21] Remember: gcloud compute instances stop surah-packages-worker --zone=us-central1-a --project=quraan-dd543
```
