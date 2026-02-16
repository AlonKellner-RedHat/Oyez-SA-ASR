# Edited by Cursor: split from test_cli_process_speakers (lintok; plan).
"""Tests for process speakers term filter (TestProcessSpeakersTermFilter)."""

import json
import tempfile
from pathlib import Path

from oyez_sa_asr.cli import app
from tests.test_cli_process_speakers_helpers import (
    _create_case,
    _create_transcript,
    _strip_ansi,
    runner,
)


class TestProcessSpeakersTermFilter:
    """Tests for term filtering."""

    def test_filters_by_term(self) -> None:
        """Only processes specified terms."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            transcripts_dir = data_dir / "transcripts"
            cases_dir = data_dir / "cases"
            output_dir = data_dir / "speakers"

            # Create transcripts for two terms
            for term in ["2023", "2024"]:
                t_dir = transcripts_dir / term / "docket"
                t_dir.mkdir(parents=True)
                transcript = _create_transcript(term, "docket")
                (t_dir / "oral_argument.json").write_text(json.dumps(transcript))

                c_dir = cases_dir / term
                c_dir.mkdir(parents=True)
                case = _create_case(term, "docket")
                (c_dir / "docket.json").write_text(json.dumps(case))

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
                    "--term",
                    "2024",
                ],
            )

            assert result.exit_code == 0

            # Check only 2024 data was processed (in other/ since only 1 case)
            smith_file = output_dir / "other" / "123_justice_smith.json"
            with smith_file.open() as f:
                smith_data = json.load(f)

            assert "2024" in smith_data["by_term"]
            assert "2023" not in smith_data["by_term"]

    def test_process_speakers_with_force(self) -> None:
        """Should regenerate speaker files when --force is used."""
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

            # Process once
            result = runner.invoke(
                app,
                [
                    "process",
                    "speakers",
                    "--transcripts-dir",
                    str(data_dir / "transcripts"),
                    "--cases-dir",
                    str(data_dir / "cases"),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0
            smith_file = output_dir / "other" / "123_justice_smith.json"
            assert smith_file.exists()

            # Process again with --force
            result = runner.invoke(
                app,
                [
                    "process",
                    "speakers",
                    "--transcripts-dir",
                    str(data_dir / "transcripts"),
                    "--cases-dir",
                    str(data_dir / "cases"),
                    "--output-dir",
                    str(output_dir),
                    "--force",
                ],
            )
            assert result.exit_code == 0
            assert (
                "Force mode" in result.output or "regenerating" in result.output.lower()
            )

    def test_process_speakers_skips_existing(self) -> None:
        """Should skip existing files when --force is not used."""
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

            # Process once
            result = runner.invoke(
                app,
                [
                    "process",
                    "speakers",
                    "--transcripts-dir",
                    str(data_dir / "transcripts"),
                    "--cases-dir",
                    str(data_dir / "cases"),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0

            # Process again without --force
            result = runner.invoke(
                app,
                [
                    "process",
                    "speakers",
                    "--transcripts-dir",
                    str(data_dir / "transcripts"),
                    "--cases-dir",
                    str(data_dir / "cases"),
                    "--output-dir",
                    str(output_dir),
                ],
            )
            assert result.exit_code == 0
            output = _strip_ansi(result.output)
            assert "Skipped (existing)" in output

    def test_process_speakers_no_transcripts(self) -> None:
        """Should handle case when no transcripts are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            transcripts_dir = data_dir / "transcripts"
            transcripts_dir.mkdir(parents=True)
            # Create empty term directory
            (transcripts_dir / "2024").mkdir()

            cases_dir = data_dir / "cases"
            output_dir = data_dir / "speakers"

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
            assert "No transcripts found" in result.output

    def test_process_speakers_invalid_json(self) -> None:
        """Should handle invalid JSON in transcript files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            transcripts_dir = data_dir / "transcripts" / "2024" / "23-1234"
            transcripts_dir.mkdir(parents=True)
            # Create invalid JSON file
            (transcripts_dir / "oral_argument.json").write_text("invalid json")

            cases_dir = data_dir / "cases"
            output_dir = data_dir / "speakers"

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
            # Should handle error gracefully
            assert (
                "processed" in result.output.lower() or "done" in result.output.lower()
            )
