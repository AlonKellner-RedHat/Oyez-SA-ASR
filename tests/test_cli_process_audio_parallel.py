# Edited by Claude
"""Tests for parallel processing in process audio command."""

import math
import re
import tempfile
from pathlib import Path

import numpy as np
from typer.testing import CliRunner

from oyez_sa_asr.audio_utils import save_audio
from oyez_sa_asr.cli import app

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def make_sine(sr: int = 16000, dur: float = 0.5) -> np.ndarray:
    """Generate a sine wave."""
    t = np.linspace(0, dur, int(sr * dur), dtype=np.float32)
    return np.sin(2 * math.pi * 440 * t)


class TestParallelProcessing:
    """Test parallel processing features."""

    def test_parallel_processing(self) -> None:
        """Should process multiple files with workers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "data"

            for i in range(3):
                mp3_dir = (
                    cache_dir
                    / "oyez.case-media.mp3"
                    / "case_data"
                    / "2020"
                    / f"case-{i}"
                )
                mp3_dir.mkdir(parents=True)
                samples = make_sine(sr=44100, dur=0.1)
                save_audio(samples, 44100, mp3_dir / f"audio_{i}.mp3")

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
                    "2",
                ],
            )
            assert result.exit_code == 0
            output = strip_ansi(result.output)
            assert "3" in output

    def test_many_files_no_hang(self) -> None:
        """Regression test: process >50 files per worker without hanging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir, output_dir = Path(tmpdir) / "cache", Path(tmpdir) / "data"
            num_files = 60
            for i in range(num_files):
                mp3_dir = cache_dir / "oyez.case-media.mp3/case_data/2020" / f"c{i}"
                mp3_dir.mkdir(parents=True)
                save_audio(make_sine(sr=16000, dur=0.05), 16000, mp3_dir / f"a{i}.mp3")

            result = runner.invoke(
                app,
                [
                    "process",
                    "audio",
                    "-c",
                    str(cache_dir),
                    "-o",
                    str(output_dir),
                    "-w",
                    "2",
                ],
            )
            assert result.exit_code == 0
            assert str(num_files) in strip_ansi(result.output)
