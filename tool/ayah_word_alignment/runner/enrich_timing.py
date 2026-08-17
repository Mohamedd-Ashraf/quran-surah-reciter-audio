"""Merge-job CLI: reciter-level timing baseline enrichment.

Lightweight, no ML, no audio. Gated by enable_timing_analysis.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from timing.aggregator import enrich_reciter  # noqa: E402
from timing.config import TimingAnalysisConfig  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--alignment-root",
        type=Path,
        required=True,
        help="build/.../alignment/{reciterId}",
    )
    ap.add_argument(
        "--config",
        type=Path,
        default=ROOT / "reciters.yaml",
    )
    ap.add_argument("--enable-timing-analysis", dest="enable", action="store_true")
    ap.add_argument("--no-timing-analysis", dest="enable", action="store_false")
    ap.set_defaults(enable=None)
    args = ap.parse_args()

    raw = {}
    if args.config.is_file():
        loaded = yaml.safe_load(args.config.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            raw = loaded
    cfg = TimingAnalysisConfig.from_mapping(raw)
    if args.enable is not None:
        cfg = cfg.with_enabled(args.enable)

    n = enrich_reciter(args.alignment_root, cfg)
    print(f"timing enrich wrote {n} files enabled={cfg.enabled}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
