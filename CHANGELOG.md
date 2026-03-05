# Changelog

## Unreleased

- Added bundled `framescribe-cli` Codex skill to repository (`skills/framescribe-cli`).
- Added `framescribe install-skill` command to install the bundled skill:
  - globally to `$CODEX_HOME/skills/framescribe-cli` (default),
  - or into a local repository via `--repo <path>`.
- Added tests for skill installation and CLI dispatch.
- Added explicit long-run runtime expectations to Framescribe skill docs, including
  guidance that a 10-second video can take more than 1 minute with current provider flow.
- Added concise heartbeat progress logs during long provider waits in frame analysis
  and summary generation to reduce false "hang" diagnosis.

## 0.1.0 - 2026-03-04

- Initial open-source production refactor.
- Added installable `framescribe` CLI package.
- Implemented provider abstraction with Codex provider backend.
- Added adaptive (default) and fixed frame sampling modes.
- Added timeline + summary reporting pipeline.
- Added tests, linting, type checks, and CI workflow.
