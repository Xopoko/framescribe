"""Timestamp selection strategies for frame extraction."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


def unique_sorted_timestamps(values: Iterable[float], *, precision: int = 6) -> list[float]:
    """Sort timestamps and drop near-duplicates by rounded precision."""
    normalized = sorted(values)
    deduped: list[float] = []
    seen: set[float] = set()
    for value in normalized:
        key = round(value, precision)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(float(value))
    return deduped


def build_fixed_timestamps(start: float, end: float, interval: float) -> list[float]:
    """Generate fixed-interval timestamps in [start, end)."""
    if end <= start:
        return []
    span = end - start
    count = max(1, int(math.floor((span - 1e-9) / interval)) + 1)
    return [start + (index * interval) for index in range(count)]


def build_adaptive_timestamps(
    *,
    start: float,
    end: float,
    min_interval: float,
    max_interval: float,
    scene_timestamps: Sequence[float],
) -> list[float]:
    """Build an adaptive schedule using scene changes and max-interval backfilling."""
    if end <= start:
        return []

    safe_end = max(start, end - 0.001)
    selected: list[float] = [start]
    last = start

    for scene_ts in scene_timestamps:
        if scene_ts <= start or scene_ts >= safe_end:
            continue

        while scene_ts - last > max_interval:
            last = min(last + max_interval, scene_ts)
            selected.append(last)

        if scene_ts - last >= min_interval:
            selected.append(scene_ts)
            last = scene_ts

    while safe_end - last > max_interval:
        last = last + max_interval
        selected.append(last)

    if safe_end - last >= min_interval and safe_end > last:
        selected.append(safe_end)

    return unique_sorted_timestamps(selected)
