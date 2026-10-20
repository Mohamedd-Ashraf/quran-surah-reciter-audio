#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================
  monthly_leaderboard_reset.py  —  Hard-reset all user scores
=============================================================

Resets EVERY document in `quiz_leaderboard` to zero and writes
a `lastResetAt` timestamp to `leaderboard_meta/config` so the
Flutter app can detect the reset on next launch.

Fields zeroed per user document:
  totalScore, streak, correctAnswers, totalAnswered → 0
  lastUpdated                                        → SERVER_TIMESTAMP

Credentials (one of):
  1. --service-account <path>   path to service-account JSON file
  2. FIREBASE_SERVICE_ACCOUNT_JSON env var (raw JSON string)

Usage:
  python monthly_leaderboard_reset.py -s service-account.json
  python monthly_leaderboard_reset.py -s service-account.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

try:
    import firebase_admin
    from firebase_admin import credentials, firestore as _fs
except ImportError:
    print("ERROR: firebase-admin not installed.  Run:  pip install firebase-admin")
    sys.exit(1)

# ── Constants ─────────────────────────────────────────────────────────────────

LEADERBOARD_COLLECTION = "quiz_leaderboard"
META_COLLECTION        = "leaderboard_meta"
META_DOC               = "config"
BATCH_SIZE             = 400   # Firestore limit is 500; stay safe

RESET_PAYLOAD: dict = {
    "totalScore":        0,
    "streak":            0,
    "correctAnswers":    0,
    "totalAnswered":     0,
}

# ── Init ──────────────────────────────────────────────────────────────────────

def init_firebase(service_account_path: str | None) -> None:
    """Initialize Firebase Admin from file path or environment variable."""
    if firebase_admin._DEFAULT_APP_NAME in firebase_admin._apps:
        return  # already initialised

    sa_json_env = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")

    if service_account_path:
        cred = credentials.Certificate(service_account_path)
    elif sa_json_env:
        try:
            sa_dict = json.loads(sa_json_env)
        except json.JSONDecodeError as exc:
            print(f"ERROR: FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON: {exc}")
            sys.exit(1)
        cred = credentials.Certificate(sa_dict)
    else:
        print(
            "ERROR: Provide --service-account <path> or set "
            "FIREBASE_SERVICE_ACCOUNT_JSON environment variable."
        )
        sys.exit(1)

    firebase_admin.initialize_app(cred)

# ── Reset logic ───────────────────────────────────────────────────────────────

def reset_all(dry_run: bool) -> int:
    """Paginate through quiz_leaderboard and zero every document.

    Returns the total number of documents processed.
    """
    db = _fs.client()
    collection = db.collection(LEADERBOARD_COLLECTION)

    total = 0
    last_doc = None

    while True:
        query = (
            collection
            .order_by("__name__")
            .limit(BATCH_SIZE)
        )
        if last_doc is not None:
            query = query.start_after(last_doc)

        snap = query.get()
        if not snap:
            break

        if not dry_run:
            batch = db.batch()
            for doc in snap:
                payload = dict(RESET_PAYLOAD)
                payload["lastUpdated"] = _fs.SERVER_TIMESTAMP
                batch.update(doc.reference, payload)
            batch.commit()

        total += len(snap)
        print(f"  … processed {total} documents", end="\r", flush=True)
        last_doc = snap[-1]

        if len(snap) < BATCH_SIZE:
            break   # last page

    print()  # newline after \r
    return total


def write_meta(total: int, dry_run: bool) -> None:
    """Record the reset timestamp in leaderboard_meta/config."""
    if dry_run:
        print("[dry-run] Would write leaderboard_meta/config.lastResetAt")
        return

    db = _fs.client()
    db.collection(META_COLLECTION).document(META_DOC).set(
        {
            "lastResetAt":    _fs.SERVER_TIMESTAMP,
            "lastResetCount": total,
        },
        merge=True,
    )
    print(f"✓ leaderboard_meta/config updated  (lastResetCount={total})")

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monthly hard-reset of all quiz leaderboard scores.",
    )
    parser.add_argument(
        "-s", "--service-account",
        metavar="PATH",
        default=None,
        help="Path to Firebase service-account JSON (or set FIREBASE_SERVICE_ACCOUNT_JSON env var).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without writing to Firestore.",
    )
    args = parser.parse_args()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    label = "[DRY-RUN] " if args.dry_run else ""
    print(f"\n{'='*60}")
    print(f"  {label}Monthly Leaderboard Reset")
    print(f"  Started: {now}")
    print(f"{'='*60}\n")

    init_firebase(args.service_account)

    print(f"Resetting all documents in '{LEADERBOARD_COLLECTION}' …")
    total = reset_all(dry_run=args.dry_run)

    if total == 0:
        print("  No documents found — nothing to reset.")
    else:
        action = "Would reset" if args.dry_run else "Reset"
        print(f"✓ {action} {total} user document(s).")

    write_meta(total, dry_run=args.dry_run)

    print(f"\n{'='*60}")
    print(f"  {label}Done.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
