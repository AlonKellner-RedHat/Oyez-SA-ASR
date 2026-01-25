# Edited by Claude
"""Tests for dataset CLI commands."""

import json
import tempfile
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from typer.testing import CliRunner

from oyez_sa_asr.cli import app
from oyez_sa_asr.cli_dataset import (
    _collect_recordings,
    _collect_utterances,
    _copy_tree,
)
from oyez_sa_asr.cli_dataset_helpers import (
    collect_recordings,
    collect_speakers,
    collect_utterances,
)

runner = CliRunner()


class TestDatasetRaw:
    """Tests for dataset raw command."""

    def test_help(self) -> None:
        """Show help."""
        result = runner.invoke(app, ["dataset", "raw", "--help"])
        assert result.exit_code == 0
        assert "oyez-sa-asr-raw" in result.output

    def test_creates_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "output"
            (cache_dir / "audio").mkdir(parents=True)

            result = runner.invoke(
                app,
                ["dataset", "raw", "-c", str(cache_dir), "-o", str(output_dir)],
            )

            assert result.exit_code == 0
            assert output_dir.exists()
            assert (output_dir / "index.json").exists()


class TestDatasetFlex:
    """Tests for dataset flex command."""

    def test_help(self) -> None:
        """Show help."""
        result = runner.invoke(app, ["dataset", "flex", "--help"])
        assert result.exit_code == 0
        assert "oyez-sa-asr-flex" in result.output

    @pytest.mark.slow
    def test_creates_parquets(self) -> None:
        """Create recordings and utterances parquet files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            output_dir = Path(tmpdir) / "output"

            audio_dir = data_dir / "audio" / "2024" / "22-123"
            audio_dir.mkdir(parents=True)
            meta = {
                "duration": 100.0,
                "sample_rate": 16000,
                "channels": 1,
                "source_format": "mp3",
                "source_era": "digital",
            }
            (audio_dir / "20240101a_22-123.metadata.json").write_text(json.dumps(meta))
            (audio_dir / "20240101a_22-123.flac").write_bytes(b"fake flac")

            trans_dir = data_dir / "transcripts" / "2024" / "22-123"
            trans_dir.mkdir(parents=True)
            transcript = {
                "term": "2024",
                "case_docket": "22-123",
                "type": "argument",
                "turns": [
                    {
                        "index": 0,
                        "is_valid": True,
                        "start": 0.0,
                        "stop": 10.0,
                        "duration": 10.0,
                        "speaker_id": 1,
                        "speaker_name": "John Roberts",
                        "text": "We will hear argument.",
                        "word_count": 4,
                    }
                ],
            }
            (trans_dir / "argument.json").write_text(json.dumps(transcript))

            result = runner.invoke(
                app,
                ["dataset", "flex", "-d", str(data_dir), "-o", str(output_dir)],
            )

            assert result.exit_code == 0
            assert (output_dir / "data" / "recordings.parquet").exists()
            assert (output_dir / "data" / "utterances.parquet").exists()


class TestTermFilter:
    """Tests for --term filter on dataset commands."""

    def test_raw_with_term_filter(self) -> None:
        """Filter to specific term."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "output"

            for term in ["2023", "2024"]:
                audio_term = (
                    cache_dir / "audio" / "oyez.case-media.mp3" / "case_data" / term
                )
                audio_term.mkdir(parents=True)
                (audio_term / "docket").mkdir()
                (audio_term / "docket" / "test.mp3").write_bytes(b"mp3")

            result = runner.invoke(
                app,
                [
                    "dataset",
                    "raw",
                    "-c",
                    str(cache_dir),
                    "-o",
                    str(output_dir),
                    "-T",
                    "2024",
                ],
            )

            assert result.exit_code == 0
            assert (output_dir / "audio" / "2024").exists()
            assert not (output_dir / "audio" / "2023").exists()


