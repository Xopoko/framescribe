"""Application service that runs the full Framescribe pipeline."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .models import CliOptions, FramescribeError, ProviderName, SamplingMode
from .paths import prepare_output_dir
from .progress import run_with_heartbeat
from .providers import CodexProvider
from .providers.base import Provider
from .reporting import (
    build_frame_prompt,
    build_summary_prompt,
    parse_short_event,
    sample_evenly,
    write_timeline_jsonl,
    write_timeline_markdown,
)
from .sampling import build_adaptive_timestamps
from .video import (
    detect_scene_change_timestamps,
    ensure_tool,
    extract_frames_at_timestamps,
    extract_frames_fixed,
    get_video_duration_seconds,
)

HEARTBEAT_SECONDS = 20.0


def _sampling_description(options: CliOptions) -> str:
    if options.sampling_mode == SamplingMode.ADAPTIVE:
        return (
            f"adaptive(min={options.adaptive_min_interval:.3f}s, "
            f"max={options.adaptive_max_interval:.3f}s, "
            f"scene_threshold={options.adaptive_scene_threshold:.3f})"
        )
    return f"fixed(interval={options.interval:.3f}s)"


def _create_provider(name: ProviderName) -> Provider:
    if name == ProviderName.CODEX:
        return CodexProvider()
    raise FramescribeError(f"unsupported provider: {name}", exit_code=2)


def _validate_inputs(options: CliOptions) -> None:
    if not options.video.is_file():
        raise FramescribeError(f"video file not found: {options.video}", exit_code=2)


def _ensure_dependencies(options: CliOptions, provider: Provider) -> None:
    ensure_tool("ffmpeg")
    ensure_tool("ffprobe")

    if options.dry_run:
        return

    health = provider.healthcheck(options.provider_run_options)
    if not health.ok:
        raise FramescribeError(health.details)


def run(options: CliOptions) -> Path:
    """Execute the pipeline and return output directory path."""
    _validate_inputs(options)
    provider = _create_provider(options.provider)
    _ensure_dependencies(options, provider)

    duration = get_video_duration_seconds(options.video, verbose=options.verbose)
    end = duration if options.end is None else min(options.end, duration)
    if end <= options.start:
        raise FramescribeError("--end must be greater than --start", exit_code=2)

    output_dir = prepare_output_dir(options.video, options.output, options.overwrite)
    frames_dir = output_dir / "frames"
    frame_reports_dir = output_dir / "frame_reports"
    frame_reports_dir.mkdir(parents=True, exist_ok=True)

    timeline_jsonl_path = output_dir / "timeline.jsonl"
    timeline_md_path = output_dir / "timeline.md"
    summary_md_path = output_dir / "summary.md"
    run_config_path = output_dir / "run_config.json"

    sampling_description = _sampling_description(options)

    if options.sampling_mode == SamplingMode.ADAPTIVE:
        scene_timestamps = detect_scene_change_timestamps(
            options.video,
            start=options.start,
            end=end,
            threshold=options.adaptive_scene_threshold,
            verbose=options.verbose,
        )
        timestamps = build_adaptive_timestamps(
            start=options.start,
            end=end,
            min_interval=options.adaptive_min_interval,
            max_interval=options.adaptive_max_interval,
            scene_timestamps=scene_timestamps,
        )
        if options.max_frames is not None:
            timestamps = timestamps[: options.max_frames]
        if not timestamps:
            raise FramescribeError("adaptive sampling produced no timestamps")

        frame_samples = extract_frames_at_timestamps(
            options.video,
            frames_dir,
            timestamps=timestamps,
            image_format=options.image_format,
            verbose=options.verbose,
        )
    else:
        frame_samples = extract_frames_fixed(
            options.video,
            frames_dir,
            interval=options.interval,
            start=options.start,
            end=end,
            image_format=options.image_format,
            max_frames=options.max_frames,
            verbose=options.verbose,
        )

    run_config = {
        "video": str(options.video),
        "duration_sec": duration,
        "range_start_sec": options.start,
        "range_end_sec": end,
        "provider": options.provider.value,
        "sampling_mode": options.sampling_mode.value,
        "sampling_description": sampling_description,
        "fixed_interval_sec": options.interval,
        "adaptive_min_interval_sec": options.adaptive_min_interval,
        "adaptive_max_interval_sec": options.adaptive_max_interval,
        "adaptive_scene_threshold": options.adaptive_scene_threshold,
        "frames_extracted": len(frame_samples),
        "image_format": options.image_format.value,
        "report_language": options.report_language,
        "dry_run": options.dry_run,
        "generated_at": dt.datetime.now().isoformat(),
    }
    run_config_path.write_text(
        json.dumps(run_config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if options.dry_run:
        print(f"Done (dry-run). Extracted {len(frame_samples)} frames into: {frames_dir}")
        print(f"Sampling: {sampling_description}")
        print(f"Run config: {run_config_path}")
        return output_dir

    print(
        "Note: frame-by-frame analysis can take time. With the current provider setup, "
        "a 10-second video can take over 1 minute. Wait for progress lines; longer videos "
        "usually take longer. Heartbeat lines appear roughly every 20 seconds while waiting."
    )

    records: list[dict[str, object]] = []
    previous_short_event: str | None = None
    previous_timestamp: float | None = None

    for index, sample in enumerate(frame_samples):
        frame_path = sample.frame_path
        timestamp = sample.timestamp_sec
        frame_report_path = frame_reports_dir / f"frame_{index + 1:06d}.md"
        frame_raw_output_path = frame_reports_dir / f"frame_{index + 1:06d}.last_message.txt"

        if options.sampling_mode == SamplingMode.ADAPTIVE:
            if previous_timestamp is None:
                sampling_note = "Adaptive sampling: this is the first analyzed frame."
            else:
                delta = timestamp - previous_timestamp
                sampling_note = f"Adaptive sampling: {delta:.2f}s since previous sampled frame."
        else:
            sampling_note = f"Fixed sampling interval: {options.interval:.2f}s."

        prompt = build_frame_prompt(
            language=options.report_language,
            frame_index=index,
            total_frames=len(frame_samples),
            timestamp_seconds=timestamp,
            sampling_note=sampling_note,
            previous_short_event=previous_short_event,
        )

        print(f"[{index + 1}/{len(frame_samples)}] start t={timestamp:.2f}s")

        def _analyze_current_frame(
            frame: Path = frame_path,
            frame_prompt: str = prompt,
            raw_output: Path = frame_raw_output_path,
        ) -> str:
            return provider.analyze_frame(
                image_path=frame,
                prompt=frame_prompt,
                output_path=raw_output,
                run_options=options.provider_run_options,
                verbose=options.verbose,
            )

        analysis_text, frame_elapsed = run_with_heartbeat(
            task_name=f"frame {index + 1}/{len(frame_samples)}",
            work=_analyze_current_frame,
            heartbeat_seconds=HEARTBEAT_SECONDS,
        )
        frame_report_path.write_text(analysis_text + "\n", encoding="utf-8")
        short_event = parse_short_event(analysis_text)

        previous_short_event = short_event
        previous_timestamp = timestamp

        records.append(
            {
                "index": index,
                "timestamp_sec": timestamp,
                "frame_path": str(frame_path),
                "frame_name": frame_path.name,
                "sampling_mode": options.sampling_mode.value,
                "short_event": short_event,
                "analysis": analysis_text,
            }
        )

        print(
            f"[{index + 1}/{len(frame_samples)}] done "
            f"t={timestamp:.2f}s in {frame_elapsed:.1f}s -> {short_event}"
        )

    write_timeline_jsonl(timeline_jsonl_path, records)
    write_timeline_markdown(
        timeline_md_path,
        video_path=options.video,
        sampling_description=sampling_description,
        start=options.start,
        end=end,
        records=records,
    )

    if options.no_summary:
        print("Summary step skipped (--no-summary).")
        print(f"Timeline markdown: {timeline_md_path}")
        print(f"Timeline JSONL: {timeline_jsonl_path}")
        return output_dir

    event_lines = [
        f"t={record['timestamp_sec']:.2f}s | {record['short_event']}"
        for record in records
    ]
    sampled_lines = sample_evenly(event_lines, options.summary_max_events)

    print("[summary] start")
    summary_text, summary_elapsed = run_with_heartbeat(
        task_name="summary",
        work=lambda: provider.summarize(
            prompt=build_summary_prompt(
                language=options.report_language,
                event_lines=sampled_lines,
                was_sampled=len(sampled_lines) < len(event_lines),
                total_events=len(event_lines),
                used_events=len(sampled_lines),
                sampling_description=sampling_description,
            ),
            output_path=summary_md_path,
            run_options=options.provider_run_options,
            verbose=options.verbose,
        ),
        heartbeat_seconds=HEARTBEAT_SECONDS,
    )
    summary_md_path.write_text(summary_text + "\n", encoding="utf-8")
    print(f"[summary] done in {summary_elapsed:.1f}s")

    print("Done.")
    print(f"Output dir: {output_dir}")
    print(f"Sampling: {sampling_description}")
    print(f"Frames: {frames_dir}")
    print(f"Per-frame reports: {frame_reports_dir}")
    print(f"Timeline markdown: {timeline_md_path}")
    print(f"Timeline JSONL: {timeline_jsonl_path}")
    print(f"Summary markdown: {summary_md_path}")

    return output_dir
