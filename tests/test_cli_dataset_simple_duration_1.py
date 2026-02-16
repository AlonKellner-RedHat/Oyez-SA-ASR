# Edited by Cursor: split from test_cli_dataset_simple for lintok.
"""Tests for dataset simple CLI - duration (1/2)."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from oyez_sa_asr.cli import app
from tests.test_cli_dataset_simple_common import _create_test_flac, runner


class TestDurationFlavors:
    """Tests for duration-based simple dataset commands."""

    def test_lt1m_help(self) -> None:
        """simple-lt1m shows help."""
        result = runner.invoke(app, ["dataset", "simple-lt1m", "--help"])
        assert result.exit_code == 0
        assert "< 1 minute" in result.output

    def test_lt5m_help(self) -> None:
        """simple-lt5m shows help."""
        result = runner.invoke(app, ["dataset", "simple-lt5m", "--help"])
        assert result.exit_code == 0
        assert "1-5 minutes" in result.output

    def test_lt30m_help(self) -> None:
        """simple-lt30m shows help."""
        result = runner.invoke(app, ["dataset", "simple-lt30m", "--help"])
        assert result.exit_code == 0
        assert "5-30 minutes" in result.output

    def test_lt1m_default_workers(self) -> None:
        """simple-lt1m defaults to 8 workers."""
        result = runner.invoke(app, ["dataset", "simple-lt1m", "--help"])
        assert "default: 8" in result.output.lower()

    def test_lt30m_default_workers(self) -> None:
        """simple-lt30m defaults to 1 worker."""
        result = runner.invoke(app, ["dataset", "simple-lt30m", "--help"])
        assert "default: 1" in result.output.lower()

    def test_lt5m_help_shows_workers(self) -> None:
        """simple-lt5m shows workers option."""
        result = runner.invoke(app, ["dataset", "simple-lt5m", "--help"])
        assert "workers" in result.output.lower() or "-w" in result.output

    @pytest.mark.slow
    def test_lt5m_executes(self) -> None:
        """Test that dataset_simple_lt5m function executes (line 72)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple-lt5m"

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
                    "start_sec": 100.0,  # 1-5 min range
                    "end_sec": 200.0,
                    "duration_sec": 100.0,
                }
            ]
            pq.write_table(
                pa.Table.from_pylist(utterances),
                flex_dir / "data" / "utterances.parquet",
            )
            _create_test_flac(
                flex_dir / "audio" / "2024" / "22-123" / "20240101a.flac",
                duration_sec=200.0,
            )
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
                        "simple-lt5m",
                        "--flex-dir",
                        str(flex_dir),
                        "--output-dir",
                        str(output_dir),
                        "--workers",
                        "1",
                    ],
                )

                assert result.exit_code == 0

    @pytest.mark.slow
    def test_lt30m_executes(self) -> None:
        """Test that dataset_simple_lt30m function executes (line 106)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple-lt30m"

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
                    "start_sec": 500.0,  # 5-30 min range
                    "end_sec": 1000.0,
                    "duration_sec": 500.0,
                }
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
                        "simple-lt30m",
                        "--flex-dir",
                        str(flex_dir),
                        "--output-dir",
                        str(output_dir),
                    ],
                )

                assert result.exit_code == 0
