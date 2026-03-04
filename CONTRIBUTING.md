# Contributing

Thanks for contributing to Framescribe.

## Prerequisites

- Python 3.10+
- `ffmpeg` and `ffprobe`
- Codex CLI (for provider integration testing)

## Setup

```bash
python -m pip install -e '.[dev]'
```

## Quality Gates

```bash
make lint
make test
make build
```

## Pull Request Guidelines

- Keep changes focused and well-scoped.
- Add or update tests for behavior changes.
- Keep CLI output and docs in English.
- Update `CHANGELOG.md` when user-facing behavior changes.
