"""Progress helpers for long-running operations."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import TypeVar, cast

T = TypeVar("T")
_MISSING = object()


def run_with_heartbeat(
    *,
    task_name: str,
    work: Callable[[], T],
    heartbeat_seconds: float,
    log: Callable[[str], None] = print,
) -> tuple[T, float]:
    """Run blocking work and print heartbeat messages while waiting.

    Returns the work result and elapsed seconds.
    """
    if heartbeat_seconds <= 0:
        raise ValueError("heartbeat_seconds must be > 0")

    done = threading.Event()
    result_holder: dict[str, object] = {}
    error_holder: list[BaseException] = []

    def _runner() -> None:
        try:
            result_holder["value"] = work()
        except BaseException as exc:  # pragma: no cover - exercised by tests
            error_holder.append(exc)
        finally:
            done.set()

    start = time.monotonic()
    thread = threading.Thread(target=_runner, name=f"framescribe-{task_name}", daemon=True)
    thread.start()

    try:
        while not done.wait(timeout=heartbeat_seconds):
            elapsed = time.monotonic() - start
            log(f"[progress] {task_name} still running... {elapsed:.1f}s elapsed")
    finally:
        thread.join()

    elapsed = time.monotonic() - start
    if error_holder:
        raise error_holder[0]

    value = result_holder.get("value", _MISSING)
    if value is _MISSING:  # pragma: no cover - defensive
        raise RuntimeError("work finished without result")
    return cast(T, value), elapsed
