# surah: `ar.ghamadi`

- **status:** success
- **rank:** 17
- **runId:** 20260906-014842
- **durationSec:** 792
- **publish:** https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/tag/surah-reciter-ar.ghamadi

## Metrics
```json
{
  "totalSurahs": 114,
  "assetCount": 114,
  "totalBytes": 706902878
}
```

## Log tail
```
  File I/O: 5.4%
Built ar.ghamadi :: 114 surahs :: 706902878 bytes
build_summary ok
[13:43:12] Validating manifest SHA-256 + sizes...
validation ok: 114/114 surahs
[13:43:13] Publishing to Mohamedd-Ashraf/quran-surah-reciter-audio tag surah-reciter-ar.ghamadi...
https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/tag/surah-reciter-ar.ghamadi
[13:47:19] Uploaded manifest + 228 audio/timing assets to Mohamedd-Ashraf/quran-surah-reciter-audio
[13:47:19] Public smoke test...
[13:47:19] Waiting for public manifest: https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/download/surah-reciter-ar.ghamadi/manifest.json
[13:47:19] manifest fetched after 10s
manifest ok ar.ghamadi 114
checking 228 files are live...
all 228 files are live
{
  "edition": "ar.ghamadi",
  "baseUrl": "https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/download/surah-reciter-ar.ghamadi",
  "sampleSize": 3,
  "allPassed": true,
  "results": [
    {
      "surah": 82,
      "ok": true,
      "bytes": 763864
    },
    {
      "surah": 15,
      "ok": true,
      "bytes": 6610486
    },
    {
      "surah": 4,
      "ok": true,
      "bytes": 35035054
    }
  ]
}
[13:48:11] Smoke PASSED for ar.ghamadi
[13:48:11] DONE surah packages for ar.ghamadi → https://github.com/Mohamedd-Ashraf/quran-surah-reciter-audio/releases/tag/surah-reciter-ar.ghamadi
[13:48:11] Remember: gcloud compute instances stop surah-packages-worker --zone=us-central1-a --project=quraan-dd543
```
