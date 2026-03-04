"""Core data models used by Framescribe."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class FramescribeError(Exception):
    """Domain error with a CLI-friendly exit code."""

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class ProviderName(str, Enum):
    """Available analysis providers."""

    CODEX = "codex"


class SamplingMode(str, Enum):
    """Video frame sampling strategy."""

    FIXED = "fixed"
    ADAPTIVE = "adaptive"


class ImageFormat(str, Enum):
    """Image format for extracted frames."""

    PNG = "png"
    JPG = "jpg"


@dataclass(frozen=True)
class ProviderRunOptions:
    """Runtime configuration passed to a provider backend."""

    codex_path: str = "codex"
    model: str | None = None
    profile: str | None = None
    cd: str | None = None


@dataclass(frozen=True)
class ProviderHealth:
    """Provider preflight result."""

    ok: bool
    details: str


@dataclass(frozen=True)
class FrameSample:
    """Single extracted frame and its timestamp."""

    timestamp_sec: float
    frame_path: Path


@dataclass(frozen=True)
class CliOptions:
    """Validated CLI options converted into strongly typed config."""

    video: Path
    output: Path | None
    overwrite: bool
    dry_run: bool

    provider: ProviderName
    provider_run_options: ProviderRunOptions

    sampling_mode: SamplingMode
    interval: float
    adaptive_min_interval: float
    adaptive_max_interval: float
    adaptive_scene_threshold: float
    start: float
    end: float | None
    max_frames: int | None

    summary_max_events: int
    report_language: str
    image_format: ImageFormat
    no_summary: bool
    verbose: bool
