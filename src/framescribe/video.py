"""Video and subprocess utilities for Framescribe."""

from __future__ import annotations

import re
import shlex
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path

from .models import FrameSample, FramescribeError, ImageFormat


def command_to_string(cmd: Sequence[str]) -> str:
    """Render a shell-safe command string for logs."""
    return " ".join(shlex.quote(part) for part in cmd)


def run_command(
    cmd: Sequence[str],
    *,
    stdin_text: str | None = None,
    verbose: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Execute a command and optionally raise a FramescribeError on non-zero exit."""
    if verbose:
        print(f"$ {command_to_string(cmd)}")

    process = subprocess.run(cmd, input=stdin_text, text=True, capture_output=True)

    if check and process.returncode != 0:
        details = process.stderr.strip() or process.stdout.strip() or (
            f"command exited with code {process.returncode}"
        )
        raise FramescribeError(details)

    return process


def ensure_tool(name: str) -> None:
    """Ensure an executable is discoverable in PATH."""
    if shutil.which(name) is None:
        raise FramescribeError(f"required tool not found in PATH: {name}")


def get_video_duration_seconds(video_path: Path, *, verbose: bool = False) -> float:
    """Read video duration using ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    process = run_command(cmd, verbose=verbose)
    output = process.stdout.strip()
    if not output:
        raise FramescribeError("ffprobe returned empty duration")

    try:
        duration = float(output)
    except ValueError as exc:  # pragma: no cover - defensive
        raise FramescribeError(
            f"unable to parse video duration from ffprobe output: {output}"
        ) from exc

    if duration <= 0:
        raise FramescribeError(f"video duration must be positive, got {duration}")

    return duration


def detect_scene_change_timestamps(
    video_path: Path,
    *,
    start: float,
    end: float,
    threshold: float,
    verbose: bool,
) -> list[float]:
    """Return scene-change timestamps reported by ffmpeg showinfo output."""
    clip_duration = max(end - start, 0.0)
    if clip_duration <= 0:
        return []

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "info",
        "-ss",
        f"{start:.6f}",
        "-i",
        str(video_path),
        "-t",
        f"{clip_duration:.6f}",
        "-vf",
        f"select='gt(scene,{threshold})',showinfo",
        "-f",
        "null",
        "-",
    ]
    process = run_command(cmd, verbose=verbose, check=False)
    if process.returncode != 0:
        details = process.stderr.strip() or process.stdout.strip() or (
            f"scene detection failed with code {process.returncode}"
        )
        raise FramescribeError(details)

    combined_output = f"{process.stdout}\n{process.stderr}"
    matches = re.findall(r"pts_time:([0-9]+(?:\.[0-9]+)?)", combined_output)
    timestamps = [start + float(match) for match in matches]
    return sorted(ts for ts in timestamps if start < ts < end)


def extract_frame_at_timestamp(
    video_path: Path,
    *,
    timestamp: float,
    output_path: Path,
    image_format: ImageFormat,
    verbose: bool,
) -> None:
    """Extract a single frame at a timestamp, with a near-end fallback."""

    def build_cmd(seek_ts: float) -> list[str]:
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{seek_ts:.6f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
        ]
        if image_format == ImageFormat.JPG:
            cmd += ["-q:v", "2"]
        cmd += [str(output_path)]
        return cmd

    run_command(build_cmd(timestamp), verbose=verbose)
    if output_path.exists():
        return

    fallback_ts = max(0.0, timestamp - 0.100)
    if fallback_ts < timestamp:
        run_command(build_cmd(fallback_ts), verbose=verbose)
        if output_path.exists():
            return

    raise FramescribeError(f"failed to extract frame at {timestamp:.3f}s into {output_path}")


def extract_frames_fixed(
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
    """Extract fixed-rate frame sequence via ffmpeg fps filter."""
    frames_dir.mkdir(parents=True, exist_ok=True)

    clip_duration = max(end - start, 0.0)
    if clip_duration <= 0:
        raise FramescribeError("empty clip after applying --start/--end", exit_code=2)

    fps_expr = f"fps=1/{interval}"
    output_pattern = frames_dir / f"frame_%06d.{image_format.value}"

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    if start > 0:
        cmd += ["-ss", f"{start:.6f}"]
    cmd += ["-i", str(video_path), "-t", f"{clip_duration:.6f}", "-vf", fps_expr]
    if image_format == ImageFormat.JPG:
        cmd += ["-q:v", "2"]
    if max_frames is not None:
        cmd += ["-frames:v", str(max_frames)]
    cmd += [str(output_pattern)]

    run_command(cmd, verbose=verbose)

    frame_paths = sorted(frames_dir.glob(f"*.{image_format.value}"))
    if not frame_paths:
        raise FramescribeError("no frames were extracted by ffmpeg")

    samples: list[FrameSample] = []
    for index, frame_path in enumerate(frame_paths):
        timestamp = start + (index * interval)
        if timestamp >= end:
            break
        samples.append(FrameSample(timestamp_sec=timestamp, frame_path=frame_path))

    if not samples:
        raise FramescribeError("fixed sampling produced no frame samples")

    return samples


def extract_frames_at_timestamps(
    video_path: Path,
    frames_dir: Path,
    *,
    timestamps: Sequence[float],
    image_format: ImageFormat,
    verbose: bool,
) -> list[FrameSample]:
    """Extract frames for explicit timestamp list."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    samples: list[FrameSample] = []

    for index, timestamp in enumerate(timestamps):
        frame_path = frames_dir / f"frame_{index + 1:06d}.{image_format.value}"
        extract_frame_at_timestamp(
            video_path,
            timestamp=timestamp,
            output_path=frame_path,
            image_format=image_format,
            verbose=verbose,
        )
        samples.append(FrameSample(timestamp_sec=timestamp, frame_path=frame_path))

    if not samples:
        raise FramescribeError("timestamp-based extraction produced no frame samples")

    return samples
