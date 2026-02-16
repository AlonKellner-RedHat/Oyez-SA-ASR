# Edited by Cursor: split from test_cli_process_audio (lintok; plan).
"""Tests for process audio command execution (TestProcessAudioExecution)."""

import json
import tempfile
from pathlib import Path

from oyez_sa_asr.audio_utils import save_audio
from oyez_sa_asr.cli import app
from tests.test_cli_process_audio_helpers import make_sine, runner, strip_ansi


class TestProcessAudioExecution:
    """Test process audio command execution."""

    def test_empty_cache(self) -> None:
        """Should handle empty cache gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            result = runner.invoke(
                app,
                ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)],
            )
            assert result.exit_code == 0
            output = strip_ansi(result.output)
            assert "0" in output or "No" in output

    def test_processes_mp3_to_flac(self) -> None:
        """Should convert MP3 to FLAC and save metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            mp3_dir = (
                cache_dir / "oyez.case-media.mp3" / "case_data" / "2020" / "19-123"
            )
            mp3_dir.mkdir(parents=True)
            samples = make_sine(sr=44100, dur=0.3)
            mp3_path = mp3_dir / "19-123_20201001-argument.mp3"
            save_audio(samples, 44100, mp3_path)
            result = runner.invoke(
                app,
                ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)],
            )
            assert result.exit_code == 0
            flac_path = output_dir / "2020" / "19-123" / "19-123_20201001-argument.flac"
            meta_path = (
                output_dir
                / "2020"
                / "19-123"
                / "19-123_20201001-argument.metadata.json"
            )
            assert flac_path.exists(), f"FLAC not found: {flac_path}"
            assert meta_path.exists(), f"Metadata not found: {meta_path}"
            with meta_path.open() as f:
                meta = json.load(f)
            assert meta["format"] == "mp3"
            assert meta["sample_rate"] == 44100
            assert "source_path" in meta

    def test_processes_ogg_to_flac(self) -> None:
        """Should convert OGG to FLAC."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            ogg_dir = (
                cache_dir / "oyez.case-media.ogg" / "case_data" / "2021" / "20-456"
            )
            ogg_dir.mkdir(parents=True)
            samples = make_sine(sr=44100, dur=0.2)
            ogg_path = ogg_dir / "20-456_20210501-opinion.ogg"
            save_audio(samples, 44100, ogg_path)
            result = runner.invoke(
                app,
                ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)],
            )
            assert result.exit_code == 0
            flac_path = output_dir / "2021" / "20-456" / "20-456_20210501-opinion.flac"
            assert flac_path.exists()

    def test_skips_already_processed(self) -> None:
        """Should skip files that already have output FLAC."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            mp3_dir = (
                cache_dir / "oyez.case-media.mp3" / "case_data" / "2020" / "19-999"
            )
            mp3_dir.mkdir(parents=True)
            samples = make_sine(sr=44100, dur=0.2)
            save_audio(samples, 44100, mp3_dir / "test_skip.mp3")
            out_flac_dir = output_dir / "2020" / "19-999"
            out_flac_dir.mkdir(parents=True)
            flac_path = out_flac_dir / "test_skip.flac"
            flac_path.write_bytes(b"dummy_existing_content")
            orig_mtime = flac_path.stat().st_mtime
            result = runner.invoke(
                app,
                ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)],
            )
            assert result.exit_code == 0
            output = strip_ansi(result.output)
            assert "skip" in output.lower()
            assert flac_path.stat().st_mtime == orig_mtime

    def test_workers_option_in_help(self) -> None:
        """Should show --workers option in help."""
        result = runner.invoke(app, ["process", "audio", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--workers" in output or "-w" in output
