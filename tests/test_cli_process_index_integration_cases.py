# Edited by Cursor: split from test_cli_process_index_integration (lintok; plan).
"""Integration tests for process cases (TestProcessIndexIntegrationCases)."""

import json
import tempfile
from pathlib import Path

from oyez_sa_asr.cli import app
from tests.test_cli_process_helpers import runner


class TestProcessIndexIntegrationCases:
    """Integration tests for process cases (from TestProcessIndex)."""

    def test_process_cases_with_list_data(self) -> None:
        """Should skip files that are lists (not case objects)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)
            (raw_dir / "list_file.json").write_text(json.dumps([{"id": 1}]))
            case_data = {
                "ID": 12345,
                "name": "Test v. Case",
                "docket_number": "21-476",
                "term": "2022",
                "href": "https://example.com/cases/2022/21-476",
                "timeline": [],
                "decisions": [],
                "oral_argument_audio": [],
                "opinion_announcement": [],
            }
            (raw_dir / "valid_case.json").write_text(json.dumps(case_data))
            result = runner.invoke(
                app,
                [
                    "process",
                    "cases",
                    "--cache-dir",
                    str(cache_dir),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0
            assert (output_dir / "2022" / "21-476.json").exists()

    def test_process_cases_with_errors(self) -> None:
        """Should handle JSON decode errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)
            (raw_dir / "invalid.json").write_text("not valid json")
            case_data = {
                "ID": 12345,
                "name": "Test v. Case",
                "docket_number": "21-476",
                "term": "2022",
                "href": "https://example.com/cases/2022/21-476",
                "timeline": [],
                "decisions": [],
                "oral_argument_audio": [],
                "opinion_announcement": [],
            }
            (raw_dir / "valid.json").write_text(json.dumps(case_data))
            result = runner.invoke(
                app,
                [
                    "process",
                    "cases",
                    "--cache-dir",
                    str(cache_dir),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0
            assert (output_dir / "2022" / "21-476.json").exists()
            assert "Warnings" in result.output or "errors" in result.output.lower()

    def test_process_cases_empty_raw_files(self) -> None:
        """Should handle case when raw_files list is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)
            result = runner.invoke(
                app,
                [
                    "process",
                    "cases",
                    "--cache-dir",
                    str(cache_dir),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0
            assert "No cached cases" in result.output
