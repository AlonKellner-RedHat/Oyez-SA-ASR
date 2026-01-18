# Edited by Claude
"""Tests for era-aware format selection in process audio."""

import json
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


class TestEraAwareFormatSelection:
    """Test era-aware format selection (OGG pre-2006, MP3 post-2005)."""

    def test_pre2006_prefers_ogg(self) -> None:
        """Pre-2006 terms should prefer OGG."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir, output_dir = Path(tmpdir) / "cache", Path(tmpdir) / "data"
            for fmt in ("mp3", "ogg"):
                d = cache_dir / f"oyez.case-media.{fmt}/case_data/2004/04-123"
                d.mkdir(parents=True)
                suffix = ".delivery" if fmt == "mp3" else ""
                save_audio(make_sine(), 16000, d / f"test{suffix}.{fmt}")

            result = runner.invoke(
                app, ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)]
            )
            assert result.exit_code == 0
            with (output_dir / "2004/04-123/test.metadata.json").open() as f:
                meta = json.load(f)
            assert meta["source_format"] == "ogg"
            assert meta["source_era"] == "analog"

    def test_post2005_prefers_mp3(self) -> None:
        """Post-2005 terms should prefer MP3."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir, output_dir = Path(tmpdir) / "cache", Path(tmpdir) / "data"
            for fmt in ("mp3", "ogg"):
                d = cache_dir / f"oyez.case-media.{fmt}/case_data/2010/10-456"
                d.mkdir(parents=True)
                suffix = ".delivery" if fmt == "mp3" else ""
                save_audio(make_sine(), 16000, d / f"audio{suffix}.{fmt}")

            result = runner.invoke(
                app, ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)]
            )
            assert result.exit_code == 0
            with (output_dir / "2010/10-456/audio.metadata.json").open() as f:
                meta = json.load(f)
            assert meta["source_format"] == "mp3"
            assert meta["source_era"] == "digital"

    def test_fallback_when_preferred_missing(self) -> None:
        """Should use fallback format when preferred is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir, output_dir = Path(tmpdir) / "cache", Path(tmpdir) / "data"
            mp3_dir = cache_dir / "oyez.case-media.mp3/case_data/2000/00-789"
            mp3_dir.mkdir(parents=True)
            save_audio(make_sine(), 16000, mp3_dir / "fallback.delivery.mp3")

            result = runner.invoke(
                app, ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)]
            )
            assert result.exit_code == 0
            with (output_dir / "2000/00-789/fallback.metadata.json").open() as f:
                meta = json.load(f)
            assert meta["source_format"] == "mp3"

    def test_output_uses_common_recording_id(self) -> None:
        """Output filename should use common ID (without .delivery)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir, output_dir = Path(tmpdir) / "cache", Path(tmpdir) / "data"
            mp3_dir = cache_dir / "oyez.case-media.mp3/case_data/2015/15-111"
            mp3_dir.mkdir(parents=True)
            save_audio(make_sine(), 16000, mp3_dir / "recording.delivery.mp3")

            result = runner.invoke(
                app, ["process", "audio", "-c", str(cache_dir), "-o", str(output_dir)]
            )
            assert result.exit_code == 0
            assert (output_dir / "2015/15-111/recording.flac").exists()
