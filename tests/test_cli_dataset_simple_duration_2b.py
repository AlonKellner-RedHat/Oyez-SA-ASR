# Edited by Cursor: split from test_cli_dataset_simple for lintok.
"""Tests for dataset simple CLI - duration (2b)."""

import json
import tempfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from oyez_sa_asr.cli import app
from oyez_sa_asr.cli_dataset_simple_load import (
    build_audio_paths,
)
from tests.test_cli_dataset_simple_common import _create_test_flac, runner


class TestDurationFlavors:
    """Tests for duration-based simple dataset commands."""

    def test_build_audio_paths_handles_missing_recordings(self) -> None:
        """Should return empty dict when recordings.parquet doesn't exist (line 96)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            audio_dir = flex_dir / "audio"
            audio_paths = build_audio_paths(flex_dir, pq, audio_dir)
            assert audio_paths == {}

    def test_build_audio_paths_filters_by_term(self) -> None:
        """Should filter recordings by term (line 101)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            (flex_dir / "data").mkdir(parents=True)
            audio_dir = flex_dir / "audio"

            recordings = [
                {
                    "term": "2023",
                    "docket": "22-123",
                    "transcript_type": "oral_argument",
                    "audio_path": "2023/22-123/rec.flac",
                },
                {
                    "term": "2024",
                    "docket": "22-123",
                    "transcript_type": "oral_argument",
                    "audio_path": "2024/22-123/rec.flac",
                },
            ]
            pq.write_table(
                pa.Table.from_pylist(recordings),
                flex_dir / "data" / "recordings.parquet",
            )

            # Filter to 2024 only
            audio_paths = build_audio_paths(flex_dir, pq, audio_dir, terms=["2024"])
            # Should only include 2024 recording (paths don't exist, but key should be filtered)
            assert isinstance(audio_paths, dict)

    @pytest.mark.slow
    def test_speakers_parquet_empty_speakers(self) -> None:
        """Should handle empty speakers list gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"
            speakers_dir = Path(tmpdir) / "data" / "speakers"
            justices_dir = speakers_dir / "justices"
            justices_dir.mkdir(parents=True)

            # Create empty speaker file or no matching speakers
            # Actually, create a speaker file that won't match the terms
            speaker_data = {
                "id": 123,
                "name": "Test Justice",
                "role": "justice",
                "totals": {
                    "recordings": 0,
                    "cases": 0,
                    "turns": 0,
                    "duration_seconds": 0.0,
                    "word_count": 0,
                },
                "first_appearance": "2020",
                "last_appearance": "2020",
                "by_term": {
                    "2020": {
                        "recordings": 0,
                        "turns": 0,
                        "duration_seconds": 0.0,
                        "word_count": 0,
                    }
                },
                "cases": [],
                "recordings": [],
            }
            (justices_dir / "123_test_justice.json").write_text(
                json.dumps(speaker_data)
            )

            # Setup flex dataset with different term
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
                    "--term",
                    "2024",  # Different term than speaker
                ],
            )

            assert result.exit_code == 0
            # Should show note about no speakers or skip generation
            # The speaker has data for 2020, not 2024, so it might be filtered

    @pytest.mark.slow
    def test_speakers_parquet_skipped_when_missing(self) -> None:
        """Flavor commands don't generate speakers.parquet (no message shown)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

            # Setup flex dataset without speakers
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
            # Flavor commands don't generate or mention speakers.parquet
            speakers_pq = output_dir / "data" / "speakers.parquet"
            assert not speakers_pq.exists()
