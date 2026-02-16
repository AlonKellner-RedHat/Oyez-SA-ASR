# Edited by Cursor: split from test_cli_dataset_simple for lintok.
"""Tests for dataset simple CLI - main (1/2)."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from oyez_sa_asr.cli import app
from tests.test_cli_dataset_simple_common import _create_test_flac, runner


class TestDatasetSimpleMainCommand:
    """Tests for the main 'dataset simple' command that runs all splits sequentially."""

    def test_max_workers_validation_error(self) -> None:
        """Should raise error when max_workers < 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

            (flex_dir / "data").mkdir(parents=True)
            (flex_dir / "index.json").write_text(json.dumps({"terms": ["2024"]}))

            result = runner.invoke(
                app,
                [
                    "dataset",
                    "simple",
                    "--flex-dir",
                    str(flex_dir),
                    "--output-dir",
                    str(output_dir),
                    "--max-workers",
                    "0",
                ],
            )

            assert result.exit_code != 0
            assert "must be at least 1" in result.output.lower()

    @pytest.mark.slow
    def test_sequential_execution_runs_all_splits(self) -> None:
        """Should run all three splits (lt1m, lt5m, lt30m) sequentially."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

            # Setup flex dataset with utterances in different duration ranges
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

            # Create utterances in different duration ranges
            utterances = [
                {
                    "term": "2024",
                    "docket": "22-123",
                    "transcript_type": "oral_argument",
                    "text": "Short",
                    "word_count": 1,
                    "start_sec": 0.0,
                    "end_sec": 30.0,  # < 1 min
                    "duration_sec": 30.0,
                },
                {
                    "term": "2024",
                    "docket": "22-123",
                    "transcript_type": "oral_argument",
                    "text": "Medium",
                    "word_count": 1,
                    "start_sec": 100.0,
                    "end_sec": 200.0,  # 1-5 min
                    "duration_sec": 100.0,
                },
                {
                    "term": "2024",
                    "docket": "22-123",
                    "transcript_type": "oral_argument",
                    "text": "Long",
                    "word_count": 1,
                    "start_sec": 500.0,
                    "end_sec": 1000.0,  # 5-30 min
                    "duration_sec": 500.0,
                },
            ]
            pq.write_table(
                pa.Table.from_pylist(utterances),
                flex_dir / "data" / "utterances.parquet",
            )

            _create_test_flac(
                flex_dir / "audio" / "2024" / "22-123" / "20240101a.flac",
                duration_sec=1000.0,
            )
            (flex_dir / "index.json").write_text(json.dumps({"terms": ["2024"]}))

            # Mock process_by_recording to avoid heavy audio processing
            with patch(
                "oyez_sa_asr.cli_dataset_simple_core.process_by_recording"
            ) as mock_process:
                # Return mock stats indicating successful processing
                mock_process.return_value = {
                    "embedded": 3,
                    "skipped": 0,
                    "errors": 0,
                    "shards": 1,
                }

                result = runner.invoke(
                    app,
                    [
                        "dataset",
                        "simple",
                        "--flex-dir",
                        str(flex_dir),
                        "--output-dir",
                        str(output_dir),
                        "--max-workers",
                        "1",
                    ],
                )

                assert result.exit_code == 0
                # Verify all three splits were created
                assert (output_dir / "lt1m").exists()
            assert (output_dir / "lt5m").exists()
            assert (output_dir / "lt30m").exists()
            # Verify output mentions all splits
            assert "lt1m" in result.output.lower()
            assert "lt5m" in result.output.lower()
            assert "lt30m" in result.output.lower()
