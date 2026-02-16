# Edited by Cursor: split from test_cli_process_speakers (lintok; plan).
"""Tests for process speakers help and missing data (TestProcessSpeakersHelp, TestProcessSpeakersMissingData)."""

import tempfile
from pathlib import Path

from oyez_sa_asr.cli import app
from tests.test_cli_process_speakers_helpers import _strip_ansi, runner


class TestProcessSpeakersHelp:
    """Tests for help output."""

    def test_help(self) -> None:
        """Shows help message."""
        result = runner.invoke(app, ["process", "speakers", "--help"])
        assert result.exit_code == 0
        assert "speakers" in result.output.lower()


class TestProcessSpeakersMissingData:
    """Tests for missing data handling."""

    def test_missing_transcripts_dir(self) -> None:
        """Fails gracefully when transcripts directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                [
                    "process",
                    "speakers",
                    "--transcripts-dir",
                    str(Path(tmpdir) / "missing"),
                    "--output-dir",
                    str(Path(tmpdir) / "output"),
                ],
            )
            output = _strip_ansi(result.output)
            assert "not found" in output.lower() or "no transcripts" in output.lower()
