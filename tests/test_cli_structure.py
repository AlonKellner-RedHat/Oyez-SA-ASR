# Edited by Cursor: split from test_cli (lintok; no new exclusions).
"""Tests for CLI command structure."""

from typer.testing import CliRunner

from oyez_sa_asr.cli import app

runner = CliRunner()


class TestCliStructure:
    """Tests for CLI command structure."""

    def test_scrape_subcommand_exists(self) -> None:
        """Should have a scrape subcommand group."""
        result = runner.invoke(app, ["scrape", "--help"])
        assert result.exit_code == 0
        assert "index" in result.output
        assert "cases" in result.output

    def test_process_subcommand_exists(self) -> None:
        """Should have a process subcommand group."""
        result = runner.invoke(app, ["process", "--help"])
        assert result.exit_code == 0
        assert "index" in result.output
