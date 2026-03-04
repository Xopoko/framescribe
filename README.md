# Framescribe

Framescribe is a production-ready CLI that turns a video into a structured, frame-by-frame report.

It samples frames from a video, sends each frame to a vision-capable CLI provider (Codex in v0.1.0), and generates:
- detailed per-frame analysis
- a timeline report
- a final summary

## Features

- Installable CLI (`framescribe`) via `pipx` / `pip`
- Sensible defaults: usually only pass a video path
- Adaptive sampling (default) and fixed-interval sampling
- Provider abstraction ready for future providers (Claude/Gemini roadmap)
- Machine-readable output (`timeline.jsonl`) and markdown reports

## Requirements

- Python 3.10+
- `ffmpeg` and `ffprobe` available in `PATH`
- Codex CLI installed and authenticated (`codex login`)

## Installation

### Install with pipx (recommended)

```bash
pipx install .
```

### Install with pip

```bash
python -m pip install .
```

## Quickstart

Minimal run:

```bash
framescribe /path/to/video.mov
```

Custom output directory:

```bash
framescribe /path/to/video.mov --output /path/to/result
```

Default output path (when `--output` is omitted):

```text
~/.framescribe/<video_stem>/
```

## Bundled Codex Skill

The repository ships a reusable Codex skill at `skills/framescribe-cli`.

Install it globally into Codex skills:

```bash
framescribe install-skill
```

Install it into another repository:

```bash
framescribe install-skill --repo /path/to/repo
```

Replace existing installed skill:

```bash
framescribe install-skill --overwrite
```

## CLI Usage

```bash
framescribe <video> [options]
framescribe install-skill [--repo <path>] [--overwrite]
```

### Core options

- `-o, --output <dir>`: output directory (default `~/.framescribe/<video_stem>/`)
- `--overwrite`: replace output directory if it exists
- `--dry-run`: extract/sample frames only (no provider calls)

### Provider options

- `--provider codex` (default: `codex`)
- `--codex-path <path>` (default: `codex`)
- `--codex-model <model>`
- `--codex-profile <profile>`
- `--codex-cd <dir>`

### Sampling options

- `--sampling-mode {fixed,adaptive}` (default: `adaptive`)
- `--interval <sec>` (fixed mode, default: `1.0`)
- `--adaptive-min-interval <sec>` (default: `0.4`)
- `--adaptive-max-interval <sec>` (default: `2.0`)
- `--adaptive-scene-threshold <float>` (default: `0.12`)
- `--start <sec>` (default: `0`)
- `--end <sec>` (default: full duration)
- `--max-frames <n>`

### Reporting options

- `--summary-max-events <n>` (default: `300`)
- `--report-language <lang>` (default: `en`)
- `--image-format {png,jpg}` (default: `png`)
- `--no-summary`
- `--verbose`

### Skill installation command

- `install-skill`: install bundled `framescribe-cli` Codex skill
- `--repo <path>`: install to `<repo>/skills/framescribe-cli` instead of global Codex skills
- `--overwrite`: replace target skill directory if it already exists

## Examples

Fixed sampling every second:

```bash
framescribe /path/to/video.mov --sampling-mode fixed --interval 1
```

Adaptive sampling with tuned thresholds:

```bash
framescribe /path/to/video.mov \
  --sampling-mode adaptive \
  --adaptive-min-interval 0.4 \
  --adaptive-max-interval 2.0 \
  --adaptive-scene-threshold 0.12
```

Use a custom Codex binary path:

```bash
framescribe /path/to/video.mov --codex-path /usr/local/bin/codex
```

## Output Structure

Framescribe writes the following artifacts:

```text
<output>/
  frames/
  frame_reports/
    frame_000001.md
    frame_000001.last_message.txt
    ...
  timeline.md
  timeline.jsonl
  summary.md
  run_config.json
```

## Exit Codes

- `0`: success
- `2`: invalid arguments / validation errors
- `1`: runtime/provider/tool errors

## Troubleshooting

### `required tool not found in PATH: ffmpeg` / `ffprobe`
Install FFmpeg and ensure both tools are in `PATH`.

### `Codex CLI not found`
Install Codex CLI or pass `--codex-path` explicitly.

### `Codex execution failed`
Authenticate first:

```bash
codex login
```

## Development

Install dev dependencies:

```bash
python -m pip install -e '.[dev]'
```

Run checks:

```bash
make lint
make test
make build
```

## Provider Roadmap

`v0.1.0` ships with `codex` provider only.

The project architecture is provider-ready and will be extended with additional provider backends in future versions.

## License

MIT. See [LICENSE](./LICENSE).
