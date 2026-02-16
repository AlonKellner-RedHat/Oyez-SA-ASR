# Edited by Cursor: split from test_cli_dataset_simple for lintok.
"""Tests for dataset simple CLI - main (2/2)."""

import json
import os
import shutil
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

    def test_speakers_parquet_generation_in_main_command(self) -> None:
        """Should generate speakers.parquet when speakers dir exists in main command."""
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

                # Mock the speakers directory path by creating it in the expected location
                # The code looks for Path("data/speakers") relative to current directory
                # We'll use a workaround by patching or using the actual path
                original_cwd = os.getcwd()
                try:
                    os.chdir(tmpdir)
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
                finally:
                    os.chdir(original_cwd)

                assert result.exit_code == 0
                # Check that speakers.parquet was generated in the output directory
                speakers_pq = output_dir / "data" / "speakers.parquet"
                assert speakers_pq.exists()
                # Verify it contains speaker data
                speakers_table = pq.read_table(speakers_pq)
                assert len(speakers_table) > 0

    @pytest.mark.slow
    def test_speakers_parquet_skip_message_in_main_command(self) -> None:
        """Should show skip message when speakers dir doesn't exist in main command."""
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

            # Change to tmpdir to ensure data/speakers doesn't exist
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Ensure data/speakers doesn't exist
                speakers_dir = Path("data/speakers")
                if speakers_dir.exists():
                    shutil.rmtree(speakers_dir)

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
                # Should show note about missing speakers dir
                assert (
                    "speakers not found" in result.output.lower()
                    or "skipping" in result.output.lower()
                    or "note:" in result.output.lower()
                )
            finally:
                os.chdir(original_cwd)
