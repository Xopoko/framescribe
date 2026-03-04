from __future__ import annotations

from pathlib import Path

from framescribe.models import ProviderRunOptions
from framescribe.providers.codex import CodexProvider


def test_analyze_frame_invocation(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_run_command(cmd, *, stdin_text=None, verbose=False, check=True):
        captured["cmd"] = list(cmd)
        captured["prompt"] = stdin_text
        output_index = cmd.index("--output-last-message") + 1
        output_file = Path(cmd[output_index])
        output_file.write_text("SHORT_EVENT: test\n", encoding="utf-8")

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return Result()

    monkeypatch.setattr("framescribe.providers.codex.run_command", fake_run_command)

    provider = CodexProvider()
    output_path = tmp_path / "last.txt"
    image_path = tmp_path / "frame.png"
    image_path.write_text("x", encoding="utf-8")

    text = provider.analyze_frame(
        image_path=image_path,
        prompt="Describe frame",
        output_path=output_path,
        run_options=ProviderRunOptions(codex_path="codex"),
        verbose=False,
    )

    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    assert "--image" in cmd
    assert str(image_path) in cmd
    assert "--output-last-message" in cmd
    assert text.startswith("SHORT_EVENT")
