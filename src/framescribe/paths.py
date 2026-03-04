"""Path and filesystem helpers for Framescribe."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from .models import FramescribeError


def slugify_video_stem(stem: str) -> str:
    """Convert a video filename stem into a safe output directory name."""
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-").lower()
    return slug or "video"


def default_output_dir(video_path: Path) -> Path:
    """Return default output path under ~/.framescribe/<video_stem>."""
    return (Path.home() / ".framescribe" / slugify_video_stem(video_path.stem)).resolve()


def prepare_output_dir(video_path: Path, output: Path | None, overwrite: bool) -> Path:
    """Create output directory or replace it when overwrite is allowed."""
    destination = (
        output.expanduser().resolve() if output is not None else default_output_dir(video_path)
    )

    if destination.exists():
        if not overwrite:
            raise FramescribeError(
                f"output directory already exists: {destination} (use --overwrite to replace)"
            )
        shutil.rmtree(destination)

    destination.mkdir(parents=True, exist_ok=True)
    return destination
