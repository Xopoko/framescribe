"""CLI entrypoint for Framescribe."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .app import run
from .models import (
    CliOptions,
    FramescribeError,
    ImageFormat,
    ProviderName,
    ProviderRunOptions,
    SamplingMode,
)


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for `framescribe` command."""
    parser = argparse.ArgumentParser(
        prog="framescribe",
        description=(
            "Analyze a video frame-by-frame using a vision CLI provider and "
            "generate timeline and summary reports."
        ),
    )

    parser.add_argument("video", help="Path to input video file")

    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output directory (default: ~/.framescribe/<video_stem>/)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace output directory if it exists",
    )
    parser.add_argument("--dry-run", action="store_true", help="Extract/sample frames only")

    parser.add_argument(
        "--provider",
        choices=[member.value for member in ProviderName],
        default=ProviderName.CODEX.value,
        help="Analysis provider backend (default: codex)",
    )
    parser.add_argument(
        "--codex-path",
        default="codex",
        help="Path or executable name for Codex CLI (default: codex)",
    )
    parser.add_argument("--codex-model", default=None, help="Optional Codex model")
    parser.add_argument("--codex-profile", default=None, help="Optional Codex profile")
    parser.add_argument(
        "--codex-cd",
        default=None,
        help="Optional working directory for Codex (-C)",
    )

    parser.add_argument(
        "--sampling-mode",
        choices=[member.value for member in SamplingMode],
        default=SamplingMode.ADAPTIVE.value,
        help="Frame sampling strategy (default: adaptive)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Fixed mode interval in seconds",
    )
    parser.add_argument(
        "--adaptive-min-interval",
        type=float,
        default=0.4,
        help="Adaptive mode minimum interval in seconds",
    )
    parser.add_argument(
        "--adaptive-max-interval",
        type=float,
        default=2.0,
        help="Adaptive mode maximum interval in seconds",
    )
    parser.add_argument(
        "--adaptive-scene-threshold",
        type=float,
        default=0.12,
        help="Adaptive scene-change threshold for ffmpeg select(scene)",
    )
    parser.add_argument("--start", type=float, default=0.0, help="Start offset in seconds")
    parser.add_argument("--end", type=float, default=None, help="End offset in seconds")
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Cap number of analyzed frames",
    )

    parser.add_argument(
        "--summary-max-events",
        type=int,
        default=300,
        help="Maximum timeline events included in summary prompt",
    )
    parser.add_argument(
        "--report-language",
        default="en",
        help="Language used for generated reports and prompts (default: en)",
    )
    parser.add_argument(
        "--image-format",
        choices=[member.value for member in ImageFormat],
        default=ImageFormat.PNG.value,
        help="Extracted frame format",
    )
    parser.add_argument("--no-summary", action="store_true", help="Skip final summary step")
    parser.add_argument("--verbose", action="store_true", help="Print underlying shell commands")

    parser.add_argument("--version", action="version", version=f"framescribe {__version__}")

    return parser


def _build_options(args: argparse.Namespace) -> CliOptions:
    if args.interval <= 0:
        raise FramescribeError("--interval must be > 0", exit_code=2)
    if args.adaptive_min_interval <= 0:
        raise FramescribeError("--adaptive-min-interval must be > 0", exit_code=2)
    if args.adaptive_max_interval <= 0:
        raise FramescribeError("--adaptive-max-interval must be > 0", exit_code=2)
    if args.adaptive_min_interval > args.adaptive_max_interval:
        raise FramescribeError(
            "--adaptive-min-interval must be <= --adaptive-max-interval", exit_code=2
        )
    if args.adaptive_scene_threshold <= 0:
        raise FramescribeError("--adaptive-scene-threshold must be > 0", exit_code=2)
    if args.start < 0:
        raise FramescribeError("--start must be >= 0", exit_code=2)
    if args.end is not None and args.end <= args.start:
        raise FramescribeError("--end must be greater than --start", exit_code=2)
    if args.max_frames is not None and args.max_frames <= 0:
        raise FramescribeError("--max-frames must be > 0", exit_code=2)
    if args.summary_max_events <= 0:
        raise FramescribeError("--summary-max-events must be > 0", exit_code=2)

    return CliOptions(
        video=Path(args.video).expanduser().resolve(),
        output=Path(args.output).expanduser() if args.output else None,
        overwrite=bool(args.overwrite),
        dry_run=bool(args.dry_run),
        provider=ProviderName(args.provider),
        provider_run_options=ProviderRunOptions(
            codex_path=args.codex_path,
            model=args.codex_model,
            profile=args.codex_profile,
            cd=args.codex_cd,
        ),
        sampling_mode=SamplingMode(args.sampling_mode),
        interval=float(args.interval),
        adaptive_min_interval=float(args.adaptive_min_interval),
        adaptive_max_interval=float(args.adaptive_max_interval),
        adaptive_scene_threshold=float(args.adaptive_scene_threshold),
        start=float(args.start),
        end=float(args.end) if args.end is not None else None,
        max_frames=int(args.max_frames) if args.max_frames is not None else None,
        summary_max_events=int(args.summary_max_events),
        report_language=str(args.report_language),
        image_format=ImageFormat(args.image_format),
        no_summary=bool(args.no_summary),
        verbose=bool(args.verbose),
    )


def main(argv: list[str] | None = None) -> int:
    """CLI main function used by console_scripts and __main__."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        options = _build_options(args)
        run(options)
        return 0
    except FramescribeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
