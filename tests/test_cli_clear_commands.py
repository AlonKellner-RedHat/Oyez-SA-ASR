# Edited by Cursor: split from test_cli (lintok; no new exclusions).
"""Tests for clear subcommands (help and --force)."""

import tempfile
from pathlib import Path

from typer.testing import CliRunner

from oyez_sa_asr.cli import app
from tests.test_cli_helpers import strip_ansi

runner = CliRunner()


class TestClearCommands:
    """Tests for clear subcommands."""

    def test_clear_subcommand_exists(self) -> None:
        result = runner.invoke(app, ["clear", "--help"])
        assert result.exit_code == 0
        assert "index" in result.output
        assert "cases" in result.output

    def test_clear_index_help(self) -> None:
        result = runner.invoke(app, ["clear", "index", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert (
            "--cache-dir" in output and "--data-dir" in output and "--force" in output
        )

    def test_clear_cases_help(self) -> None:
        result = runner.invoke(app, ["clear", "cases", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert (
            "--cache-dir" in output and "--data-dir" in output and "--force" in output
        )

    def test_clear_index_removes_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache" / "index"
            data_dir = Path(tmpdir) / "data" / "index"
            cache_dir.mkdir(parents=True)
            (cache_dir / "test.json").write_text("{}")
            data_dir.mkdir(parents=True)
            (data_dir / "cases_index.json").write_text("{}")
            result = runner.invoke(
                app,
                [
                    "clear",
                    "index",
                    "--cache-dir",
                    str(cache_dir),
                    "--data-dir",
                    str(data_dir),
                    "--force",
                ],
            )
            assert result.exit_code == 0
            assert not cache_dir.exists()
            assert not data_dir.exists()

    def test_clear_cases_removes_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache" / "cases"
            data_dir = Path(tmpdir) / "data" / "cases"
            cache_dir.mkdir(parents=True)
            (cache_dir / "meta").mkdir()
            (cache_dir / "meta" / "abc.json").write_text("{}")
            data_dir.mkdir(parents=True)
            (data_dir / "case1.json").write_text("{}")
            result = runner.invoke(
                app,
                [
                    "clear",
                    "cases",
                    "--cache-dir",
                    str(cache_dir),
                    "--data-dir",
                    str(data_dir),
                    "--force",
                ],
            )
            assert result.exit_code == 0
            assert not cache_dir.exists()
            assert not data_dir.exists()

    def test_clear_handles_nonexistent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "nonexistent_cache"
            data_dir = Path(tmpdir) / "nonexistent_data"
            result = runner.invoke(
                app,
                [
                    "clear",
                    "index",
                    "--cache-dir",
                    str(cache_dir),
                    "--data-dir",
                    str(data_dir),
                    "--force",
                ],
            )
            assert result.exit_code == 0
            assert "does not exist" in result.output
