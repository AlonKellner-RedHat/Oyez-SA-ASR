# Edited by Cursor: split from test_cli_process (lintok; plan).
"""Tests for process index command (TestProcessIndex)."""

import json
import tempfile
from pathlib import Path

from oyez_sa_asr.cli import app
from tests.test_cli_process_helpers import runner, strip_ansi


class TestProcessIndex:
    """Tests for process index command."""

    def test_process_index_help(self) -> None:
        """Shows help for process index."""
        result = runner.invoke(app, ["process", "index", "--help"])
        assert result.exit_code == 0
        assert "--cache-dir" in strip_ansi(result.output)

    def test_process_index_empty_cache(self) -> None:
        """Handles empty cache gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output = Path(tmpdir) / "index.json"
            result = runner.invoke(
                app,
                [
                    "process",
                    "index",
                    "--cache-dir",
                    str(cache_dir),
                    "--output",
                    str(output),
                ],
            )
            assert result.exit_code == 0
            assert "No cached cases" in result.output

    def test_process_index_with_force(self) -> None:
        """Should regenerate index when --force is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output = Path(tmpdir) / "index.json"
            output.write_text('{"total_cases": 0, "cases": []}')
            result = runner.invoke(
                app,
                [
                    "process",
                    "index",
                    "--cache-dir",
                    str(cache_dir),
                    "--output",
                    str(output),
                    "--force",
                ],
            )
            assert result.exit_code == 0
            assert (
                "Force mode" in result.output or "regenerating" in result.output.lower()
            )

    def test_process_index_with_valid_cache(self) -> None:
        """Should process index when cache has valid data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output = Path(tmpdir) / "index.json"
            (cache_dir / "api.oyez.org" / "raw").mkdir(parents=True)
            (cache_dir / "api.oyez.org" / "raw" / "page_0.json").write_text(
                json.dumps([{"ID": 1, "name": "Test"}])
            )
            result = runner.invoke(
                app,
                [
                    "process",
                    "index",
                    "--cache-dir",
                    str(cache_dir),
                    "--output",
                    str(output),
                ],
            )
            assert result.exit_code == 0
            assert output.exists()
            assert "Done" in result.output

    def test_process_index_default_paths(self) -> None:
        """Should use stage-based default paths."""
        result = runner.invoke(app, ["process", "index", "--help"])
        assert result.exit_code == 0
        assert "--output" in strip_ansi(result.output)
