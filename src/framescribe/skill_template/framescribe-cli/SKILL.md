---
name: framescribe-cli
description: Run and operate the Framescribe video-to-report CLI end to end. Use when a user asks to analyze local video files frame-by-frame, generate timeline/summary artifacts, tune frame sampling (adaptive or fixed), control output location, troubleshoot ffmpeg/ffprobe/codex dependencies, or run with a custom Codex binary path.
---

# Framescribe CLI

## Overview

Use `framescribe` to convert a local video into frame-by-frame analysis, timeline outputs, and a final summary.

Prefer default behavior unless the user asks for specific tuning.

## Quick Start

Run minimal command:

```bash
framescribe /absolute/path/to/video.mov
```

Run with explicit output:

```bash
framescribe /absolute/path/to/video.mov --output /absolute/path/to/result
```

Remember default output when `--output` is omitted:

```text
~/.framescribe/<video_stem>/
```

## Execution Workflow

1. Validate prerequisites before running:

```bash
command -v framescribe
command -v ffmpeg
command -v ffprobe
command -v codex
```

2. Confirm input path exists and is a file.
3. Choose the smallest command that satisfies the request:
- Use default adaptive sampling for most runs.
- Use fixed sampling only when user asks for exact cadence.
- Use `--dry-run` when user wants extraction/sanity-check without LLM analysis.
- Use `--max-frames` for quick/cheap exploratory runs.
4. Execute command.
5. Confirm output artifacts:
- `frames/`
- `frame_reports/`
- `timeline.md`
- `timeline.jsonl`
- `summary.md` (unless `--no-summary`)
- `run_config.json`
6. Report output directory and key artifacts to the user.

## Command Patterns

Use adaptive defaults:

```bash
framescribe /path/video.mov --overwrite
```

Use fixed interval sampling:

```bash
framescribe /path/video.mov --sampling-mode fixed --interval 1.0 --overwrite
```

Tune adaptive sampling:

```bash
framescribe /path/video.mov \
  --sampling-mode adaptive \
  --adaptive-min-interval 0.4 \
  --adaptive-max-interval 2.0 \
  --adaptive-scene-threshold 0.12 \
  --overwrite
```

Use custom Codex binary path:

```bash
framescribe /path/video.mov --codex-path /absolute/path/to/codex --overwrite
```

Run extraction only:

```bash
framescribe /path/video.mov --dry-run --overwrite
```

## Troubleshooting Checklist

If run fails, check in this order:

1. Missing tools:
- Install/add to `PATH`: `ffmpeg`, `ffprobe`, `codex`, `framescribe`.
2. Codex auth/provider failure:
- Run `codex login` and retry.
3. Output directory exists:
- Re-run with `--overwrite` or choose another `--output` path.
4. Invalid range/sampling args:
- Ensure `--end > --start`.
- Ensure intervals and thresholds are positive.
5. Very long or expensive runs:
- Start with `--max-frames` or `--dry-run`, then run full analysis.

## Output Interpretation

Use `timeline.md` for human-readable sequence, `timeline.jsonl` for machine processing, and `summary.md` for final narrative.

If `summary.md` is missing, check whether `--no-summary` was used.
