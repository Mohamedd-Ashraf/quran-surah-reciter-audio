"""Merge shard summaries into summary.json + failures.csv."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def merge_summaries(summaries: list[dict]) -> dict:
    attempted = passed = failed = skipped = 0
    all_failures: list[dict] = []
    for s in summaries:
        attempted += int(s.get("attempted", 0))
        passed += int(s.get("passed", 0))
        failed += int(s.get("failed", 0))
        skipped += int(s.get("skipped", 0))
        all_failures.extend(s.get("failures", []))
    return {
        "attempted": attempted,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "processed": passed + failed,
        # Skipped (already-valid) ayahs are part of the job, not a 100% fail.
        "failRate": (failed / attempted) if attempted else 0.0,
        "failures": all_failures,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--failed-root", type=Path, required=True)
    ap.add_argument("--max-fail-rate", type=float, default=0.05)
    ap.add_argument(
        "--no-gate",
        action="store_true",
        help="Write summary.json but do not exit 1 on a high fail rate",
    )
    args = ap.parse_args()

    loaded = [
        json.loads(sp.read_text(encoding="utf-8"))
        for sp in sorted(args.failed_root.glob("summary_shard*.json"))
    ]
    out = merge_summaries(loaded)
    (args.failed_root / "summary.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8"
    )
    with (args.failed_root / "failures.csv").open("w", newline="", encoding="utf-8") as f:
        wri = csv.writer(f)
        wri.writerow(["surah", "ayah", "reason"])
        for row in out["failures"]:
            wri.writerow([row.get("surah"), row.get("ayah"), row.get("reason")])

    print(json.dumps(out, indent=2))
    if (
        not args.no_gate
        and out["attempted"] > 0
        and out["failRate"] > args.max_fail_rate
    ):
        print(f"FAIL: failRate {out['failRate']:.3f} > {args.max_fail_rate}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
