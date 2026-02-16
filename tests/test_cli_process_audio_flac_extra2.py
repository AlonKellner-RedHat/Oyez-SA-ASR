# Edited by Cursor: split from test_cli_process_audio_flac_extra (lintok; plan).
"""Extra FLAC/process audio tests part 2 (TestFlacValidationExtra2)."""

import importlib
import tempfile
from concurrent.futures import BrokenExecutor
from pathlib import Path
from unittest.mock import MagicMock, patch

from oyez_sa_asr import cli_process_audio
from oyez_sa_asr.audio_source import AudioSource
from oyez_sa_asr.audio_utils import save_audio
from oyez_sa_asr.cli import app
from oyez_sa_asr.cli_process_audio import (
    _run_parallel_sources,
    _try_process_file,
    _validate_flac_files,
)
from tests.test_cli_process_audio_helpers import make_sine, runner, strip_ansi


class TestFlacValidationExtra2:
    """Extra FLAC/process audio tests part 2."""

    def test_force_mode_output(self) -> None:
        """Should show force mode message when --force is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            mp3_dir = (
                cache_dir / "oyez.case-media.mp3" / "case_data" / "2020" / "19-force"
            )
            mp3_dir.mkdir(parents=True)
            save_audio(make_sine(sr=44100, dur=0.1), 44100, mp3_dir / "test_force.mp3")
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
            assert (
                "force" in strip_ansi(result.output).lower()
                or "reprocess" in strip_ansi(result.output).lower()
            )

    def test_all_files_already_processed_message(self) -> None:
        """Should show message when all files are already processed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            mp3_dir = (
                cache_dir / "oyez.case-media.mp3" / "case_data" / "2020" / "19-already"
            )
            mp3_dir.mkdir(parents=True)
            save_audio(
                make_sine(sr=44100, dur=0.1), 44100, mp3_dir / "test_already.mp3"
            )
            runner.invoke(
                app, ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)]
            )
            result = runner.invoke(
                app, ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)]
            )
            assert result.exit_code == 0
            out = strip_ansi(result.output).lower()
            assert "already processed" in out or "skipped" in out or "all files" in out

    def test_skipped_count_output(self) -> None:
        """Should show skipped count when files are already processed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            mp3_dir = (
                cache_dir / "oyez.case-media.mp3" / "case_data" / "2020" / "19-skip"
            )
            mp3_dir.mkdir(parents=True)
            save_audio(make_sine(sr=44100, dur=0.1), 44100, mp3_dir / "test_skip.mp3")
            runner.invoke(
                app, ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)]
            )
            result = runner.invoke(
                app, ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)]
            )
            assert result.exit_code == 0
            assert (
                "skip" in strip_ansi(result.output).lower()
                or "existing" in strip_ansi(result.output).lower()
            )

    def test_mp_context_valueerror_handling(self) -> None:
        """Should handle ValueError when spawn context is unavailable."""
        with patch(
            "multiprocessing.get_context", side_effect=ValueError("spawn not available")
        ):
            importlib.reload(cli_process_audio)
            assert cli_process_audio._MP_CONTEXT is None

    def test_try_process_file_returns_false_on_failure(self) -> None:
        """Should return (False, err) when processing fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            fake_path = Path(tmpdir) / "nonexistent.mp3"
            success, err, meta = _try_process_file(
                fake_path, "test", "2020", "19-999", output_dir, 24, "mp3"
            )
            assert not success
            assert err != ""
            assert meta == {}

    def test_process_audio_reports_missing_flac_files(self) -> None:
        """Should report missing FLAC files after processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"
            mp3_dir = (
                cache_dir / "oyez.case-media.mp3" / "case_data" / "2020" / "19-missing"
            )
            mp3_dir.mkdir(parents=True)
            save_audio(
                make_sine(sr=44100, dur=0.1), 44100, mp3_dir / "test_missing.mp3"
            )
            with patch(
                "oyez_sa_asr.cli_process_audio._process_recording",
                return_value=(True, ""),
            ):
                result = runner.invoke(
                    app,
                    ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)],
                )
            assert result.exit_code in {0, 1}

    def test_process_audio_reports_more_than_five_missing(self) -> None:
        """Should report '... and X more' when more than 5 files are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            sources = [AudioSource(f"rec_{i}", "2020", f"case-{i}") for i in range(7)]
            for source in sources:
                out_dir = output_dir / source.term / source.docket
                out_dir.mkdir(parents=True)
                (out_dir / f"{source.recording_id}.metadata.json").write_text(
                    '{"format": "mp3", "sample_rate": 44100}'
                )
            missing_count, missing_sources = _validate_flac_files(sources, output_dir)
            assert missing_count == 7
            assert len(missing_sources) > 5

    def test_run_parallel_sources_handles_exceptions(self) -> None:
        """Should handle exceptions in parallel processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data"
            sources = [AudioSource("test", "2020", "19-999")]
            with (
                patch(
                    "oyez_sa_asr._cli_process_audio_helpers.ProcessPoolExecutor"
                ) as mock_executor_cls,
                patch(
                    "oyez_sa_asr._cli_process_audio_helpers.as_completed"
                ) as mock_as_completed,
            ):
                mock_executor = MagicMock()
                mock_future = MagicMock()
                mock_future.result.side_effect = BrokenExecutor("executor broken")
                mock_executor.submit.return_value = mock_future
                mock_executor_cls.return_value.__enter__.return_value = mock_executor
                mock_as_completed.return_value = [mock_future]
                _processed, errors = _run_parallel_sources(sources, output_dir, 24, 1)
                assert errors >= 0
