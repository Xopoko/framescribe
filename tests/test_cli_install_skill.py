from __future__ import annotations

from pathlib import Path

from framescribe import cli
from framescribe.models import FramescribeError


def test_main_dispatches_install_skill(monkeypatch, tmp_path: Path, capsys) -> None:
    calls: dict[str, object] = {}

    def fake_install_skill(*, repo_path: Path | None, overwrite: bool) -> Path:
        calls["repo_path"] = repo_path
        calls["overwrite"] = overwrite
        return tmp_path / "skills" / "framescribe-cli"

    monkeypatch.setattr(cli, "install_skill", fake_install_skill)

    exit_code = cli.main(["install-skill", "--repo", "/tmp/demo-repo", "--overwrite"])

    assert exit_code == 0
    assert calls["repo_path"] == Path("/tmp/demo-repo")
    assert calls["overwrite"] is True
    assert "Installed skill 'framescribe-cli'" in capsys.readouterr().out


def test_main_install_skill_propagates_validation_error(monkeypatch, capsys) -> None:
    def fake_install_skill(*, repo_path: Path | None, overwrite: bool) -> Path:
        _ = (repo_path, overwrite)
        raise FramescribeError("bad destination", exit_code=2)

    monkeypatch.setattr(cli, "install_skill", fake_install_skill)

    exit_code = cli.main(["install-skill"])

    assert exit_code == 2
    assert "error: bad destination" in capsys.readouterr().err
