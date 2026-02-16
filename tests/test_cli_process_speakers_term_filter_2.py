# Edited by Cursor: split from test_cli_process_speakers_term_filter (lintok; plan).
"""Tests for process speakers term filter part 2 (TestProcessSpeakersTermFilter2)."""

import json
import tempfile
from pathlib import Path
from typing import Any

from oyez_sa_asr.cli import app
from oyez_sa_asr.cli_process_speakers import _load_case_names, _process_transcript_file
from tests.test_cli_process_speakers_helpers import (
    _create_case,
    _create_transcript,
    _strip_ansi,
    runner,
)


class TestProcessSpeakersTermFilter2:
    """Tests for process speakers (load_case_names, process_transcript_file, skips)."""

    def test_load_case_names_skips_non_directories(self) -> None:
        """Should skip non-directory entries (lines 32, 42-43)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cases_dir = Path(tmpdir)
            (cases_dir / "not_a_dir.txt").write_text("test")
            term_dir = cases_dir / "2024"
            term_dir.mkdir()
            case = {"term": "2024", "docket_number": "22-123", "name": "Test Case"}
            (term_dir / "22-123.json").write_text(json.dumps(case))
            case_names = _load_case_names(cases_dir, None)
            assert "2024/22-123" in case_names
            assert case_names["2024/22-123"] == "Test Case"

    def test_load_case_names_handles_exceptions(self) -> None:
        """Should handle JSONDecodeError, KeyError (line 42-43)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cases_dir = Path(tmpdir)
            term_dir = cases_dir / "2024"
            term_dir.mkdir()
            (term_dir / "invalid.json").write_text("{ invalid json }")
            incomplete = {"id": 1}
            (term_dir / "incomplete.json").write_text(json.dumps(incomplete))
            case = {"term": "2024", "docket_number": "22-123", "name": "Test Case"}
            (term_dir / "valid.json").write_text(json.dumps(case))
            case_names = _load_case_names(cases_dir, None)
            assert "2024/22-123" in case_names

    def test_process_transcript_file_skips_invalid_turns(self) -> None:
        """Should skip invalid turns (lines 74, 78)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript_file = Path(tmpdir) / "transcript.json"
            transcript = {
                "term": "2024",
                "case_docket": "22-123",
                "turns": [
                    {"is_valid": False, "speaker_id": 123},
                    {"is_valid": True, "speaker_id": 456},
                    {"is_valid": True},
                ],
            }
            transcript_file.write_text(json.dumps(transcript))
            speakers: dict[int, Any] = {}
            case_names = {"2024/22-123": "Test Case"}
            count = _process_transcript_file(transcript_file, speakers, case_names)
            assert count == 1
            assert 456 in speakers
            assert 123 not in speakers

    def test_process_speakers_skips_non_directories(self) -> None:
        """Should skip non-directory entries (lines 173, 176)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            transcripts_dir = data_dir / "transcripts"
            cases_dir = data_dir / "cases"
            output_dir = data_dir / "speakers"
            transcripts_dir.mkdir(parents=True)
            (transcripts_dir / "not_a_dir.txt").write_text("test")
            term_dir = transcripts_dir / "2024"
            term_dir.mkdir()
            (term_dir / "not_a_dir.json").write_text("test")
            docket_dir = term_dir / "22-123"
            docket_dir.mkdir()
            transcript = _create_transcript("2024", "22-123")
            (docket_dir / "transcript.json").write_text(json.dumps(transcript))
            cases_dir.mkdir()
            case_dir = cases_dir / "2024"
            case_dir.mkdir()
            case = _create_case("2024", "22-123")
            (case_dir / "22-123.json").write_text(json.dumps(case))
            result = runner.invoke(
                app,
                [
                    "process",
                    "speakers",
                    "--transcripts-dir",
                    str(transcripts_dir),
                    "--cases-dir",
                    str(cases_dir),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0

    def test_process_speakers_skips_existing_in_other_subdir(self) -> None:
        """Should skip existing files in other subdirectory (lines 221-222)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            transcripts_dir = data_dir / "transcripts" / "2024" / "23-1234"
            transcripts_dir.mkdir(parents=True)
            transcript = _create_transcript("2024", "23-1234")
            (transcripts_dir / "oral_argument.json").write_text(json.dumps(transcript))
            cases_dir = data_dir / "cases" / "2024"
            cases_dir.mkdir(parents=True)
            case = _create_case("2024", "23-1234")
            (cases_dir / "23-1234.json").write_text(json.dumps(case))
            output_dir = data_dir / "speakers"
            other_dir = output_dir / "other"
            other_dir.mkdir(parents=True)
            existing_file = other_dir / "123_justice_smith.json"
            existing_file.write_text('{"id": 123, "name": "Justice Smith"}')
            result = runner.invoke(
                app,
                [
                    "process",
                    "speakers",
                    "--transcripts-dir",
                    str(data_dir / "transcripts"),
                    "--cases-dir",
                    str(cases_dir),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0
            output = _strip_ansi(result.output)
            assert "Skipped" in output or "skipped" in output.lower()
