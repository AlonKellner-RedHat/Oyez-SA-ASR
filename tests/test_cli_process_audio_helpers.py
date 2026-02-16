# Edited by Cursor: split from test_cli_process_audio (lintok; plan).
"""Shared helpers for process audio subcommand tests."""

import math
import re

import numpy as np
from typer.testing import CliRunner

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def make_sine(sr: int = 16000, dur: float = 0.5) -> np.ndarray:
    """Generate a sine wave."""
    t = np.linspace(0, dur, int(sr * dur), dtype=np.float32)
    return np.sin(2 * math.pi * 440 * t)
