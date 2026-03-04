from __future__ import annotations

from pathlib import Path

import pytest

from framescribe.models import FramescribeError
from framescribe.skill_install import SKILL_NAME, install_skill


def test_install_skill_global_uses_codex_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    codex_home = tmp_path / "codex-home"
    monkeypatch.setenv("CODEX_HOME", str(codex_home))

    destination = install_skill(repo_path=None, overwrite=False)

    assert destination == codex_home / "skills" / SKILL_NAME
    assert (destination / "SKILL.md").is_file()
    assert (destination / "agents" / "openai.yaml").is_file()


def test_install_skill_repo_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    destination = install_skill(repo_path=repo, overwrite=False)

    assert destination == repo / "skills" / SKILL_NAME
    assert (destination / "SKILL.md").is_file()


def test_install_skill_requires_overwrite(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    codex_home = tmp_path / "codex-home"
    monkeypatch.setenv("CODEX_HOME", str(codex_home))

    destination = install_skill(repo_path=None, overwrite=False)
    (destination / "marker.txt").write_text("old", encoding="utf-8")

    with pytest.raises(FramescribeError) as err:
        install_skill(repo_path=None, overwrite=False)

    assert err.value.exit_code == 2


def test_install_skill_overwrite_replaces_existing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    codex_home = tmp_path / "codex-home"
    monkeypatch.setenv("CODEX_HOME", str(codex_home))

    destination = install_skill(repo_path=None, overwrite=False)
    marker = destination / "marker.txt"
    marker.write_text("old", encoding="utf-8")

    second_destination = install_skill(repo_path=None, overwrite=True)

    assert second_destination == destination
    assert not marker.exists()


def test_install_skill_missing_repo_path_fails(tmp_path: Path) -> None:
    missing_repo = tmp_path / "missing-repo"

    with pytest.raises(FramescribeError) as err:
        install_skill(repo_path=missing_repo, overwrite=False)

    assert err.value.exit_code == 2
