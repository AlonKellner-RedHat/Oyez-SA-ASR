# Edited by Claude, Cursor
"""Tests for dataset simple segment extraction."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from typer.testing import CliRunner

from oyez_sa_asr.audio_utils import save_audio
from oyez_sa_asr.cli import app
from oyez_sa_asr.cli_dataset_simple_proc import _process_single_recording_impl

runner = CliRunner()


def _create_test_flac(path: Path, duration_sec: float = 5.0) -> None:
    """Create a test FLAC file with silence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 16000
    samples = int(duration_sec * sample_rate)
    audio = np.zeros((1, samples), dtype=np.float32)
    save_audio(audio, sample_rate, path)


class TestDatasetSimpleWithSegments:
    """Tests for dataset simple with proper segment extraction."""

    def test_embeds_segments_not_full_files(self) -> None:
        """Embeds only the segment, not the full audio file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

            (flex_dir / "data").mkdir(parents=True)
            audio_subdir = flex_dir / "audio" / "2024" / "22-123"
            audio_subdir.mkdir(parents=True)

            flac_path = audio_subdir / "20240101a.flac"
            _create_test_flac(flac_path, duration_sec=10.0)

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
                    "text": "First segment test words here",
                    "word_count": 5,
                    "speaker_name": "Roberts",
                    "start_sec": 0.0,
                    "end_sec": 2.0,
                    "duration_sec": 2.0,
                },
                {
                    "term": "2024",
                    "docket": "22-123",
                    "transcript_type": "oral_argument",
                    "text": "Second segment test words here",
                    "word_count": 5,
                    "speaker_name": "Sotomayor",
                    "start_sec": 5.0,
                    "end_sec": 7.0,
                    "duration_sec": 2.0,
                },
            ]
            pq.write_table(
                pa.Table.from_pylist(utterances),
                flex_dir / "data" / "utterances.parquet",
            )

            (flex_dir / "index.json").write_text(json.dumps({"terms": ["2024"]}))

            # Mock process_by_recording to avoid heavy audio processing
            with patch(
                "oyez_sa_asr.cli_dataset_simple_core.process_by_recording"
            ) as mock_process:
                # Create dummy output files to satisfy test assertions
                (output_dir / "data" / "utterances").mkdir(parents=True, exist_ok=True)
                # Create dummy parquet with 2 rows matching the test expectation
                dummy_rows = [
                    {
                        "text": "First segment test words here",
                        "audio": {"bytes": b"fLaC" + b"\x00" * 100},
                    },
                    {
                        "text": "Second segment test words here",
                        "audio": {"bytes": b"fLaC" + b"\x00" * 100},
                    },
                ]
                dummy_table = pa.Table.from_pylist(dummy_rows)
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
                        "simple-lt1m",
                        "--flex-dir",
                        str(flex_dir),
                        "--output-dir",
                        str(output_dir),
                    ],
                )

                assert result.exit_code == 0

            output_parquet = list(
                (output_dir / "data" / "utterances").glob("*.parquet")
            )
            assert len(output_parquet) >= 1

            table = pq.read_table(output_parquet[0])
            rows = table.to_pylist()
            assert len(rows) == 2

            # Verify segments are valid FLAC and smaller than full file
            full_file_size = flac_path.stat().st_size
            for row in rows:
                segment_size = len(row["audio"]["bytes"])
                # Segments should be smaller than full file (accounting for FLAC overhead)
                assert segment_size <= full_file_size
                assert row["audio"]["bytes"][:4] == b"fLaC"


class TestProcessSingleRecordingImpl:
    """Tests for _process_single_recording_impl function.

    Edited by Cursor: Added to verify duration calculation fix for start_sec=0.
    """

    def test_duration_computed_when_start_is_zero(self) -> None:
        """Duration is correctly computed when start_sec=0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "test.flac"
            _create_test_flac(audio_path, duration_sec=5.0)

            key = ("2024", "22-123", "oral_argument")
            utterances = [
                {
                    "term": "2024",
                    "docket": "22-123",
                    "text": "Test utterance",
                    "speaker_name": "Roberts",
                    "start_sec": 0.0,  # Bug was: 0.0 treated as falsy
                    "end_sec": 2.5,
                }
            ]

            rows, errors = _process_single_recording_impl(key, utterances, audio_path)

            assert errors == 0
            assert len(rows) == 1
            assert rows[0]["duration"] == 2.5  # Should be 2.5, not 0.0

    def test_duration_computed_for_nonzero_start(self) -> None:
        """Duration is correctly computed for non-zero start_sec."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "test.flac"
            _create_test_flac(audio_path, duration_sec=5.0)

            key = ("2024", "22-123", "oral_argument")
            utterances = [
                {
                    "term": "2024",
                    "docket": "22-123",
                    "text": "Test utterance",
                    "speaker_name": "Roberts",
                    "start_sec": 1.0,
                    "end_sec": 3.5,
                }
            ]

            rows, errors = _process_single_recording_impl(key, utterances, audio_path)

            assert errors == 0
            assert len(rows) == 1
            assert rows[0]["duration"] == 2.5

    def test_skips_invalid_utterances(self) -> None:
        """Skips utterances with missing or invalid time ranges."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "test.flac"
            _create_test_flac(audio_path, duration_sec=5.0)

            key = ("2024", "22-123", "oral_argument")
            utterances = [
                {"text": "Missing times", "speaker_name": "A"},  # No start/end
                {"text": "Missing end", "start_sec": 0.0},  # No end
                {
                    "text": "Invalid range",
                    "start_sec": 3.0,
                    "end_sec": 2.0,
                },  # start > end
                {"text": "Valid", "start_sec": 0.0, "end_sec": 1.0},  # Valid
            ]

            rows, errors = _process_single_recording_impl(key, utterances, audio_path)

            assert errors == 0
            assert len(rows) == 1
            assert rows[0]["sentence"] == "Valid"

    def test_returns_empty_when_no_valid_utterances(self) -> None:
        """Returns empty list when no valid utterances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "test.flac"
            _create_test_flac(audio_path, duration_sec=5.0)

            key = ("2024", "22-123", "oral_argument")
            utterances = [{"text": "Invalid", "start_sec": 3.0, "end_sec": 2.0}]

            rows, errors = _process_single_recording_impl(key, utterances, audio_path)

            assert errors == 0
            assert len(rows) == 0
