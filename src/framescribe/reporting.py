"""Prompting and report-generation helpers."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import cast


def parse_short_event(report_text: str) -> str:
    """Extract SHORT_EVENT line from model output, with fallback."""
    match = re.search(r"^SHORT_EVENT:\s*(.+)$", report_text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()

    for line in report_text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:180]
    return "(empty model response)"


def sample_evenly(items: Sequence[str], max_items: int) -> list[str]:
    """Downsample lines while preserving timeline coverage."""
    if len(items) <= max_items:
        return list(items)
    if max_items <= 1:
        return [items[0]]

    sampled: list[str] = []
    for index in range(max_items):
        position = round(index * (len(items) - 1) / (max_items - 1))
        sampled.append(items[position])
    return sampled


def build_frame_prompt(
    *,
    language: str,
    frame_index: int,
    total_frames: int,
    timestamp_seconds: float,
    sampling_note: str,
    previous_short_event: str | None,
) -> str:
    """Prompt for detailed single-frame scene analysis."""
    prev = previous_short_event or "no previous frame"
    return (
        "You are analyzing one frame from a video. This is not OCR-only: "
        "describe the full visual scene and observed actions.\n"
        f"Output language: {language}.\n"
        f"Frame: {frame_index + 1}/{total_frames}.\n"
        f"Timestamp: {timestamp_seconds:.2f}s.\n"
        f"{sampling_note}\n"
        f"Previous frame summary: {prev}.\n\n"
        "Requirements:\n"
        "1) Describe the visible scene in detail (UI, objects, actions, state changes).\n"
        "2) Describe what changed compared with the previous frame.\n"
        "3) Extract visible text.\n"
        "4) Do not invent facts; mark uncertain observations as assumptions.\n\n"
        "Reply in this strict format:\n"
        "SHORT_EVENT: <short event phrase, up to about 18 words>\n"
        "DETAILS:\n"
        "- Visible scene: ...\n"
        "- Changes from previous frame: ...\n"
        "- Visible text: ...\n"
        "- Additional notes: ...\n"
    )


def build_summary_prompt(
    *,
    language: str,
    event_lines: Iterable[str],
    was_sampled: bool,
    total_events: int,
    used_events: int,
    sampling_description: str,
) -> str:
    """Prompt for final timeline summary synthesis."""
    sample_note = (
        f"Note: only {used_events} of {total_events} events are included in this summary input "
        "because the timeline is large.\n"
        if was_sampled
        else ""
    )
    events_blob = "\n".join(event_lines)

    return (
        "Below is a frame-by-frame timeline extracted from a video.\n"
        f"Output language: {language}.\n"
        f"Sampling mode: {sampling_description}.\n"
        f"{sample_note}\n"
        "Events:\n"
        f"{events_blob}\n\n"
        "Generate a markdown report with these sections:\n"
        "1) Timeline (key steps over time).\n"
        "2) User/object actions.\n"
        "3) Visible UI/scene details and on-screen text.\n"
        "4) Uncertainties and sampling limitations.\n"
        "5) Final summary (5-8 sentences).\n"
    )


def write_timeline_markdown(
    output_path: Path,
    *,
    video_path: Path,
    sampling_description: str,
    start: float,
    end: float,
    records: Sequence[dict[str, object]],
) -> None:
    """Write a human-readable timeline report."""
    lines = [
        "# Frame-by-Frame Timeline",
        "",
        f"- Source video: `{video_path}`",
        f"- Sampling: `{sampling_description}`",
        f"- Range: `{start:.3f}` .. `{end:.3f}` sec",
        f"- Frames analyzed: `{len(records)}`",
        "",
    ]

    for record in records:
        timestamp = cast(float, record["timestamp_sec"])
        frame_name = cast(str, record["frame_name"])
        analysis = cast(str, record["analysis"])
        lines += [
            f"## t={timestamp:.2f}s ({frame_name})",
            "",
            analysis,
            "",
        ]

    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_timeline_jsonl(output_path: Path, records: Sequence[dict[str, object]]) -> None:
    """Write machine-readable timeline records as JSONL."""
    with output_path.open("w", encoding="utf-8") as out:
        for record in records:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
