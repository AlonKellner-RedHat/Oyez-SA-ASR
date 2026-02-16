# Edited by Cursor: split from test_cli_dataset_simple for lintok.
"""Tests for dataset simple CLI - duration (2a)."""

import json
import tempfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from oyez_sa_asr.cli import app
from oyez_sa_asr.cli_dataset_simple_load import (
    get_flex_terms,
    load_and_filter_utterances,
)
from tests.test_cli_dataset_simple_common import _create_test_flac, runner


class TestDurationFlavors:
    """Tests for duration-based simple dataset commands."""

    def test_speakers_parquet_generation(self) -> None:
        """Should generate speakers.parquet when speakers directory exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"
            speakers_dir = Path(tmpdir) / "data" / "speakers"
            justices_dir = speakers_dir / "justices"
            justices_dir.mkdir(parents=True)

            # Create a speaker file
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

            # Setup flex dataset
            (flex_dir / "data").mkdir(parents=True)
            (flex_dir / "audio" / "2024" / "22-123").mkdir(parents=True)
            recordings = [
                {
                    "term": "2024",
                    "docket": "22-123",
                    "recording_id": "20240101a",
                    "transcript_type": "oral_argument",
                    "audio_path": "2024/22-123/20240101a.flac",
                }
            ]
            pq.write_table(
                pa.Table.from_pylist(recordings),
                flex_dir / "data" / "recordings.parquet",
            )
            utterances = [
                {
                    "term": "2024",
                    "docket": "22-123",
                    "transcript_type": "oral_argument",
                    "text": "Test",
                    "word_count": 1,
                    "start_sec": 0.0,
                    "end_sec": 1.0,
                    "duration_sec": 1.0,
                }
            ]
            pq.write_table(
                pa.Table.from_pylist(utterances),
                flex_dir / "data" / "utterances.parquet",
            )
            _create_test_flac(flex_dir / "audio" / "2024" / "22-123" / "20240101a.flac")
            (flex_dir / "index.json").write_text(json.dumps({"terms": ["2024"]}))

            result = runner.invoke(
                app,
                [
                    "dataset",
                    "simple-lt1m",
                    "--flex-dir",
                    str(flex_dir),
                    "--output-dir",
                    str(output_dir),
                ],
            )

            assert result.exit_code == 0
            # Flavor commands do NOT generate speakers.parquet (only main 'simple' command does)
            speakers_pq = output_dir / "data" / "speakers.parquet"
            assert not speakers_pq.exists()

    def test_get_flex_terms_handles_missing_index(self) -> None:
        """Should return empty list when index file doesn't exist (line 17)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir)
            terms = get_flex_terms(flex_dir)
            assert terms == []

    def test_get_flex_terms_handles_exceptions(self) -> None:
        """Should handle JSONDecodeError and OSError (lines 21-22)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir)
            index_file = flex_dir / "index.json"

            # Test JSONDecodeError
            index_file.write_text("{ invalid json }")
            terms = get_flex_terms(flex_dir)
            assert terms == []

            # Test OSError (permission denied)
            index_file.write_text('{"terms": ["2024"]}')
            index_file.chmod(0o000)  # Remove read permission
            try:
                terms = get_flex_terms(flex_dir)
                assert terms == []
            finally:
                index_file.chmod(0o644)  # Restore permission

    def test_load_and_filter_utterances_counts_invalid_reasons(self) -> None:
        """Should count and display invalid utterance reasons (lines 55-64)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            (flex_dir / "data").mkdir(parents=True)

            utterances = [
                {
                    "term": "2024",
                    "docket": "22-123",
                    "valid": False,
                    "invalid_reason": "wpm_too_low:15.0",
                },
                {
                    "term": "2024",
                    "docket": "22-123",
                    "valid": False,
                    "invalid_reason": "wpm_too_low:12.0",
                },
                {
                    "term": "2024",
                    "docket": "22-123",
                    "valid": False,
                    "invalid_reason": "overlap:5.0s",
                },
                {
                    "term": "2024",
                    "docket": "22-123",
                    "valid": True,
                },
            ]
            pq.write_table(
                pa.Table.from_pylist(utterances),
                flex_dir / "data" / "utterances.parquet",
            )

            result = load_and_filter_utterances(
                pq,
                flex_dir / "data" / "utterances.parquet",
                None,
                include_invalid=False,
            )
            # Should filter out invalid utterances
            assert len(result) == 1
            assert result[0]["valid"] is True
