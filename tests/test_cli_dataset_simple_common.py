# Edited by Cursor: shared fixtures/helpers for test_cli_dataset_simple (lintok split).
"""Shared runner and helpers for dataset simple CLI tests."""

from pathlib import Path

import numpy as np
from typer.testing import CliRunner

from oyez_sa_asr.audio_utils import save_audio

runner = CliRunner()


def _create_test_flac(path: Path, duration_sec: float = 10.0) -> None:
    """Create a test FLAC audio file."""
    sample_rate = 16000
    t = np.linspace(0, duration_sec, int(duration_sec * sample_rate), dtype=np.float32)
    samples = np.sin(2 * np.pi * 440 * t) * 0.5
    samples = samples[np.newaxis, :]
    path.parent.mkdir(parents=True, exist_ok=True)
    save_audio(samples, sample_rate, path, format="flac", bits_per_sample=16)
