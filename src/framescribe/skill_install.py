"""Install bundled Framescribe Codex skill into target directories."""

from __future__ import annotations

import os
import shutil
from importlib import resources
from importlib.abc import Traversable
from pathlib import Path

from .models import FramescribeError

SKILL_NAME = "framescribe-cli"


def resolve_global_skills_root() -> Path:
    """Resolve global Codex skills root from environment."""
    codex_home = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
    return codex_home / "skills"


def resolve_skill_destination(repo_path: Path | None) -> Path:
    """Resolve destination directory for skill installation."""
    if repo_path is None:
        return resolve_global_skills_root() / SKILL_NAME

    repo_root = repo_path.expanduser().resolve()
    if not repo_root.exists():
        raise FramescribeError(f"repository path not found: {repo_root}", exit_code=2)
    if not repo_root.is_dir():
        raise FramescribeError(f"repository path is not a directory: {repo_root}", exit_code=2)

    return repo_root / "skills" / SKILL_NAME


def _copy_tree(source: Traversable, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        target = destination / child.name
        if child.is_dir():
            _copy_tree(child, target)
        else:
            target.write_bytes(child.read_bytes())


def install_skill(*, repo_path: Path | None, overwrite: bool) -> Path:
    """Install bundled `framescribe-cli` skill and return destination path."""
    template = resources.files("framescribe").joinpath("skill_template").joinpath(SKILL_NAME)
    if not template.is_dir():
        raise FramescribeError("bundled skill template not found in package", exit_code=1)

    destination = resolve_skill_destination(repo_path)
    if destination.exists():
        if not overwrite:
            raise FramescribeError(
                f"skill destination already exists: {destination}. "
                "Use --overwrite to replace it.",
                exit_code=2,
            )
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
        else:
            shutil.rmtree(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)
    _copy_tree(template, destination)
    return destination
