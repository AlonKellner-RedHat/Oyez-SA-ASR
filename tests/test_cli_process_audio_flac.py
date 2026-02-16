# Edited by Cursor: split from test_cli_process_audio (lintok; plan).
"""Tests for FLAC validation (TestFlacValidation part 1)."""

import tempfile
from pathlib import Path

from oyez_sa_asr.audio_source import AudioSource
from oyez_sa_asr.cli_process_audio import _validate_flac_files


class TestFlacValidation:
    """Test FLAC validation after processing."""

    def test_reports_missing_flac_files(self) -> None:
        """Should report when FLAC files are missing after processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            sources = [
                AudioSource("rec1", "2020", "19-999"),
                AudioSource("rec2", "2020", "19-888"),
            ]
            for source in sources:
                out_dir = output_dir / source.term / source.docket
                out_dir.mkdir(parents=True)
                meta_path = out_dir / f"{source.recording_id}.metadata.json"
                meta_path.write_text('{"format": "mp3", "sample_rate": 44100}')
            missing_count, missing_sources = _validate_flac_files(sources, output_dir)
            assert missing_count == 2
            assert len(missing_sources) == 2
            assert missing_sources[0].recording_id == "rec1"
            assert missing_sources[1].recording_id == "rec2"

    def test_no_warning_when_all_flacs_exist(self) -> None:
        """Should not report warning when all FLACs are created successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            sources = [AudioSource("rec1", "2020", "19-888")]
            out_dir = output_dir / "2020" / "19-888"
            out_dir.mkdir(parents=True)
            flac_path = out_dir / "rec1.flac"
            flac_path.write_bytes(b"fLaC\x00\x00\x00")
            missing_count, missing_sources = _validate_flac_files(sources, output_dir)
            assert missing_count == 0
            assert len(missing_sources) == 0

    def test_reports_multiple_missing_files(self) -> None:
        """Should report count when multiple FLACs are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            sources = [AudioSource(f"audio_{i}", "2020", f"case-{i}") for i in range(3)]
            for source in sources:
                out_dir = output_dir / source.term / source.docket
                out_dir.mkdir(parents=True)
                meta_path = out_dir / f"{source.recording_id}.metadata.json"
                meta_path.write_text('{"format": "mp3", "sample_rate": 44100}')
            missing_count, missing_sources = _validate_flac_files(sources, output_dir)
            assert missing_count == 3
            assert len(missing_sources) == 3

    def test_integration_reports_missing_after_processing(self) -> None:
        """Integration test: should report missing FLACs in actual command output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            source = AudioSource("test_integration", "2020", "19-777")
            missing_count, _ = _validate_flac_files([source], output_dir)
            assert missing_count == 1

    def test_validation_logs_more_than_five_missing(self) -> None:
        """Should log '... and X more' when more than 5 files are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            sources = [AudioSource(f"rec_{i}", "2020", f"case-{i}") for i in range(7)]
            for source in sources:
                out_dir = output_dir / source.term / source.docket
                out_dir.mkdir(parents=True)
                meta_path = out_dir / f"{source.recording_id}.metadata.json"
                meta_path.write_text('{"format": "mp3", "sample_rate": 44100}')
            missing_count, missing_sources = _validate_flac_files(sources, output_dir)
            assert missing_count == 7
            assert len(missing_sources) == 7
            assert len(missing_sources) > 5

    def test_empty_pending_list(self) -> None:
        """Should handle empty pending list gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            missing_count, missing_sources = _validate_flac_files([], output_dir)
            assert missing_count == 0
            assert len(missing_sources) == 0
