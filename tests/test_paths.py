from __future__ import annotations

from pathlib import Path

import pytest

from framescribe.models import FramescribeError
from framescribe.paths import default_output_dir, prepare_output_dir, slugify_video_stem


def test_slugify_video_stem() -> None:
    assert slugify_video_stem("My Video (Final)!") == "my-video-final"


def test_default_output_dir_uses_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    output = default_output_dir(Path("/tmp/My Demo Video.mov"))
    assert output == (tmp_path / ".framescribe" / "my-demo-video").resolve()


def test_prepare_output_dir_requires_overwrite(tmp_path: Path) -> None:
    video = Path("/tmp/sample.mov")
    target = tmp_path / "existing"
    target.mkdir(parents=True)

    with pytest.raises(FramescribeError):
        prepare_output_dir(video, target, overwrite=False)


def test_prepare_output_dir_overwrites(tmp_path: Path) -> None:
    video = Path("/tmp/sample.mov")
    target = tmp_path / "existing"
    target.mkdir(parents=True)
    (target / "old.txt").write_text("old", encoding="utf-8")

    output = prepare_output_dir(video, target, overwrite=True)
    assert output == target.resolve()
    assert not (target / "old.txt").exists()
