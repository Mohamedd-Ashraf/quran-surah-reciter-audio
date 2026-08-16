"""Load ayah_text from quran_ayahs.json snapshot or quran_data.dart."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_TOOL_ROOT = Path(__file__).resolve().parents[1]
_JSON_SNAPSHOT = _TOOL_ROOT / "testdata" / "quran_ayahs.json"
_DEFAULT_QURAN_DATA = (
    Path(__file__).resolve().parents[3]
    / "packages"
    / "qcf_quran_plus"
    / "lib"
    / "src"
    / "data"
    / "quran_data.dart"
)

_ENTRY_RE = re.compile(
    r'"sora"\s*:\s*(\d+)\s*,.*?\"aya_no\"\s*:\s*(\d+)\s*,.*?\"aya_text\"\s*:\s*\"((?:\\.|[^\"\\])*)\"',
    re.DOTALL,
)


def _unescape_dart_string(s: str) -> str:
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            if n == "n":
                out.append("\n"); i += 2; continue
            if n == "t":
                out.append("\t"); i += 2; continue
            if n == "\\":
                out.append("\\"); i += 2; continue
            if n == '"':
                out.append('"'); i += 2; continue
            if n == "u" and i + 5 < len(s):
                hexpart = s[i + 2 : i + 6]
                try:
                    out.append(chr(int(hexpart, 16))); i += 6; continue
                except ValueError:
                    pass
            out.append(n); i += 2; continue
        out.append(c); i += 1
    return "".join(out)


def _from_json(path: Path) -> dict[tuple[int, int], dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    index: dict[tuple[int, int], dict[str, Any]] = {}
    for _k, e in raw.items():
        surah = int(e["sora"])
        ayah = int(e["aya_no"])
        index[(surah, ayah)] = {
            "sora": surah,
            "aya_no": ayah,
            "aya_text": e["aya_text"],
        }
    return index


def _from_dart(path: Path) -> dict[tuple[int, int], dict[str, Any]]:
    raw = path.read_text(encoding="utf-8")
    index: dict[tuple[int, int], dict[str, Any]] = {}
    for m in _ENTRY_RE.finditer(raw):
        surah = int(m.group(1))
        ayah = int(m.group(2))
        text = _unescape_dart_string(m.group(3))
        index[(surah, ayah)] = {"sora": surah, "aya_no": ayah, "aya_text": text}
    return index


@lru_cache(maxsize=2)
def load_quran_index(path: str | None = None) -> dict[tuple[int, int], dict[str, Any]]:
    if path:
        p = Path(path)
        if p.suffix.lower() == ".json":
            index = _from_json(p)
        else:
            index = _from_dart(p)
    elif _JSON_SNAPSHOT.is_file():
        index = _from_json(_JSON_SNAPSHOT)
    elif _DEFAULT_QURAN_DATA.is_file():
        index = _from_dart(_DEFAULT_QURAN_DATA)
    else:
        raise FileNotFoundError(
            f"No Quran text source: missing {_JSON_SNAPSHOT} and {_DEFAULT_QURAN_DATA}"
        )
    if len(index) < 6000:
        raise RuntimeError(f"Expected ~6236 ayahs, got {len(index)}")
    return index


def ayah_entry(surah: int, ayah: int, path: str | None = None) -> dict[str, Any]:
    index = load_quran_index(path)
    key = (surah, ayah)
    if key not in index:
        raise KeyError(f"Missing ayah {surah}:{ayah}")
    return index[key]
