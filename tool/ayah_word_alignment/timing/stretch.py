"""Safe visual Tatweel insertion boundaries.

Positions are layout metadata, not Tajweed. A boundary after cluster i is safe
when inserting U+0640 between cluster i and i+1 preserves Arabic joining:

    left letter joins forward (dual-joining)
    AND right letter joins backward (dual- or right-joining)

``afterClusterIndex`` always refers to a complete grapheme cluster.
Canonical ``text`` is never modified.
"""

from __future__ import annotations

from .clusters import Cluster, clusterize, joins_backward, joins_forward


def safe_boundaries(clusters: list[Cluster]) -> list[int]:
    """Return afterClusterIndex values where Tatweel may be inserted."""
    out: list[int] = []
    for i in range(len(clusters) - 1):
        left = clusters[i]
        right = clusters[i + 1]
        if joins_forward(left) and joins_backward(right):
            out.append(i)
    return out


def _priority(
    after_index: int,
    clusters: list[Cluster],
    madd_indexes: set[int],
) -> int:
    """1 = adjacent to a Madd cluster, 2 = dual|dual, 3 = other safe."""
    adjacent = after_index in madd_indexes or (after_index + 1) in madd_indexes
    if adjacent:
        return 1
    left = clusters[after_index]
    right = clusters[after_index + 1]
    if left.joining == "dual" and right.joining == "dual":
        return 2
    return 3


def detect_stretch_positions(
    text: str,
    *,
    madd_cluster_indexes: list[int] | None = None,
    max_recommended: int = 4,
) -> list[dict]:
    clusters = clusterize(text)
    madd_set = set(madd_cluster_indexes or ())
    positions: list[dict] = []
    for after in safe_boundaries(clusters):
        positions.append(
            {
                "afterClusterIndex": after,
                "priority": _priority(after, clusters, madd_set),
                "maxRecommended": max_recommended,
            }
        )
    positions.sort(key=lambda p: (p["priority"], p["afterClusterIndex"]))
    return positions


def stretch_payload(
    text: str,
    *,
    madd_cluster_indexes: list[int] | None = None,
    max_recommended: int = 4,
) -> dict | None:
    positions = detect_stretch_positions(
        text,
        madd_cluster_indexes=madd_cluster_indexes,
        max_recommended=max_recommended,
    )
    if not positions:
        return None
    return {"positions": positions}


def insert_tatweel(text: str, after_cluster_index: int, count: int = 1) -> str:
    """Insert ``count`` Tatweel characters after the given cluster.

    Never separates a base letter from its combining marks.
    """
    if count < 1:
        raise ValueError("count must be >= 1")
    clusters = clusterize(text)
    if after_cluster_index < 0 or after_cluster_index >= len(clusters) - 1:
        raise ValueError(
            f"after_cluster_index {after_cluster_index} is not a between-cluster boundary"
        )
    parts: list[str] = []
    for i, c in enumerate(clusters):
        parts.append(c.text)
        if i == after_cluster_index:
            parts.append("\u0640" * count)
    return "".join(parts)
