# Edited by Cursor: split from test_cli (lintok; no new exclusions).
"""Tests for process index command."""

from typer.testing import CliRunner

from oyez_sa_asr.cli import app
from tests.test_cli_helpers import strip_ansi

runner = CliRunner()


class TestProcessIndex:
    """Tests for process index command."""

    def test_process_index_help(self) -> None:
        """Should show help for process index."""
        result = runner.invoke(app, ["process", "index", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--cache-dir" in output
        assert "--output" in output

    def test_process_index_default_paths(self) -> None:
        """Should use stage-based default paths."""
        result = runner.invoke(app, ["process", "index", "--help"])
        assert result.exit_code == 0
