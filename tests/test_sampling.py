from __future__ import annotations

from framescribe.sampling import build_adaptive_timestamps, build_fixed_timestamps


def test_build_fixed_timestamps_end_exclusive() -> None:
    timestamps = build_fixed_timestamps(0.0, 10.0, 1.0)
    assert timestamps == [float(i) for i in range(10)]


def test_build_adaptive_timestamps_static_scene() -> None:
    timestamps = build_adaptive_timestamps(
        start=0.0,
        end=10.0,
        min_interval=0.4,
        max_interval=2.0,
        scene_timestamps=[],
    )
    assert timestamps[0] == 0.0
    assert len(timestamps) == 6
    assert timestamps[-1] > 9.8


def test_build_adaptive_timestamps_includes_valid_scene_changes() -> None:
    timestamps = build_adaptive_timestamps(
        start=0.0,
        end=8.0,
        min_interval=0.4,
        max_interval=2.0,
        scene_timestamps=[0.2, 1.1, 1.3, 6.5],
    )
    assert 1.1 in timestamps
    assert 6.5 in timestamps
