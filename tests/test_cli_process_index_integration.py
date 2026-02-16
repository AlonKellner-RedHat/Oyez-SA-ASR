# Edited by Cursor: split from test_cli_process_index (lintok; plan).
"""Integration tests for process transcripts (TestProcessIndexIntegration)."""

import json
import tempfile
from pathlib import Path

from oyez_sa_asr.cli import app
from tests.test_cli_process_helpers import runner, strip_ansi


class TestProcessIndexIntegration:
    """Integration tests for process transcripts."""

    def test_process_transcripts_with_list_data(self) -> None:
        """Should skip transcript files that are lists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)
            (raw_dir / "list_file.json").write_text(json.dumps([{"id": 1}]))
            transcript_data = {
                "id": 25123,
                "title": "Oral Argument",
                "media_file": [],
                "transcript": {"duration": 100.0, "sections": [{"turns": []}]},
            }
            (raw_dir / "valid.json").write_text(json.dumps(transcript_data))
            cases_dir = Path(tmpdir) / "cases" / "2022"
            cases_dir.mkdir(parents=True)
            (cases_dir / "21-476.json").write_text(
                json.dumps(
                    {
                        "docket_number": "21-476",
                        "term": "2022",
                        "oral_arguments": [{"id": 25123}],
                        "opinion_announcements": [],
                    }
                )
            )
            output_dir = Path(tmpdir) / "output"
            result = runner.invoke(
                app,
                [
                    "process",
                    "transcripts",
                    "--cache-dir",
                    str(cache_dir),
                    "--cases-dir",
                    str(cases_dir.parent),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0

    def test_process_transcripts_with_missing_id(self) -> None:
        """Should skip transcripts without id field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)
            transcript_data = {
                "title": "Oral Argument",
                "media_file": [],
                "transcript": {"duration": 100.0, "sections": [{"turns": []}]},
            }
            (raw_dir / "no_id.json").write_text(json.dumps(transcript_data))
            cases_dir = Path(tmpdir) / "cases"
            output_dir = Path(tmpdir) / "output"
            result = runner.invoke(
                app,
                [
                    "process",
                    "transcripts",
                    "--cache-dir",
                    str(cache_dir),
                    "--cases-dir",
                    str(cases_dir),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0

    def test_process_transcripts_with_errors(self) -> None:
        """Should handle JSON decode errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)
            (raw_dir / "invalid.json").write_text("not valid json")
            transcript_data = {
                "id": 25123,
                "title": "Oral Argument",
                "media_file": [],
                "transcript": {"duration": 100.0, "sections": [{"turns": []}]},
            }
            (raw_dir / "valid.json").write_text(json.dumps(transcript_data))
            cases_dir = Path(tmpdir) / "cases" / "2022"
            cases_dir.mkdir(parents=True)
            (cases_dir / "21-476.json").write_text(
                json.dumps(
                    {
                        "docket_number": "21-476",
                        "term": "2022",
                        "oral_arguments": [{"id": 25123}],
                        "opinion_announcements": [],
                    }
                )
            )
            output_dir = Path(tmpdir) / "output"
            result = runner.invoke(
                app,
                [
                    "process",
                    "transcripts",
                    "--cache-dir",
                    str(cache_dir),
                    "--cases-dir",
                    str(cases_dir.parent),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0
            assert "Warnings" in result.output or "errors" in result.output.lower()

    def test_process_transcripts_empty_raw_files(self) -> None:
        """Should handle case when raw_files list is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)
            cases_dir = Path(tmpdir) / "cases"
            output_dir = Path(tmpdir) / "output"
            result = runner.invoke(
                app,
                [
                    "process",
                    "transcripts",
                    "--cache-dir",
                    str(cache_dir),
                    "--cases-dir",
                    str(cases_dir),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0
            assert "No cached transcripts" in result.output

    def test_process_transcripts_with_terms_display(self) -> None:
        """Should display terms when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)
            cases_dir = Path(tmpdir) / "cases"
            output_dir = Path(tmpdir) / "output"
            result = runner.invoke(
                app,
                [
                    "process",
                    "transcripts",
                    "--cache-dir",
                    str(cache_dir),
                    "--cases-dir",
                    str(cases_dir),
                    "--output-dir",
                    str(output_dir),
                    "--term",
                    "2022",
                ],
            )
            assert result.exit_code == 0
            assert "2022" in result.output

    def test_process_transcripts_skipped_no_case_display(self) -> None:
        """Should display skipped count when transcripts have no case mapping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            raw_dir = cache_dir / "api.oyez.org" / "raw"
            raw_dir.mkdir(parents=True)
            transcript_data = {
                "id": 99999,
                "title": "Oral Argument",
                "media_file": [],
                "transcript": {"duration": 100.0, "sections": [{"turns": []}]},
            }
            (raw_dir / "no_case.json").write_text(json.dumps(transcript_data))
            cases_dir = Path(tmpdir) / "cases"
            output_dir = Path(tmpdir) / "output"
            result = runner.invoke(
                app,
                [
                    "process",
                    "transcripts",
                    "--cache-dir",
                    str(cache_dir),
                    "--cases-dir",
                    str(cases_dir),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0
            assert "Skipped (no case mapping)" in strip_ansi(result.output)
