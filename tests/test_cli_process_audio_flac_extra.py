# Edited by Cursor: split from test_cli_process_audio (lintok; plan).
"""Extra FLAC/process audio tests (TestFlacValidation part 2)."""

import tempfile
from pathlib import Path

from oyez_sa_asr.audio_source import AudioSource
from oyez_sa_asr.audio_utils import save_audio
from oyez_sa_asr.cli import app
from oyez_sa_asr.cli_process_audio import (
    _count_anomalies,
    _filter_pending_sources,
    _process_recording,
    _try_process_file,
    _validate_flac_files,
)
from tests.test_cli_process_audio_helpers import make_sine, runner, strip_ansi


class TestFlacValidationExtra:
    """Extra FLAC validation and process audio tests."""

    def test_force_mode_reprocesses_existing(self) -> None:
        """Should reprocess files when --force is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            mp3_dir = (
                cache_dir / "oyez.case-media.mp3" / "case_data" / "2020" / "19-force"
            )
            mp3_dir.mkdir(parents=True)
            samples = make_sine(sr=44100, dur=0.1)
            save_audio(samples, 44100, mp3_dir / "test_force.mp3")
            result = runner.invoke(
                app, ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)]
            )
            assert result.exit_code == 0
            result = runner.invoke(
                app,
                [
                    "process",
                    "audio",
                    "-c",
                    str(cache_dir),
                    "-o",
                    str(output_dir),
                    "--force",
                ],
            )
            assert result.exit_code == 0
            output = strip_ansi(result.output)
            assert "skip" not in output.lower() or "force" in output.lower()

    def test_validation_with_exactly_five_missing(self) -> None:
        """Should handle exactly 5 missing files (boundary case)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            sources = [AudioSource(f"rec_{i}", "2020", f"case-{i}") for i in range(5)]
            for source in sources:
                out_dir = output_dir / source.term / source.docket
                out_dir.mkdir(parents=True)
                (out_dir / f"{source.recording_id}.metadata.json").write_text(
                    '{"format": "mp3", "sample_rate": 44100}'
                )
            missing_count, missing_sources = _validate_flac_files(sources, output_dir)
            assert missing_count == 5
            assert len(missing_sources) == 5

    def test_terms_filtering_in_output(self) -> None:
        """Should show terms in output when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            mp3_dir = (
                cache_dir / "oyez.case-media.mp3" / "case_data" / "2020" / "19-terms"
            )
            mp3_dir.mkdir(parents=True)
            save_audio(make_sine(sr=44100, dur=0.1), 44100, mp3_dir / "test_terms.mp3")
            result = runner.invoke(
                app,
                [
                    "process",
                    "audio",
                    "-c",
                    str(cache_dir),
                    "-o",
                    str(output_dir),
                    "--term",
                    "2020",
                ],
            )
            assert result.exit_code == 0
            assert "2020" in strip_ansi(result.output)

    def test_orphaned_metadata_cleanup(self) -> None:
        """Should clean up orphaned metadata files without FLAC."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            term_dir = output_dir / "2020" / "19-orphan"
            term_dir.mkdir(parents=True)
            meta_path = term_dir / "recording.metadata.json"
            meta_path.write_text('{"format": "mp3", "sample_rate": 44100}')
            source = AudioSource("recording", "2020", "19-orphan")
            sources = {("2020", "19-orphan", "recording"): source}
            pending, skipped = _filter_pending_sources(sources, output_dir, force=False)
            assert not meta_path.exists()
            assert len(pending) == 1
            assert skipped == 0

    def test_exception_handling_in_try_process_file(self) -> None:
        """Should handle exceptions in _try_process_file gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            fake_path = Path(tmpdir) / "nonexistent.mp3"
            success, err, meta = _try_process_file(
                fake_path, "test", "2020", "19-999", output_dir, 24, "mp3"
            )
            assert not success
            assert err != ""
            assert meta == {}

    def test_no_valid_source_file_path(self) -> None:
        """Should handle AudioSource with no valid source files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            source = AudioSource("test", "2020", "19-999")
            source.mp3_path = None
            source.ogg_path = None
            success, err = _process_recording(source, output_dir, 24)
            assert not success
            assert "No valid source file" in err

    def test_count_anomalies_with_invalid_json(self) -> None:
        """Should handle invalid JSON in metadata files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            (output_dir / "2020" / "19-invalid").mkdir(parents=True)
            (output_dir / "2020" / "19-invalid" / "recording.metadata.json").write_text(
                "invalid json content"
            )
            assert _count_anomalies(output_dir) == 0

    def test_count_anomalies_with_missing_file(self) -> None:
        """Should handle missing metadata files gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            output_dir.mkdir(parents=True)
            assert _count_anomalies(output_dir) == 0

    def test_count_anomalies_detects_anomalies(self) -> None:
        """Should count files with is_anomaly flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            (output_dir / "2020" / "19-anomaly").mkdir(parents=True)
            (output_dir / "2020" / "19-anomaly" / "recording.metadata.json").write_text(
                '{"is_anomaly": true, "format": "mp3"}'
            )
            assert _count_anomalies(output_dir) == 1

    def test_sequential_processing_path(self) -> None:
        """Should use sequential processing when workers=1 or single file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            mp3_dir = (
                cache_dir / "oyez.case-media.mp3" / "case_data" / "2020" / "19-seq"
            )
            mp3_dir.mkdir(parents=True)
            save_audio(make_sine(sr=44100, dur=0.1), 44100, mp3_dir / "test_seq.mp3")
            result = runner.invoke(
                app,
                [
                    "process",
                    "audio",
                    "-c",
                    str(cache_dir),
                    "-o",
                    str(output_dir),
                    "--workers",
                    "1",
                ],
            )
            assert result.exit_code == 0
            assert "Processed" in strip_ansi(result.output) or "Done" in strip_ansi(
                result.output
            )
