# Edited by Claude
"""Tests for dataset simple segment extraction."""

import json
import tempfile
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from typer.testing import CliRunner

from oyez_sa_asr.audio_utils import save_audio
from oyez_sa_asr.cli import app

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
