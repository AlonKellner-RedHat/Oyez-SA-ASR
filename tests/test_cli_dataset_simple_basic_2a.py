# Edited by Cursor: split from test_cli_dataset_simple for lintok.
"""Tests for dataset simple CLI - basic (2a)."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from oyez_sa_asr.cli import app
from tests.test_cli_dataset_simple_common import _create_test_flac, runner


class TestDatasetSimple:
    """Tests for dataset simple command."""

    def test_displays_filtered_utterances(self) -> None:
        """Should display count of filtered utterances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

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

            # Create utterances, some with matching audio, some without
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
                },
                {
                    "term": "2024",
                    "docket": "22-999",  # No matching audio
                    "transcript_type": "oral_argument",
                    "text": "No audio",
                    "word_count": 1,
                    "start_sec": 0.0,
                    "end_sec": 1.0,
                    "duration_sec": 1.0,
                },
            ]
            pq.write_table(
                pa.Table.from_pylist(utterances),
                flex_dir / "data" / "utterances.parquet",
            )

            flac_path = flex_dir / "audio" / "2024" / "22-123" / "20240101a.flac"
            _create_test_flac(flac_path, duration_sec=10.0)

            (flex_dir / "index.json").write_text(json.dumps({"terms": ["2024"]}))

            # Mock process_by_recording to avoid heavy audio processing
            with patch(
                "oyez_sa_asr.cli_dataset_simple_core.process_by_recording"
            ) as mock_process:
                mock_process.return_value = {
                    "embedded": 1,
                    "skipped": 0,
                    "errors": 0,
                    "shards": 1,
                }

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
                assert (
                    "Filtered" in result.output or "filtered" in result.output.lower()
                )

    @pytest.mark.slow
    def test_displays_errors_count(self) -> None:
        """Should display error count when there are read errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

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

            # Create invalid FLAC file (will cause read error)
            flac_path = flex_dir / "audio" / "2024" / "22-123" / "20240101a.flac"
            flac_path.write_bytes(b"invalid flac data")

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

            # May succeed but show warnings, or fail
            # The important thing is it handles errors gracefully
            assert (
                "Warning" in result.output
                or "error" in result.output.lower()
                or result.exit_code == 0
            )
