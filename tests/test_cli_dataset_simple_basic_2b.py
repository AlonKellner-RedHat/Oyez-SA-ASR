# Edited by Cursor: split from test_cli_dataset_simple for lintok.
"""Tests for dataset simple CLI - basic (2b)."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from click.exceptions import Exit as ClickExit

from oyez_sa_asr.cli import app
from oyez_sa_asr.cli_dataset_simple_core import run_simple_dataset
from tests.test_cli_dataset_simple_common import _create_test_flac, runner


class TestDatasetSimple:
    """Tests for dataset simple command."""

    @pytest.mark.slow
    def test_handles_processing_exception(self) -> None:
        """Should handle processing exceptions gracefully."""
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

            # Create a file that will cause processing to fail
            flac_path = flex_dir / "audio" / "2024" / "22-123" / "20240101a.flac"
            flac_path.write_bytes(b"invalid" * 1000)  # Invalid FLAC

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
                    "--workers",
                    "1",
                ],
            )

            assert (
                result.exit_code == 1
                or "Error" in result.output
                or "error" in result.output.lower()
            )

    def test_run_simple_dataset_handles_processing_exception(self) -> None:
        """Should handle exceptions in process_by_recording (lines 136-143)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

            (flex_dir / "data").mkdir(parents=True)
            (flex_dir / "audio" / "2024" / "22-123").mkdir(parents=True)
            (flex_dir / "index.json").write_text(json.dumps({"terms": ["2024"]}))

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

            with patch(
                "oyez_sa_asr.cli_dataset_simple_core.process_by_recording",
                side_effect=RuntimeError("Processing failed"),
            ):
                with pytest.raises((SystemExit, ClickExit)) as exc_info:
                    run_simple_dataset(
                        flex_dir,
                        output_dir,
                        None,
                        100,
                        1,
                        False,
                        False,
                        0.0,
                        60.0,
                        "test",
                    )
                if isinstance(exc_info.value, SystemExit):
                    assert exc_info.value.code == 1
                elif isinstance(exc_info.value, ClickExit):
                    assert exc_info.value.exit_code == 1
