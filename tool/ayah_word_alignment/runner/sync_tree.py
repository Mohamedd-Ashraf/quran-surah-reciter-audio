"""Copy validated SSSAAA.json files into the public repo tree layout.

Target layout (committed to git, not Releases):

    word-alignment/{reciterId}/{SSSAAA}.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def sync_alignment_tree(
    alignment_root: Path,
    tree_dir: Path,
    *,
    reciter_id: str,
) -> int:
    """Copy *.json from alignment_root into tree_dir/word-alignment/{reciterId}/.

    Accepts either flat SSSAAA.json or legacy SSS/SSS_AAA.json layouts.
    Returns number of files written.
    """
    dest = tree_dir / "word-alignment" / reciter_id
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    if not alignment_root.is_dir():
        return 0

    for path in sorted(alignment_root.rglob("*.json")):
        if path.name.startswith("_"):
            continue
        stem = path.stem
        if "_" in stem:
            parts = stem.split("_", 1)
            if (
                len(parts) == 2
                and parts[0].isdigit()
                and parts[1].isdigit()
            ):
                stem = f"{int(parts[0]):03d}{int(parts[1]):03d}"
            else:
                continue
        if not (len(stem) == 6 and stem.isdigit()):
            continue
        out = dest / f"{stem}.json"
        shutil.copy2(path, out)
        count += 1

    meta = {
        "reciterId": reciter_id,
        "ayahJsonCount": count,
        "layout": "word-alignment/{reciterId}/SSSAAA.json",
    }
    (dest / "_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    print(f"synced {count} ayah JSON → {dest}")
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
