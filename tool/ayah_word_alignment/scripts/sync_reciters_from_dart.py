#!/usr/bin/env python3
"""Regenerate reciters.yaml keys from kEveryAyahFolders in ayah_audio_service.dart.

Keeps pipeline + Flutter on one unified reciterId set.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DART = ROOT / "lib" / "core" / "services" / "ayah_audio_service.dart"
YAML = Path(__file__).resolve().parents[1] / "reciters.yaml"
BITRATE_RE = re.compile(
    r"'(ar\.[^']+)':\s*(\d+)",
)
FOLDER_BLOCK = re.compile(
    r"const Map<String, String> kEveryAyahFolders = \{([\s\S]*?)^\};",
    re.M,
)
ENTRY_RE = re.compile(r"'((?:ar\.)[^']+)':\s*'([^']+)'")


def main() -> int:
    dart = DART.read_text(encoding="utf-8")
    m = FOLDER_BLOCK.search(dart)
    if not m:
        print("Could not find kEveryAyahFolders", file=sys.stderr)
        return 1
    folders = {k: v for k, v in ENTRY_RE.findall(m.group(1))}
    bitrates = dict(BITRATE_RE.findall(dart))

    header = """# Auto-synced from lib/core/services/ayah_audio_service.dart (kEveryAyahFolders).
# Unified identity: the same reciterId (e.g. ar.alafasy) is used for:
#   - EveryAyah audio:  https://everyayah.com/data/{folder}/{SSSAAA}.mp3
#   - Word alignment:   word-alignment/{reciterId}/{SSSAAA}.json  (git tree)
default_model: jonatasgrosman/wav2vec2-large-xlsr-53-arabic
aligner: ctc-forced-aligner
dataset_version: "1"
schema_version: 1
# Public distribution: repo files (not Releases). App CDN:
alignment_cdn_base: https://cdn.jsdelivr.net/gh/Mohamedd-Ashraf/quran-surah-reciter-audio@main
alignment_path_template: word-alignment/{reciterId}/{SSSAAA}.json
reciters:
"""
    lines = [header]
    for rid in sorted(folders):
        folder = folders[rid]
        br = bitrates.get(rid, "128")
        lines.append(f"  {rid}:\n")
        lines.append(f"    everyayah_folder: {folder}\n")
        lines.append(f"    bitrate_kbps: {br}\n")
    lines.append("initial_test_surahs: [1, 2, 112, 113, 114]\n")
    YAML.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {len(folders)} reciters to {YAML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
