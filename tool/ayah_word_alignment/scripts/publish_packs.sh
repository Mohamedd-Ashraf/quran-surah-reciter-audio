#!/usr/bin/env bash
# Publish EveryAyah word-alignment packs to a DEDICATED release tag.
# Independent of surah-reciter-* MP3 packages.
#
# Tag:  word-alignment-{reciterId}   e.g. word-alignment-ar.alijaber
# Assets: word-alignment-001.zip …
#
# Usage:
#   PUBLIC_PAT=... bash scripts/publish_packs.sh ar.alijaber /path/to/packs
set -euo pipefail
ED="${1:?reciter id e.g. ar.alijaber}"
PACKS_DIR="${2:?path to packs dir containing word-alignment-*.zip}"
TAG="word-alignment-$ED"
PUBLIC_REPO="${PUBLIC_REPO:-Mohamedd-Ashraf/quran-surah-reciter-audio}"

shopt -s nullglob
ZIPS=("$PACKS_DIR"/word-alignment-*.zip)
if [[ ${#ZIPS[@]} -eq 0 ]]; then
  echo "No word-alignment-*.zip in $PACKS_DIR" >&2
  exit 1
fi

upload_to() {
  local repo="$1"
  local token="$2"
  export GH_TOKEN="$token"
  if ! gh release view "$TAG" --repo "$repo" >/dev/null 2>&1; then
    gh release create "$TAG" --repo "$repo" \
      --title "Word alignment — $ED" \
      --notes "EveryAyah per-ayah word timestamps for $ED. Independent of surah-reciter audio packages."
  fi
  for z in "${ZIPS[@]}"; do
    gh release upload "$TAG" --repo "$repo" --clobber "$z"
  done
  if [[ -f "$PACKS_DIR/manifest.json" ]]; then
    gh release upload "$TAG" --repo "$repo" --clobber "$PACKS_DIR/manifest.json"
  fi
  echo "Published ${#ZIPS[@]} packs to $repo@$TAG"
}

if [[ -n "${PUBLIC_PAT:-}" ]]; then
  upload_to "$PUBLIC_REPO" "$PUBLIC_PAT"
elif [[ -n "${GH_TOKEN:-}" ]]; then
  upload_to "$PUBLIC_REPO" "$GH_TOKEN"
else
  echo "Set PUBLIC_PAT or GH_TOKEN to publish to $PUBLIC_REPO" >&2
  exit 1
fi