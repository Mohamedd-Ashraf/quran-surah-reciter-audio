# surah: `ar.warsh.abdulbasit`

- **status:** failed
- **rank:** 2
- **runId:** 20260906-014842
- **durationSec:** 1547
- **error:** exit 255: <asynchronous suspension> #6      _buildEdition (file:///home/mohamed_ashraf_1177s_gmail_com/quraan/tool/build_surah_reciter_packages.dart:255:3) <asynchronous suspension> #7      main (file:///home/m

## Log tail
```
Surah 010: 109/109 ayahs | overall 1471/6236 | cache hits=109 misses=0
Surah 011:  50/123 ayahs | overall 1521/6236 | cache hits=50 misses=0
Surah 011: 100/123 ayahs | overall 1571/6236 | cache hits=100 misses=0
Fetching https://everyayah.com/data/warsh/warsh_Abdul_Basit_128kbps/011122.mp3 (attempt 1/3)
Fetching https://everyayah.com/data/warsh/warsh_Abdul_Basit_128kbps/011122.mp3 (attempt 2/3)
Fetching https://everyayah.com/data/warsh/warsh_Abdul_Basit_128kbps/011122.mp3 (attempt 3/3)
Surah 012:  50/111 ayahs | overall 1642/6236 | cache hits=50 misses=0
Surah 012: 100/111 ayahs | overall 1692/6236 | cache hits=100 misses=0
Surah 012: 111/111 ayahs | overall 1703/6236 | cache hits=111 misses=0
Surah 013:  43/43 ayahs | overall 1746/6236 | cache hits=43 misses=0
Surah 014:  50/52 ayahs | overall 1796/6236 | cache hits=50 misses=0
Surah 014:  52/52 ayahs | overall 1798/6236 | cache hits=52 misses=0
Surah 015:  50/99 ayahs | overall 1848/6236 | cache hits=50 misses=0
Surah 015:  99/99 ayahs | overall 1897/6236 | cache hits=99 misses=0
Surah 016:  50/128 ayahs | overall 1947/6236 | cache hits=50 misses=0
Surah 016: 100/128 ayahs | overall 1997/6236 | cache hits=100 misses=0
Surah 016: 128/128 ayahs | overall 2025/6236 | cache hits=128 misses=0
Surah 017:  50/111 ayahs | overall 2075/6236 | cache hits=50 misses=0
Surah 017: 100/111 ayahs | overall 2125/6236 | cache hits=100 misses=0
Fetching https://everyayah.com/data/warsh/warsh_Abdul_Basit_128kbps/017111.mp3 (attempt 1/3)
Fetching https://everyayah.com/data/warsh/warsh_Abdul_Basit_128kbps/017111.mp3 (attempt 2/3)
Fetching https://everyayah.com/data/warsh/warsh_Abdul_Basit_128kbps/017111.mp3 (attempt 3/3)
Unhandled exception:
HttpException: HTTP 404 for https://everyayah.com/data/warsh/warsh_Abdul_Basit_128kbps/004176.mp3
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
