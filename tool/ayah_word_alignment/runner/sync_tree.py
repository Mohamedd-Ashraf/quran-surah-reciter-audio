"""Copy validated ayah JSON into the public repo tree layout.

Target layout (committed to git, not Releases):

    word-alignment/{reciterId}/{surahNumber}/{ayahNumber}.json

Example: word-alignment/ar.alijaber/2/255.json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_FLAT_STEM = re.compile(r"^(\d{3})(\d{3})$")
_UNDERSCORE = re.compile(r"^(\d+)_(\d+)$")


def _parse_surah_ayah(path: Path) -> tuple[int, int] | None:
    """Resolve surah/ayah from nested dirs or legacy flat names."""
    # Preferred build output: {surah}/{ayah}.json
    if path.parent.name.isdigit() and path.stem.isdigit():
        # .../alignment/{reciter}/{surah}/{ayah}.json OR .../{surah}/{ayah}.json
        return int(path.parent.name), int(path.stem)

    stem = path.stem
    m = _FLAT_STEM.match(stem)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = _UNDERSCORE.match(stem)
    if m:
        return int(m.group(1)), int(m.group(2))

    # Legacy: .../002/002_255.json
    if path.parent.name.isdigit():
        surah = int(path.parent.name)
        m = _UNDERSCORE.match(stem)
        if m and int(m.group(1)) == surah:
            return surah, int(m.group(2))
        if stem.isdigit():
            return surah, int(stem)
    return None


def sync_alignment_tree(
    alignment_root: Path,
    tree_dir: Path,
    *,
    reciter_id: str,
) -> int:
    """Copy *.json into tree_dir/word-alignment/{reciterId}/{surah}/{ayah}.json."""
    dest_root = tree_dir / "word-alignment" / reciter_id
    dest_root.mkdir(parents=True, exist_ok=True)
    count = 0
    if not alignment_root.is_dir():
        return 0

    for path in sorted(alignment_root.rglob("*.json")):
        if path.name.startswith("_"):
            continue
        parsed = _parse_surah_ayah(path)
        if parsed is None:
            continue
        surah, ayah = parsed
        out = dest_root / str(surah) / f"{ayah}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out)
        count += 1

    meta = {
        "reciterId": reciter_id,
        "ayahJsonCount": count,
        "layout": "word-alignment/{reciterId}/{surahNumber}/{ayahNumber}.json",
    }
    (dest_root / "_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    print(f"synced {count} ayah JSON -> {dest_root}")
    return count


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--alignment-root",
        type=Path,
        required=True,
        help="build/.../alignment/{reciterId}",
    )
    ap.add_argument(
        "--tree-dir",
        type=Path,
        required=True,
        help="Repo root that will contain word-alignment/",
    )
    ap.add_argument("--reciter-id", required=True)
    args = ap.parse_args()
    n = sync_alignment_tree(
        args.alignment_root, args.tree_dir, reciter_id=args.reciter_id
    )
    return 0 if n >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())