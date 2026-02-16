# Edited by Cursor: split from test_cli_process (lintok; plan).
"""Tests for process cases command (TestProcessCases)."""

import json
import tempfile
from pathlib import Path

from oyez_sa_asr.cli import app
from tests.test_cli_process_helpers import runner, strip_ansi


class TestProcessCases:
    """Tests for process cases command."""

    def test_process_cases_help(self) -> None:
        """Should show help for process cases."""
        result = runner.invoke(app, ["process", "cases", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--cache-dir" in output
        assert "--output-dir" in output

    def test_process_cases_creates_files(self) -> None:
        """Should create one JSON file per case."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)

            # Create a sample case file
            case_data = {
                "ID": 12345,
                "name": "Test v. Case",
                "docket_number": "21-476",
                "term": "2022",
                "href": "https://example.com/cases/2022/21-476",
                "timeline": [],
                "decisions": [{"decision_type": "majority opinion"}],
                "oral_argument_audio": [],
                "opinion_announcement": [],
            }
            (raw_dir / "abc123.json").write_text(json.dumps(case_data))

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
            expected_file = output_dir / "2022" / "21-476.json"
            assert expected_file.exists()

    def test_process_cases_empty_cache(self) -> None:
        """Should handle empty cache gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"

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
            assert "0 cases" in result.output or "No cached cases" in result.output

    def test_process_cases_multiple_cases(self) -> None:
        """Should process multiple cases into separate files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)

            # Create two case files
            for i, (docket, term) in enumerate(
                [("21-476", "2022"), ("20-123", "2021")]
            ):
                case_data = {
                    "ID": i,
                    "name": f"Case {i}",
                    "docket_number": docket,
                    "term": term,
                    "href": f"https://example.com/cases/{term}/{docket}",
                    "timeline": [],
                    "decisions": [],
                    "oral_argument_audio": [],
                    "opinion_announcement": [],
                }
                (raw_dir / f"case{i}.json").write_text(json.dumps(case_data))

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
            assert (output_dir / "2021" / "20-123.json").exists()

    def test_process_cases_with_term_filter(self) -> None:
        """Filters to specific term."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)

            # Create cases for multiple terms
            for i, (docket, term) in enumerate(
                [("21-476", "2022"), ("20-123", "2021")]
            ):
                case_data = {
                    "ID": i,
                    "name": f"Case {i}",
                    "docket_number": docket,
                    "term": term,
                    "href": f"https://example.com/cases/{term}/{docket}",
                    "timeline": [],
                    "decisions": [],
                    "oral_argument_audio": [],
                    "opinion_announcement": [],
                }
                (raw_dir / f"case{i}.json").write_text(json.dumps(case_data))

            result = runner.invoke(
                app,
                [
                    "process",
                    "cases",
                    "--cache-dir",
                    str(cache_dir),
                    "--output-dir",
                    str(output_dir),
                    "--term",
                    "2022",
                ],
            )

            assert result.exit_code == 0
            assert (output_dir / "2022" / "21-476.json").exists()
            assert not (output_dir / "2021").exists()

    def test_process_cases_with_force(self) -> None:
        """Should reprocess existing files when --force is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)

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
            (raw_dir / "abc123.json").write_text(json.dumps(case_data))

            # Process once
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
            expected_file = output_dir / "2022" / "21-476.json"
            assert expected_file.exists()
            original_mtime = expected_file.stat().st_mtime

            # Process again with --force
            result = runner.invoke(
                app,
                [
                    "process",
                    "cases",
                    "--cache-dir",
                    str(cache_dir),
                    "--output-dir",
                    str(output_dir),
                    "--force",
                ],
            )
            assert result.exit_code == 0
            # File should be reprocessed (newer mtime)
            assert expected_file.stat().st_mtime >= original_mtime
            assert (
                "Force mode" in result.output or "reprocessing" in result.output.lower()
            )

    def test_process_cases_skips_existing(self) -> None:
        """Should skip existing files when --force is not used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)

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
            (raw_dir / "abc123.json").write_text(json.dumps(case_data))

            # Process once
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
            expected_file = output_dir / "2022" / "21-476.json"
            assert expected_file.exists()

            # Process again without --force
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
            output = strip_ansi(result.output)
            assert "Skipped (existing)" in output
