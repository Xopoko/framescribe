"""Provider interfaces for vision analysis backends."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..models import ProviderHealth, ProviderRunOptions


class Provider(Protocol):
    """Common interface implemented by backend providers."""

    def analyze_frame(
        self,
        *,
        image_path: Path,
        prompt: str,
        output_path: Path,
        run_options: ProviderRunOptions,
        verbose: bool,
    ) -> str:
        """Analyze a single frame and return textual output."""

    def summarize(
        self,
        *,
        prompt: str,
        output_path: Path,
        run_options: ProviderRunOptions,
        verbose: bool,
    ) -> str:
        """Create a final summary and return textual output."""

    def healthcheck(self, run_options: ProviderRunOptions) -> ProviderHealth:
        """Check whether provider binary/configuration is usable."""
