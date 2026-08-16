#!/usr/bin/env bash
# Commit word-alignment/{reciterId}/{surah}/{ayah}.json into the current git repo.
# Usage: bash scripts/commit_alignment_tree.sh <reciterId>
set -euo pipefail
ED="${1:?reciter id e.g. ar.alijaber}"
ROOT="$(git rev-parse --show-toplevel)"
DIR="$ROOT/word-alignment/$ED"
if [[ ! -d "$DIR" ]]; then
  echo "Missing $DIR" >&2
  exit 1
fi
count=$(find "$DIR" -type f -name '*.json' ! -name '_meta.json' | wc -l | tr -d ' ')
if [[ "$count" -eq 0 ]]; then
  echo "No ayah JSON under $DIR" >&2
  exit 1
fi
git config user.name "${GIT_AUTHOR_NAME:-github-actions[bot]}"
git config user.email "${GIT_AUTHOR_EMAIL:-github-actions[bot]@users.noreply.github.com}"
git add "word-alignment/$ED"
if git diff --cached --quiet; then
  echo "No tree changes for $ED"
  exit 0
fi
git commit --trailer "Co-authored-by: Cursor <cursoragent@cursor.com>" -m "chore(word-alignment): update $ED [skip ci]"
git push
echo "Committed $count files under word-alignment/$ED"