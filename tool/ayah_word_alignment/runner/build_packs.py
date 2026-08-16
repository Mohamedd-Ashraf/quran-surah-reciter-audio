"""Build word-alignment-SSS.zip packs and patch surah-reciter manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_packs(alignment_root: Path, packs_dir: Path, surahs: list[int]) -> list[dict]:
    packs_dir.mkdir(parents=True, exist_ok=True)
    meta = []
    for s in surahs:
        surah_dir = alignment_root / f"{s:03d}"
        if not surah_dir.is_dir():
            continue
        files = sorted(surah_dir.glob(f"{s:03d}_*.json"))
        if not files:
            continue
        zip_name = f"word-alignment-{s:03d}.zip"
        zip_path = packs_dir / zip_name
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                zf.write(f, arcname=f.name)
        meta.append(
            {
                "surahNumber": s,
                "wordAlignmentFile": zip_name,
                "wordAlignmentChecksum": sha256_file(zip_path),
                "wordAlignmentBytes": zip_path.stat().st_size,
                "ayahJsonCount": len(files),
            }
        )
    return meta


def merge_manifest(
    manifest_path: Path,
    pack_meta: list[dict],
    *,
    aligner: str,
    model: str,
    dataset_version: str,
) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_surah = {m["surahNumber"]: m for m in pack_meta}
    for entry in manifest.get("entries", []):
        s = entry.get("surahNumber")
        if s in by_surah:
            pm = by_surah[s]
            entry["wordAlignmentFile"] = pm["wordAlignmentFile"]
            entry["wordAlignmentChecksum"] = pm["wordAlignmentChecksum"]
            entry["wordAlignmentBytes"] = pm["wordAlignmentBytes"]
    manifest["wordAlignmentMeta"] = {
        "schemaVersion": 1,
        "aligner": aligner,
        "model": model,
        "datasetVersion": dataset_version,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alignment-root", type=Path, required=True,
                    help=".../word-alignment/{reciterId}")
    ap.add_argument("--packs-dir", type=Path, required=True)
    ap.add_argument("--surahs", default="1-114")
    ap.add_argument("--manifest-in", type=Path, default=None)
    ap.add_argument("--manifest-out", type=Path, default=None)
    ap.add_argument("--aligner", default="ctc-forced-aligner")
    ap.add_argument("--model", default="jonatasgrosman/wav2vec2-large-xlsr-53-arabic")
    ap.add_argument("--dataset-version", default="1")
    args = ap.parse_args()

    from runner.run_shard import parse_surahs  # reuse

    surahs = parse_surahs(args.surahs)
    meta = build_packs(args.alignment_root, args.packs_dir, surahs)
    (args.packs_dir / "packs_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    print(f"built {len(meta)} packs in {args.packs_dir}")

    if args.manifest_in and args.manifest_out:
        m = merge_manifest(
            args.manifest_in,
            meta,
            aligner=args.aligner,
            model=args.model,
            dataset_version=args.dataset_version,
        )
        args.manifest_out.write_text(
            json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote patched manifest {args.manifest_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
