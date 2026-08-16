"""Merge shard summaries into summary.json + failures.csv."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--failed-root", type=Path, required=True)
    ap.add_argument("--max-fail-rate", type=float, default=0.05)
    args = ap.parse_args()

    summaries = sorted(args.failed_root.glob("summary_shard*.json"))
    attempted = passed = failed = skipped = 0
    all_failures = []
    for sp in summaries:
        s = json.loads(sp.read_text(encoding="utf-8"))
        attempted += s.get("attempted", 0)
        passed += s.get("passed", 0)
        failed += s.get("failed", 0)
        skipped += s.get("skipped", 0)
        all_failures.extend(s.get("failures", []))

    out = {
        "attempted": attempted,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "processed": passed + failed,
        "failRate": (failed / (passed + failed)) if (passed + failed) else 0.0,
        "failures": all_failures,
    }
    (args.failed_root / "summary.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8"
    )
    with (args.failed_root / "failures.csv").open("w", newline="", encoding="utf-8") as f:
        wri = csv.writer(f)
        wri.writerow(["surah", "ayah", "reason"])
        for row in all_failures:
            wri.writerow([row.get("surah"), row.get("ayah"), row.get("reason")])

    print(json.dumps(out, indent=2))
    if out["processed"] > 0 and out["failRate"] > args.max_fail_rate:
        print(f"FAIL: failRate {out['failRate']:.3f} > {args.max_fail_rate}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
