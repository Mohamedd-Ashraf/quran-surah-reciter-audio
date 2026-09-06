# surah: `ar.mustafaismail`

- **status:** failed
- **rank:** 9
- **runId:** 20260906-014842
- **durationSec:** 224
- **error:** exit 255: <asynchronous suspension> #6      _buildEdition (file:///home/mohamed_ashraf_1177s_gmail_com/quraan/tool/build_surah_reciter_packages.dart:255:3) <asynchronous suspension> #7      main (file:///home/m

## Log tail
```
[12:07:59] Building packages for ar.mustafaismail (workers=4)...
Fetching https://everyayah.com/data/Mustafa_Ismail_48kbps/003001.mp3 (attempt 1/3)
Fetching https://everyayah.com/data/Mustafa_Ismail_48kbps/004001.mp3 (attempt 1/3)
Fetching https://everyayah.com/data/Mustafa_Ismail_48kbps/003001.mp3 (attempt 2/3)
Fetching https://everyayah.com/data/Mustafa_Ismail_48kbps/004001.mp3 (attempt 2/3)
Surah 001:   7/7 ayahs | overall 14/6236 | cache hits=7 misses=0
Fetching https://everyayah.com/data/Mustafa_Ismail_48kbps/005001.mp3 (attempt 1/3)
Fetching https://everyayah.com/data/Mustafa_Ismail_48kbps/003001.mp3 (attempt 3/3)
Fetching https://everyayah.com/data/Mustafa_Ismail_48kbps/004001.mp3 (attempt 3/3)
Fetching https://everyayah.com/data/Mustafa_Ismail_48kbps/005001.mp3 (attempt 2/3)
Fetching https://everyayah.com/data/Mustafa_Ismail_48kbps/005001.mp3 (attempt 3/3)
Surah 002:  50/286 ayahs | overall 57/6236 | cache hits=50 misses=0
Surah 002: 100/286 ayahs | overall 107/6236 | cache hits=100 misses=0
Surah 002: 150/286 ayahs | overall 157/6236 | cache hits=150 misses=0
Surah 002: 200/286 ayahs | overall 207/6236 | cache hits=200 misses=0
Surah 002: 250/286 ayahs | overall 257/6236 | cache hits=250 misses=0
Surah 002: 286/286 ayahs | overall 293/6236 | cache hits=286 misses=0
Fetching https://everyayah.com/data/Mustafa_Ismail_48kbps/006001.mp3 (attempt 1/3)
Fetching https://everyayah.com/data/Mustafa_Ismail_48kbps/006001.mp3 (attempt 2/3)
Fetching https://everyayah.com/data/Mustafa_Ismail_48kbps/006001.mp3 (attempt 3/3)
Unhandled exception:
HttpException: HTTP 404 for https://everyayah.com/data/Mustafa_Ismail_48kbps/003001.mp3
#0      BuildAudioCache._downloadWithRetry (file:///home/mohamed_ashraf_1177s_gmail_com/quraan/tool/build_audio_cache.dart:193:5)
<asynchronous suspension>
#1      BuildAudioCache._materializeLocked (file:///home/mohamed_ashraf_1177s_gmail_com/quraan/tool/build_audio_cache.dart:98:19)
<asynchronous suspension>
#2      BuildAudioCache.materializeWithStatus (file:///home/mohamed_ashraf_1177s_gmail_com/quraan/tool/build_audio_cache.dart:77:21)
<asynchronous suspension>
#3      _buildSurahFile (file:///home/mohamed_ashraf_1177s_gmail_com/quraan/tool/build_surah_reciter_packages.dart:507:24)
<asynchronous suspension>
#4      _buildEdition.runWorker (file:///home/mohamed_ashraf_1177s_gmail_com/quraan/tool/build_surah_reciter_packages.dart:230:22)
<asynchronous suspension>
#5      Future.wait.<anonymous closure> (dart:async/future.dart:567:21)
<asynchronous suspension>
#6      _buildEdition (file:///home/mohamed_ashraf_1177s_gmail_com/quraan/tool/build_surah_reciter_packages.dart:255:3)
<asynchronous suspension>
#7      main (file:///home/mohamed_ashraf_1177s_gmail_com/quraan/tool/build_surah_reciter_packages.dart:144:20)
<asynchronous suspension>
```
