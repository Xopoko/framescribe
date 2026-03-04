from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from framescribe.models import FramescribeError
from framescribe.video import detect_scene_change_timestamps, get_video_duration_seconds


def test_get_video_duration_seconds(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout="12.5\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    duration = get_video_duration_seconds(Path("/tmp/video.mp4"))
    assert duration == 12.5


def test_detect_scene_change_timestamps(monkeypatch: pytest.MonkeyPatch) -> None:
    log = (
        "[Parsed_showinfo_1 @ x] n:1 pts:30 pts_time:1.000\n"
        "[Parsed_showinfo_1 @ x] n:2 pts:150 pts_time:5.000"
    )

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout="", stderr=log)

    monkeypatch.setattr(subprocess, "run", fake_run)
    points = detect_scene_change_timestamps(
        Path("/tmp/video.mp4"), start=10.0, end=20.0, threshold=0.12, verbose=False
    )
    assert points == [11.0, 15.0]


def test_get_video_duration_seconds_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(FramescribeError):
        get_video_duration_seconds(Path("/tmp/video.mp4"))
