from __future__ import annotations

from framescribe.reporting import parse_short_event, sample_evenly


def test_parse_short_event_marker() -> None:
    text = "SHORT_EVENT: User opens settings\n\nDETAILS:\n- x"
    assert parse_short_event(text) == "User opens settings"


def test_parse_short_event_fallback() -> None:
    text = "\n\nFirst visible line\nOther line"
    assert parse_short_event(text) == "First visible line"


def test_sample_evenly() -> None:
    items = [str(i) for i in range(10)]
    sampled = sample_evenly(items, 4)
    assert sampled == ["0", "3", "6", "9"]
