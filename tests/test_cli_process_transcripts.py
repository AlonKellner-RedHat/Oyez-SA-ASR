# Edited by Cursor: split from test_cli_process (lintok; plan).
"""Tests for process transcripts command (TestProcessTranscripts)."""

import tempfile
from pathlib import Path

from oyez_sa_asr.cli import app
from tests.test_cli_process_helpers import runner, strip_ansi


class TestProcessTranscripts:
    """Tests for process transcripts command."""

    def test_process_transcripts_help(self) -> None:
        """Shows help for process transcripts."""
        result = runner.invoke(app, ["process", "transcripts", "--help"])
        assert result.exit_code == 0
        assert "--cache-dir" in strip_ansi(result.output)
        assert "--term" in strip_ansi(result.output)

    def test_process_transcripts_empty_cache(self) -> None:
        """Handles empty cache gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "transcripts"
            result = runner.invoke(
                app,
                [
                    "process",
                    "transcripts",
                    "--cache-dir",
                    str(cache_dir),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0
            assert "No cached transcripts" in result.output
