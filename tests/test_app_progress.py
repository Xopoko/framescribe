from __future__ import annotations

import time
from pathlib import Path

from framescribe import app
from framescribe.models import (
    CliOptions,
    FrameSample,
    ImageFormat,
    ProviderName,
    ProviderRunOptions,
    SamplingMode,
)


class _FakeProvider:
    def __init__(self) -> None:
        self._analyze_calls = 0

    def analyze_frame(
        self,
        *,
        image_path: Path,
        prompt: str,
        output_path: Path,
        run_options: ProviderRunOptions,
        verbose: bool,
    ) -> str:
        _ = (image_path, prompt, run_options, verbose)
        self._analyze_calls += 1
        time.sleep(0.03)
        text = f"SHORT_EVENT: event {self._analyze_calls}"
        output_path.write_text(text, encoding="utf-8")
        return text

    def summarize(
        self,
        *,
        prompt: str,
        output_path: Path,
        run_options: ProviderRunOptions,
        verbose: bool,
    ) -> str:
        _ = (prompt, run_options, verbose)
        time.sleep(0.03)
        text = "Summary"
        output_path.write_text(text, encoding="utf-8")
        return text


def test_run_prints_long_run_progress_logs(monkeypatch, tmp_path: Path, capsys) -> None:
    video_path = tmp_path / "video.mov"
    video_path.write_text("video", encoding="utf-8")

    fake_provider = _FakeProvider()

    def fake_extract_frames_fixed(
        video_path: Path,
        frames_dir: Path,
        *,
        interval: float,
        start: float,
        end: float,
        image_format: ImageFormat,
        max_frames: int | None,
        verbose: bool,
    ) -> list[FrameSample]:
        _ = (video_path, interval, start, end, image_format, max_frames, verbose)
        frames_dir.mkdir(parents=True, exist_ok=True)
        frame1 = frames_dir / "frame_000001.png"
        frame2 = frames_dir / "frame_000002.png"
        frame1.write_text("f1", encoding="utf-8")
        frame2.write_text("f2", encoding="utf-8")
        return [
            FrameSample(timestamp_sec=0.0, frame_path=frame1),
            FrameSample(timestamp_sec=1.0, frame_path=frame2),
        ]

    monkeypatch.setattr(app, "_create_provider", lambda name: fake_provider)
    monkeypatch.setattr(app, "_ensure_dependencies", lambda options, provider: None)
    monkeypatch.setattr(app, "get_video_duration_seconds", lambda video, verbose: 2.0)
    monkeypatch.setattr(app, "extract_frames_fixed", fake_extract_frames_fixed)
    monkeypatch.setattr(app, "HEARTBEAT_SECONDS", 0.01)

    options = CliOptions(
        video=video_path,
        output=tmp_path / "out",
        overwrite=True,
        dry_run=False,
        provider=ProviderName.CODEX,
        provider_run_options=ProviderRunOptions(codex_path="codex"),
        sampling_mode=SamplingMode.FIXED,
        interval=1.0,
        adaptive_min_interval=0.4,
        adaptive_max_interval=2.0,
        adaptive_scene_threshold=0.12,
        start=0.0,
        end=None,
        max_frames=None,
        summary_max_events=300,
        report_language="en",
        image_format=ImageFormat.PNG,
        no_summary=False,
        verbose=False,
    )

    output_dir = app.run(options)

    assert output_dir == tmp_path / "out"
    stdout = capsys.readouterr().out
    assert "10-second video can take over 1 minute" in stdout
    assert "[1/2] start t=0.00s" in stdout
    assert "[progress] frame 1/2 still running..." in stdout
    assert "[1/2] done t=0.00s in" in stdout
    assert "[summary] start" in stdout
    assert "[progress] summary still running..." in stdout
    assert "[summary] done in" in stdout

    assert (output_dir / "timeline.md").is_file()
    assert (output_dir / "timeline.jsonl").is_file()
    assert (output_dir / "summary.md").is_file()
