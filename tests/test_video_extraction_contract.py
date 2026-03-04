from __future__ import annotations

import subprocess
from pathlib import Path

from framescribe.models import ImageFormat
from framescribe.video import extract_frames_fixed


def test_extract_frames_fixed_invokes_ffmpeg(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, *, input=None, text=None, capture_output=None):
        calls.append(list(cmd))

        pattern = cmd[-1]
        output_dir = Path(pattern).parent
        suffix = Path(pattern).suffix
        output_dir.mkdir(parents=True, exist_ok=True)
        for index in range(1, 4):
            (output_dir / f"frame_{index:06d}{suffix}").write_text("frame", encoding="utf-8")

        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    frames = extract_frames_fixed(
        Path("/tmp/input.mov"),
        tmp_path,
        interval=1.0,
        start=0.0,
        end=3.0,
        image_format=ImageFormat.PNG,
        max_frames=None,
        verbose=False,
    )

    assert calls, "ffmpeg command was not invoked"
    assert calls[0][0] == "ffmpeg"
    assert "-vf" in calls[0]
    assert len(frames) == 3
    assert frames[0].timestamp_sec == 0.0
