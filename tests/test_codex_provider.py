from __future__ import annotations

from pathlib import Path

from framescribe.models import ProviderRunOptions
from framescribe.providers.codex import CodexProvider


def test_build_base_command_with_custom_path() -> None:
    provider = CodexProvider()
    opts = ProviderRunOptions(
        codex_path="/opt/bin/codex",
        model="gpt-5.3-codex",
        profile="fast",
        cd="/tmp/work",
    )

    cmd = provider.build_base_command(opts)
    assert cmd[:4] == [
        "/opt/bin/codex",
        "exec",
        "--dangerously-bypass-approvals-and-sandbox",
        "--skip-git-repo-check",
    ]
    assert "--model" in cmd
    assert "--profile" in cmd
    assert "-C" in cmd


def test_healthcheck_missing_binary() -> None:
    provider = CodexProvider()
    health = provider.healthcheck(ProviderRunOptions(codex_path="/no/such/codex"))
    assert not health.ok
    assert "not found" in health.details.lower()


def test_healthcheck_with_existing_binary(tmp_path: Path) -> None:
    binary = tmp_path / "codex"
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    binary.chmod(0o755)

    provider = CodexProvider()
    health = provider.healthcheck(ProviderRunOptions(codex_path=str(binary)))
    assert health.ok
