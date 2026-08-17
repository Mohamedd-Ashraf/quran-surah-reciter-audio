"""Robust duration statistics (median preferred)."""

from __future__ import annotations

from statistics import median


def mean_ms(values: list[int] | list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def median_ms(values: list[int] | list[float]) -> float | None:
    if not values:
        return None
    return round(float(median(values)), 1)


def leave_one_out_median(values: list[int], index: int) -> float | None:
    if index < 0 or index >= len(values):
        return median_ms(values)
    others = [v for i, v in enumerate(values) if i != index]
    return median_ms(others)
