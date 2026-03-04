from __future__ import annotations

import pytest

from framescribe import cli
from framescribe.models import FramescribeError


def test_invalid_interval_fails() -> None:
    parser = cli.build_parser()
    args = parser.parse_args(["/tmp/video.mp4", "--interval", "0"])
    with pytest.raises(FramescribeError) as err:
        cli._build_options(args)
    assert err.value.exit_code == 2