class TestCollectFunctions:
    """Tests for helper collection functions."""

    def test_collect_recordings_empty(self) -> None:
        """Return empty list for nonexistent directory."""
        result = _collect_recordings(Path("/nonexistent"), None)
        assert result == []

    def test_collect_utterances_empty(self) -> None:
        """Return empty list for nonexistent directory."""
        result = _collect_utterances(Path("/nonexistent"), None)
        assert result == []

    def test_copy_tree_empty(self) -> None:
        """Return 0 for nonexistent source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _copy_tree(Path("/nonexistent"), Path(tmpdir) / "dst")
            assert result == 0

    def test_collect_recordings_with_data(self) -> None:
        """Collect recordings from processed audio."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_dir = Path(tmpdir)
            term_dir = audio_dir / "2024" / "22-123"
            term_dir.mkdir(parents=True)
            meta = {
                "duration": 100.0,
                "sample_rate": 16000,
                "channels": 1,
                "source_format": "mp3",
                "source_era": "digital",
            }
            (term_dir / "rec.metadata.json").write_text(json.dumps(meta))
            # Create FLAC file (required for collect_recordings to include it)
            (term_dir / "rec.flac").write_bytes(b"fLaC\x00\x00\x00")

            result = _collect_recordings(audio_dir, None)
            assert len(result) == 1
            assert result[0]["term"] == "2024"

    def test_collect_utterances_with_data(self) -> None:
        """Collect utterances from processed transcripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            trans_dir = Path(tmpdir)
            docket_dir = trans_dir / "2024" / "22-123"
            docket_dir.mkdir(parents=True)
            transcript = {
                "term": "2024",
                "case_docket": "22-123",
                "type": "argument",
                "turns": [
                    {
                        "is_valid": True,
                        "index": 0,
                        "start": 0.0,
                        "stop": 5.0,
                        "duration": 5.0,
                        "speaker_name": "Roberts",
                        "text": "Test",
                        "word_count": 1,
                    }
                ],
            }
            (docket_dir / "argument.json").write_text(json.dumps(transcript))

            result = _collect_utterances(trans_dir, None)
            assert len(result) == 1
            assert result[0]["speaker_name"] == "Roberts"

    def test_collect_recordings_with_term_filter(self) -> None:
        """Collect recordings filtered by term."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_dir = Path(tmpdir)
            for term in ["2023", "2024"]:
                term_dir = audio_dir / term / "22-123"
                term_dir.mkdir(parents=True)
                meta = {
                    "duration": 100.0,
                    "sample_rate": 16000,
                    "channels": 1,
                    "source_format": "mp3",
                    "source_era": "digital",
                }
                (term_dir / "rec.metadata.json").write_text(json.dumps(meta))
                (term_dir / "rec.flac").write_bytes(b"fLaC\x00\x00\x00")

            result = collect_recordings(audio_dir, ["2024"])
            assert len(result) == 1
            assert result[0]["term"] == "2024"

    def test_collect_recordings_skips_non_directories(self) -> None:
        """Should skip non-directory entries when iterating."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_dir = Path(tmpdir)
            term_dir = audio_dir / "2024"
            term_dir.mkdir()
            # Create a file (not a directory) in term_dir
            (term_dir / "file.txt").write_text("not a directory")

            result = collect_recordings(audio_dir, None)
            # Should handle gracefully, not crash
            assert isinstance(result, list)

    def test_collect_utterances_with_speakers_dir(self) -> None:
        """Collect utterances with speakers directory provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            trans_dir = Path(tmpdir)
            docket_dir = trans_dir / "2024" / "22-123"
            docket_dir.mkdir(parents=True)
            transcript = {
                "term": "2024",
                "case_docket": "22-123",
                "type": "argument",
                "turns": [
                    {
                        "is_valid": True,
                        "index": 0,
                        "start": 0.0,
                        "stop": 5.0,
                        "duration": 5.0,
                        "speaker_id": 123,
                        "speaker_name": "Roberts",
                        "text": "Test",
                        "word_count": 1,
                    }
                ],
            }
            (docket_dir / "argument.json").write_text(json.dumps(transcript))

            speakers_dir = Path(tmpdir) / "speakers"
            justices_dir = speakers_dir / "justices"
            justices_dir.mkdir(parents=True)
            speaker_data = {"id": 123, "name": "Roberts", "role": "justice"}
            (justices_dir / "123_roberts.json").write_text(json.dumps(speaker_data))

            result = collect_utterances(trans_dir, None, speakers_dir)
            assert len(result) == 1
            assert result[0]["is_justice"] is True

    def test_collect_speakers_basic(self) -> None:
        """Collect speakers from speakers directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            speakers_dir = Path(tmpdir) / "speakers"
            justices_dir = speakers_dir / "justices"
            justices_dir.mkdir(parents=True)

            speaker_data = {
                "id": 123,
                "name": "Test Justice",
                "role": "justice",
                "totals": {
                    "recordings": 10,
                    "cases": 5,
                    "turns": 100,
                    "duration_seconds": 3600.0,
                    "word_count": 5000,
                },
                "first_appearance": "2020",
                "last_appearance": "2024",
                "by_term": {
                    "2020": {
                        "recordings": 5,
                        "turns": 50,
                        "duration_seconds": 1800.0,
                        "word_count": 2500,
                    }
                },
                "cases": ["2020/20-123"],
                "recordings": [],
            }
            (justices_dir / "123_test_justice.json").write_text(
                json.dumps(speaker_data)
            )

            result = collect_speakers(speakers_dir, None)
            assert len(result) == 1
            assert result[0]["speaker_id"] == 123
            assert result[0]["name"] == "Test Justice"

    def test_collect_speakers_with_term_filter(self) -> None:
        """Collect speakers filtered by term."""
        with tempfile.TemporaryDirectory() as tmpdir:
            speakers_dir = Path(tmpdir) / "speakers"
            justices_dir = speakers_dir / "justices"
            justices_dir.mkdir(parents=True)

            speaker_data = {
                "id": 123,
                "name": "Test Justice",
                "role": "justice",
                "totals": {
                    "recordings": 10,
                    "cases": 5,
                    "turns": 100,
                    "duration_seconds": 3600.0,
                    "word_count": 5000,
                },
                "first_appearance": "2020",
                "last_appearance": "2024",
                "by_term": {
                    "2020": {
                        "recordings": 5,
                        "turns": 50,
                        "duration_seconds": 1800.0,
                        "word_count": 2500,
                    },
                    "2024": {
                        "recordings": 5,
                        "turns": 50,
                        "duration_seconds": 1800.0,
                        "word_count": 2500,
                    },
                },
                "cases": ["2020/20-123", "2024/24-456"],
                "recordings": [],
            }
            (justices_dir / "123_test_justice.json").write_text(
                json.dumps(speaker_data)
            )

            result = collect_speakers(speakers_dir, ["2024"])
            assert len(result) == 1
            # Should only include 2024 data in by_term
            assert "2024" in result[0]["by_term"]
            assert "2020" not in result[0]["by_term"]

    def test_flex_generates_speakers_parquet(self) -> None:
        """Should generate speakers.parquet when speakers directory exists (lines 207-214)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            output_dir = Path(tmpdir) / "output"

            # Setup audio and transcripts
            audio_dir = data_dir / "audio" / "2024" / "22-123"
            audio_dir.mkdir(parents=True)
            meta = {
                "duration": 100.0,
                "sample_rate": 16000,
                "channels": 1,
                "source_format": "mp3",
                "source_era": "digital",
            }
            (audio_dir / "20240101a_22-123.metadata.json").write_text(json.dumps(meta))
            (audio_dir / "20240101a_22-123.flac").write_bytes(b"fake flac")

            trans_dir = data_dir / "transcripts" / "2024" / "22-123"
            trans_dir.mkdir(parents=True)
            transcript = {
                "term": "2024",
                "case_docket": "22-123",
                "type": "argument",
                "turns": [],
            }
            (trans_dir / "argument.json").write_text(json.dumps(transcript))

            # Create speakers directory
            speakers_dir = data_dir / "speakers"
            justices_dir = speakers_dir / "justices"
            justices_dir.mkdir(parents=True)
            speaker_data = {
                "id": 123,
                "name": "Test Justice",
                "role": "justice",
                "totals": {
                    "recordings": 10,
                    "cases": 5,
                    "turns": 100,
                    "duration_seconds": 3600.0,
                    "word_count": 5000,
                },
                "first_appearance": "2024",
                "last_appearance": "2024",
                "by_term": {
                    "2024": {
                        "recordings": 5,
                        "turns": 50,
                        "duration_seconds": 1800.0,
                        "word_count": 2500,
                    }
                },
                "cases": ["2024/22-123"],
                "recordings": [],
            }
            (justices_dir / "123_test_justice.json").write_text(
                json.dumps(speaker_data)
            )

            result = runner.invoke(
                app,
                ["dataset", "flex", "-d", str(data_dir), "-o", str(output_dir)],
            )

            assert result.exit_code == 0
            # Check that speakers.parquet was generated
            speakers_pq = output_dir / "data" / "speakers.parquet"
            assert speakers_pq.exists()
            # Verify it contains speaker data
            speakers_table = pq.read_table(speakers_pq)
            assert len(speakers_table) > 0
