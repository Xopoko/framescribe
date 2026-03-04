"""Codex CLI provider implementation."""

from __future__ import annotations

import shlex
import shutil
from pathlib import Path

from ..models import FramescribeError, ProviderHealth, ProviderRunOptions
from ..video import run_command


class CodexProvider:
    """Analyze frames through `codex exec --image`."""

    @staticmethod
    def _is_path_like(value: str) -> bool:
        return "/" in value or value.startswith(".") or value.startswith("~")

    @classmethod
    def _resolve_executable(cls, binary: str) -> Path | None:
        if cls._is_path_like(binary):
            candidate = Path(binary).expanduser().resolve()
            return candidate if candidate.exists() else None
        resolved = shutil.which(binary)
        return Path(resolved) if resolved is not None else None

    def healthcheck(self, run_options: ProviderRunOptions) -> ProviderHealth:
        resolved = self._resolve_executable(run_options.codex_path)
        if resolved is None:
            return ProviderHealth(
                ok=False,
                details=(
                    f"Codex CLI not found for --codex-path={run_options.codex_path!r}. "
                    "Install Codex CLI and ensure it is available in PATH."
                ),
            )
        return ProviderHealth(ok=True, details=f"Using Codex binary: {resolved}")

    def build_base_command(self, run_options: ProviderRunOptions) -> list[str]:
        cmd = [
            run_options.codex_path,
            "exec",
            "--dangerously-bypass-approvals-and-sandbox",
            "--skip-git-repo-check",
        ]
        if run_options.model:
            cmd += ["--model", run_options.model]
        if run_options.profile:
            cmd += ["--profile", run_options.profile]
        if run_options.cd:
            cmd += ["-C", run_options.cd]
        return cmd

    def _run(
        self,
        *,
        prompt: str,
        output_path: Path,
        run_options: ProviderRunOptions,
        image_path: Path | None,
        verbose: bool,
    ) -> str:
        cmd = self.build_base_command(run_options)
        if image_path is not None:
            cmd += ["--image", str(image_path)]
        cmd += ["--output-last-message", str(output_path), "-"]

        process = run_command(cmd, stdin_text=prompt, verbose=verbose, check=False)
        if process.returncode != 0:
            details = process.stderr.strip() or process.stdout.strip() or (
                f"codex exited with code {process.returncode}"
            )
            quoted = " ".join(shlex.quote(part) for part in cmd)
            raise FramescribeError(
                f"Codex execution failed: {details}\n"
                f"Command: {quoted}\n"
                "Ensure Codex CLI is installed and authenticated (run `codex login`)."
            )

        if not output_path.exists():
            raise FramescribeError(f"Codex did not create expected output file: {output_path}")

        result = output_path.read_text(encoding="utf-8").strip()
        if not result:
            raise FramescribeError(f"Codex returned an empty response for: {output_path}")

        return result

    def analyze_frame(
        self,
        *,
        image_path: Path,
        prompt: str,
        output_path: Path,
        run_options: ProviderRunOptions,
        verbose: bool,
    ) -> str:
        return self._run(
            prompt=prompt,
            output_path=output_path,
            run_options=run_options,
            image_path=image_path,
            verbose=verbose,
        )

    def summarize(
        self,
        *,
        prompt: str,
        output_path: Path,
        run_options: ProviderRunOptions,
        verbose: bool,
    ) -> str:
        return self._run(
            prompt=prompt,
            output_path=output_path,
            run_options=run_options,
            image_path=None,
            verbose=verbose,
        )
