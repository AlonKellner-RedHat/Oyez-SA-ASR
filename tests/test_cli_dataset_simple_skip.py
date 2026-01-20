# Edited by Claude
"""Tests for skip-if-exists caching in dataset simple."""

import json
import tempfile
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from typer.testing import CliRunner

from oyez_sa_asr.audio_utils import save_audio
from oyez_sa_asr.cli import app
from oyez_sa_asr.cli_dataset_state import make_state, save_state

runner = CliRunner()


def _create_test_flac(path: Path, duration_sec: float = 10.0) -> None:
    """Create a test FLAC audio file."""
    sample_rate = 16000
    t = np.linspace(0, duration_sec, int(duration_sec * sample_rate), dtype=np.float32)
    samples = np.sin(2 * np.pi * 440 * t) * 0.5
    samples = samples[np.newaxis, :]
    path.parent.mkdir(parents=True, exist_ok=True)
    save_audio(samples, sample_rate, path, format="flac", bits_per_sample=16)


def _create_flex_dataset(flex_dir: Path) -> None:
    """Create a minimal flex dataset for testing."""
    (flex_dir / "data").mkdir(parents=True)
    audio_subdir = flex_dir / "audio" / "2024" / "22-123"
    audio_subdir.mkdir(parents=True)

    _create_test_flac(audio_subdir / "20240101a.flac", duration_sec=5.0)

    recordings = [
        {
            "term": "2024",
            "docket": "22-123",
            "recording_id": "20240101a",
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
            "end_sec": 2.0,
            "duration_sec": 2.0,
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
    (flex_dir / "index.json").write_text(json.dumps({"terms": ["2024"]}))


class TestSkipExisting:
    """Tests for skip-if-exists caching."""

    def test_skips_if_matching_state(self) -> None:
        """Skips processing if output state matches current settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

            _create_flex_dataset(flex_dir)

            # Create matching state with shard_size_mb=100 (default)
            state = make_state(
                "oyez dataset simple", ["2024"], completed=True, shard_size_mb=100
            )
            save_state(output_dir, state)
            (output_dir / "marker.txt").write_text("original")

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

            assert result.exit_code == 0
            assert "Skipping" in result.output
            # Marker file should still exist (not cleaned)
            assert (output_dir / "marker.txt").exists()

    def test_cleans_when_shard_size_differs(self) -> None:
        """Cleans and regenerates when shard_size_mb differs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

            _create_flex_dataset(flex_dir)

            # Create state with different shard_size_mb
            state = make_state(
                "oyez dataset simple", ["2024"], completed=True, shard_size_mb=250
            )
            save_state(output_dir, state)
            (output_dir / "marker.txt").write_text("should be removed")

            result = runner.invoke(
                app,
                [
                    "dataset",
                    "simple",
                    "--flex-dir",
                    str(flex_dir),
                    "--output-dir",
                    str(output_dir),
                    "--shard-size",
                    "500",  # Different from saved state
                ],
            )

            assert result.exit_code == 0
            assert "Cleaning" in result.output
            # Marker file should be removed
            assert not (output_dir / "marker.txt").exists()

    def test_cleans_when_flex_terms_differ(self) -> None:
        """Cleans and regenerates when flex dataset terms differ."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

            _create_flex_dataset(flex_dir)

            # Create state with different terms (simulating flex was regenerated)
            state = make_state(
                "oyez dataset simple", ["2023"], completed=True, shard_size_mb=500
            )
            save_state(output_dir, state)
            (output_dir / "marker.txt").write_text("should be removed")

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

            assert result.exit_code == 0
            assert "Cleaning" in result.output
            assert not (output_dir / "marker.txt").exists()

    def test_regenerates_if_incomplete(self) -> None:
        """Regenerates if existing state has completed=false."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

            _create_flex_dataset(flex_dir)

            # Create incomplete state
            state = make_state(
                "oyez dataset simple", ["2024"], completed=False, shard_size_mb=500
            )
            save_state(output_dir, state)

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

            assert result.exit_code == 0
            assert "Skipping" not in result.output

            # Verify completed now
            with (output_dir / "index.json").open() as f:
                index = json.load(f)
            assert index["completed"] is True

    def test_force_regenerates_matching_settings(self) -> None:
        """--force flag forces regeneration even if state matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flex_dir = Path(tmpdir) / "flex"
            output_dir = Path(tmpdir) / "simple"

            _create_flex_dataset(flex_dir)

            # Create matching state
            state = make_state(
                "oyez dataset simple", ["2024"], completed=True, shard_size_mb=500
            )
            save_state(output_dir, state)

            result = runner.invoke(
                app,
                [
                    "dataset",
                    "simple",
                    "--flex-dir",
                    str(flex_dir),
                    "--output-dir",
                    str(output_dir),
                    "--force",
                ],
            )

            assert result.exit_code == 0
            assert "Skipping" not in result.output
            # Should have regenerated
            assert (output_dir / "data" / "utterances").exists()
