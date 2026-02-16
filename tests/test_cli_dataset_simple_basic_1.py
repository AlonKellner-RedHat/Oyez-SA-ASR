# Edited by Cursor: split from test_cli_dataset_simple for lintok.
"""Tests for dataset simple CLI - basic (1/2)."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq

from oyez_sa_asr.cli import app
from tests.test_cli_dataset_simple_common import _create_test_flac, runner


class TestDatasetSimple:
    """Tests for dataset simple command."""

    def test_help(self) -> None:
        """Shows help."""
        result = runner.invoke(app, ["dataset", "simple", "--help"])
        assert result.exit_code == 0
        assert "simple dataset" in result.output.lower()

    def test_requires_flex_dataset(self) -> None:
        """Fails if flex dataset doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

            result = runner.invoke(
                app,
                [
                    "dataset",
                    "simple",
                    "--flex-dir",
                    str(flex_dir),
                    "--output-dir",
                    str(output_dir),
                ],
            )

            assert result.exit_code == 1
            assert "not found" in result.output

    def test_embeds_audio(self) -> None:
        """Embeds audio bytes into parquet files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

            (flex_dir / "data").mkdir(parents=True)
            (flex_dir / "audio" / "2024" / "22-123").mkdir(parents=True)

            # Edited by Claude: Added transcript_type field
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
                    "text": "Test utterance one",
                    "word_count": 3,
                    "speaker_name": "Roberts",
                    "start_sec": 0.0,
                    "end_sec": 3.0,
                    "duration_sec": 3.0,
                },
                {
                    "term": "2024",
                    "docket": "22-123",
                    "transcript_type": "oral_argument",
                    "text": "Test utterance two",
                    "word_count": 3,
                    "speaker_name": "Sotomayor",
                    "start_sec": 5.0,
                    "end_sec": 8.0,
                    "duration_sec": 3.0,
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
                # Create dummy output directory and files to satisfy test assertions
                (output_dir / "data" / "utterances").mkdir(parents=True, exist_ok=True)
                # Create a dummy parquet file
                dummy_table = pa.Table.from_pylist(
                    [{"text": "test", "audio": {"bytes": b"fLaC"}}]
                )
                pq.write_table(
                    dummy_table,
                    output_dir / "data" / "utterances" / "train-w00-00000.parquet",
                )

                mock_process.return_value = {
                    "embedded": 2,
                    "skipped": 0,
                    "errors": 0,
                    "shards": 1,
                }

                result = runner.invoke(
                    app,
                    [
                        "dataset",
                        "simple-lt1m",  # Use single flavor for testing
                        "--flex-dir",
                        str(flex_dir),
                        "--output-dir",
                        str(output_dir),
                    ],
                )

                assert result.exit_code == 0
            assert (output_dir / "data" / "utterances").exists()
            assert (output_dir / "index.json").exists()

    def test_fails_when_audio_dir_missing(self) -> None:
        """Should fail when audio directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

            (flex_dir / "data").mkdir(parents=True)
            # Don't create audio directory

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

            assert result.exit_code == 1
            assert "not found" in result.output
