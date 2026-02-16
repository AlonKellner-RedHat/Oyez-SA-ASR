# Edited by Cursor: split from test_cli (lintok; no new exclusions).
"""Tests for clear subcommands with confirmation prompts."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from oyez_sa_asr.cli import app

runner = CliRunner()


class TestClearCommandsConfirm:
    """Tests for clear subcommands confirmation flow."""

    def test_clear_index_confirmation_cancelled(self) -> None:
        """Should cancel when user says no to confirmation prompt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache" / "index"
            data_dir = Path(tmpdir) / "data" / "index"
            cache_dir.mkdir(parents=True)
            (cache_dir / "test.json").write_text("{}")
            data_dir.mkdir(parents=True)
            (data_dir / "cases_index.json").write_text("{}")
            with patch("oyez_sa_asr.cli_clear.typer.confirm", return_value=False):
                result = runner.invoke(
                    app,
                    [
                        "clear",
                        "index",
                        "--cache-dir",
                        str(cache_dir),
                        "--data-dir",
                        str(data_dir),
                    ],
                )
                assert result.exit_code == 0
                assert (
                    "Cancelled" in result.output or "cancelled" in result.output.lower()
                )
                assert cache_dir.exists()
                assert data_dir.exists()

    def test_clear_audio_cache_only_with_confirmation(self) -> None:
        """Should clear audio cache with confirmation prompt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache" / "audio"
            cache_dir.mkdir(parents=True)
            (cache_dir / "test.mp3").write_text("test")
            with patch("oyez_sa_asr.cli_clear.typer.confirm", return_value=True):
                result = runner.invoke(
                    app,
                    [
                        "clear",
                        "audio",
                        "--cache-dir",
                        str(cache_dir),
                    ],
                )
                assert result.exit_code == 0
                assert not cache_dir.exists()

    def test_clear_audio_cache_only_confirmation_cancelled(self) -> None:
        """Should cancel audio cache clear when user says no."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache" / "audio"
            cache_dir.mkdir(parents=True)
            (cache_dir / "test.mp3").write_text("test")
            with patch("oyez_sa_asr.cli_clear.typer.confirm", return_value=False):
                result = runner.invoke(
                    app,
                    [
                        "clear",
                        "audio",
                        "--cache-dir",
                        str(cache_dir),
                    ],
                )
                assert result.exit_code == 0
                assert (
                    "Cancelled" in result.output or "cancelled" in result.output.lower()
                )
                assert cache_dir.exists()

    def test_clear_speakers_data_only_with_confirmation(self) -> None:
        """Should clear speakers data with confirmation prompt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data" / "speakers"
            data_dir.mkdir(parents=True)
            (data_dir / "justices").mkdir()
            (data_dir / "justices" / "test.json").write_text("{}")
            with patch("oyez_sa_asr.cli_clear.typer.confirm", return_value=True):
                result = runner.invoke(
                    app,
                    [
                        "clear",
                        "speakers",
                        "--data-dir",
                        str(data_dir),
                    ],
                )
                assert result.exit_code == 0
                assert not data_dir.exists()

    def test_clear_speakers_data_only_confirmation_cancelled(self) -> None:
        """Should cancel speakers clear when user says no."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data" / "speakers"
            data_dir.mkdir(parents=True)
            (data_dir / "justices").mkdir()
            (data_dir / "justices" / "test.json").write_text("{}")
            with patch("oyez_sa_asr.cli_clear.typer.confirm", return_value=False):
                result = runner.invoke(
                    app,
                    [
                        "clear",
                        "speakers",
                        "--data-dir",
                        str(data_dir),
                    ],
                )
                assert result.exit_code == 0
                assert (
                    "Cancelled" in result.output or "cancelled" in result.output.lower()
                )
                assert data_dir.exists()
