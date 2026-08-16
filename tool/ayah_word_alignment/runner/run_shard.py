"""Shard runner: download EveryAyah MP3s, align, validate, resume."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

import requests
import yaml

# Allow `python -m runner.run_shard` from tool/ayah_word_alignment
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from align.align_ayah import AlignmentEngine, write_alignment_json  # noqa: E402
from text.load_quran import ayah_entry  # noqa: E402
from text.tokenize import api_words_from_text  # noqa: E402
from validate.validate_ayah import validate_alignment  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("run_shard")

AYAH_COUNTS = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111,
    110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45, 83,
    182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96,
    29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31,
    50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21, 11, 8, 8, 19, 5,
    8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6,
]


def parse_surahs(spec: str) -> list[int]:
    """Parse '1-114' or '1,2,112-114'."""
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return sorted(x for x in out if 1 <= x <= 114)


def ayah_list_for_surahs(surahs: list[int]) -> list[tuple[int, int]]:
    items: list[tuple[int, int]] = []
    for s in surahs:
        n = AYAH_COUNTS[s - 1]
        for a in range(1, n + 1):
            items.append((s, a))
    return items


def shard_slice(items: list[tuple[int, int]], shard_index: int, shard_count: int):
    return [x for i, x in enumerate(items) if i % shard_count == shard_index]


def everyayah_url(folder: str, surah: int, ayah: int) -> str:
    return f"https://everyayah.com/data/{folder}/{surah:03d}{ayah:03d}.mp3"


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                if chunk:
                    f.write(chunk)


def ayah_stem(surah: int, ayah: int) -> str:
    """EveryAyah-style stem: SSSAAA (e.g. '002255')."""
    return f"{surah:03d}{ayah:03d}"


def json_path(out_root: Path, surah: int, ayah: int) -> Path:
    """Flat per-reciter tree: {reciterId}/SSSAAA.json"""
    return out_root / f"{ayah_stem(surah, ayah)}.json"


def load_existing_valid(path: Path, expected: list[str]) -> bool:
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return bool(validate_alignment(data, expected_words=expected))
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reciter-id", required=True)
    ap.add_argument("--surahs", default="1-114")
    ap.add_argument("--shard-index", type=int, default=0)
    ap.add_argument("--shard-count", type=int, default=1)
    ap.add_argument("--force-rebuild", action="store_true")
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--failed-root", type=Path, required=True)
    ap.add_argument("--tmp-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=ROOT / "reciters.yaml")
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-ayahs", type=int, default=0, help="0 = all in shard")
    ap.add_argument("--dry-run", action="store_true", help="Skip CTC; proportional placeholders for smoke tests only")
    ap.add_argument(
        "--only-ayahs",
        default="",
        help="Comma list of surah:ayah to keep (e.g. 2:255). Empty = all in surah range.",
    )
    args = ap.parse_args()

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    rec = cfg["reciters"].get(args.reciter_id)
    if not rec:
        log.error("Unknown reciter %s", args.reciter_id)
        return 2
    folder = rec["everyayah_folder"]
    model = args.model or cfg.get("default_model")

    surahs = parse_surahs(args.surahs)
    items = ayah_list_for_surahs(surahs)
    items = shard_slice(items, args.shard_index, args.shard_count)
    if args.only_ayahs.strip():
        wanted = set()
        for part in args.only_ayahs.split(","):
            part = part.strip()
            if not part:
                continue
            s, a = part.split(":", 1)
            wanted.add((int(s), int(a)))
        items = [x for x in items if x in wanted]
    if args.max_ayahs > 0:
        items = items[: args.max_ayahs]

    out_root = args.output_root / args.reciter_id
    failed_root = args.failed_root / args.reciter_id
    out_root.mkdir(parents=True, exist_ok=True)
    failed_root.mkdir(parents=True, exist_ok=True)
    args.tmp_dir.mkdir(parents=True, exist_ok=True)

    failures_csv = args.failed_root / f"failures_shard{args.shard_index}.csv"
    summary = {
        "reciterId": args.reciter_id,
        "shardIndex": args.shard_index,
        "attempted": 0,
        "skipped": 0,
        "passed": 0,
        "failed": 0,
        "failures": [],
    }

    engine = None
    if items and not args.dry_run:
        engine = AlignmentEngine(model_name=model)

    with failures_csv.open("w", newline="", encoding="utf-8") as cf:
        writer = csv.writer(cf)
        writer.writerow(["surah", "ayah", "reason"])

        for surah, ayah in items:
            summary["attempted"] += 1
            entry = ayah_entry(surah, ayah)
            words = api_words_from_text(entry["aya_text"])
            dest = json_path(out_root, surah, ayah)

            if not args.force_rebuild and load_existing_valid(dest, words):
                summary["skipped"] += 1
                log.info("skip %s:%s", surah, ayah)
                continue

            mp3 = args.tmp_dir / f"{surah:03d}{ayah:03d}.mp3"
            url = everyayah_url(folder, surah, ayah)
            try:
                if args.dry_run:
                    # Proportional placeholders — NOT for production publish.
                    from align.align_ayah import AlignResult, WordTiming
                    # Rough duration from bitrate probe skipped; use 5s * words
                    duration_ms = max(1500, len(words) * 450)
                    result = AlignResult(
                        surah=surah,
                        ayah=ayah,
                        reciter_id=args.reciter_id,
                        audio_file=f"{surah:03d}{ayah:03d}.mp3",
                        duration_ms=duration_ms,
                    )
                    step = duration_ms / max(len(words), 1)
                    for i, w in enumerate(words):
                        start = int(i * step)
                        end = int((i + 1) * step) if i < len(words) - 1 else duration_ms
                        result.words.append(WordTiming(i + 1, w, start, max(start + 1, end)))
                else:
                    download(url, mp3)
                    assert engine is not None
                    result = engine.align(
                        mp3,
                        words,
                        surah=surah,
                        ayah=ayah,
                        reciter_id=args.reciter_id,
                    )
                data = result.to_json_dict()
                vr = validate_alignment(
                    data,
                    expected_words=words,
                    min_mean_score=None if args.dry_run else -20.0,
                )
                if not result.ok or not vr:
                    reason = result.error or ";".join(vr.errors)
                    fail_path = failed_root / f"{ayah_stem(surah, ayah)}.json"
                    fail_path.write_text(
                        json.dumps(
                            {"error": reason, "partial": data},
                            ensure_ascii=False,
                            indent=2,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    writer.writerow([surah, ayah, reason])
                    summary["failed"] += 1
                    summary["failures"].append(
                        {"surah": surah, "ayah": ayah, "reason": reason}
                    )
                    log.warning("FAIL %s:%s %s", surah, ayah, reason)
                else:
                    write_alignment_json(result, dest)
                    summary["passed"] += 1
                    log.info("OK %s:%s words=%d", surah, ayah, len(words))
            except Exception as e:  # noqa: BLE001
                reason = f"exception:{type(e).__name__}:{e}"
                writer.writerow([surah, ayah, reason])
                summary["failed"] += 1
                summary["failures"].append(
                    {"surah": surah, "ayah": ayah, "reason": reason}
                )
                log.exception("FAIL %s:%s", surah, ayah)
            finally:
                if mp3.exists():
                    mp3.unlink(missing_ok=True)

    summary_path = args.failed_root / f"summary_shard{args.shard_index}.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    log.info("done %s", summary)
    # Soft fail: exit 0 so other shards merge; merge job gates on rate
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
