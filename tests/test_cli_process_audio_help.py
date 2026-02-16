# Edited by Cursor: split from test_cli_process_audio (lintok; plan).
"""Tests for process audio help (TestProcessAudioHelp)."""

from oyez_sa_asr.cli import app
from tests.test_cli_process_audio_helpers import runner, strip_ansi


class TestProcessAudioHelp:
    """Test process audio help."""

    def test_help(self) -> None:
        """Should show help for process audio."""
        result = runner.invoke(app, ["process", "audio", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--cache-dir" in output
        assert "--output-dir" in output
