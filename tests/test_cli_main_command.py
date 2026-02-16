# Edited by Cursor: split from test_cli (lintok; no new exclusions).
"""Tests for main command."""

from typer.testing import CliRunner

from oyez_sa_asr.cli import app
from tests.test_cli_helpers import strip_ansi

runner = CliRunner()


class TestMainCommand:
    """Tests for main command."""

    def test_main_command(self) -> None:
        """Should execute main command."""
        result = runner.invoke(app, ["main"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "Replace this message" in output or "Typer" in output
