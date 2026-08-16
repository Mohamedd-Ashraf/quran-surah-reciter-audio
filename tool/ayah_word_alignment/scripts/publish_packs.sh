#!/usr/bin/env bash
# Deprecated: packs/releases were replaced by the git tree layout.
# Prefer: bash scripts/commit_alignment_tree.sh <reciterId>
echo "publish_packs.sh is deprecated." >&2
echo "Alignment JSON is stored in the repo at word-alignment/{reciterId}/SSSAAA.json" >&2
echo "Use: bash scripts/commit_alignment_tree.sh <reciterId>" >&2
exit 1
