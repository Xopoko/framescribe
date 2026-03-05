from __future__ import annotations

import time

import pytest

from framescribe.progress import run_with_heartbeat


def test_run_with_heartbeat_emits_heartbeat_for_slow_work() -> None:
    messages: list[str] = []

    value, elapsed = run_with_heartbeat(
        task_name="slow task",
        work=lambda: (time.sleep(0.05), "done")[1],
        heartbeat_seconds=0.01,
        log=messages.append,
    )

    assert value == "done"
    assert elapsed > 0
    assert any("slow task still running" in message for message in messages)


def test_run_with_heartbeat_emits_no_heartbeat_for_fast_work() -> None:
    messages: list[str] = []

    value, _ = run_with_heartbeat(
        task_name="fast task",
        work=lambda: "done",
        heartbeat_seconds=0.05,
        log=messages.append,
    )

    assert value == "done"
    assert messages == []


def test_run_with_heartbeat_propagates_errors_and_stops_heartbeat() -> None:
    messages: list[str] = []

    def fail() -> str:
        time.sleep(0.02)
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        run_with_heartbeat(
            task_name="failing task",
            work=fail,
            heartbeat_seconds=0.01,
            log=messages.append,
        )

    count_after_failure = len(messages)
    time.sleep(0.03)
    assert len(messages) == count_after_failure
