# Edited by Cursor: split from test_cli_dataset_simple_proc (lintok; plan).
"""Tests for group_utterances_by_recording and _process_single_recording_impl."""

from pathlib import Path
from unittest.mock import patch

import numpy as np

from oyez_sa_asr.audio_utils import save_audio
from oyez_sa_asr.cli_dataset_simple_proc import (
    _process_single_recording_impl,
    group_utterances_by_recording,
)


def _create_test_flac(path: Path, duration_sec: float = 10.0) -> None:
    """Create a test FLAC audio file."""
    sample_rate = 16000
    t = np.linspace(0, duration_sec, int(duration_sec * sample_rate), dtype=np.float32)
    samples = np.sin(2 * np.pi * 440 * t) * 0.5
    samples = samples[np.newaxis, :]
    path.parent.mkdir(parents=True, exist_ok=True)
    save_audio(samples, sample_rate, path, format="flac", bits_per_sample=16)


class TestGroupUtterancesByRecording:
    """Tests for group_utterances_by_recording function."""

    def test_groups_correctly(self) -> None:
        """Should group utterances by recording key."""
        utterances = [
            {
                "term": "2024",
                "docket": "22-123",
                "transcript_type": "oral_argument",
                "text": "test",
            }
        ]
        result = group_utterances_by_recording(utterances)
        assert ("2024", "22-123", "oral_argument") in result


class TestProcessSingleRecordingImpl:
    """Tests for _process_single_recording_impl function."""

    def test_handles_missing_audio_file(self, tmp_path: Path) -> None:
        """Should return empty list when audio file doesn't exist."""
        key = ("2024", "22-123", "oral_argument")
        utterances = [
            {
                "term": "2024",
                "docket": "22-123",
                "transcript_type": "oral_argument",
                "text": "test",
                "start_sec": 0.0,
                "end_sec": 1.0,
            }
        ]
        audio_path = tmp_path / "nonexistent.flac"

        rows, errors = _process_single_recording_impl(key, utterances, audio_path)

        assert rows == []
        assert errors == len(utterances)

    def test_handles_invalid_time_ranges(self, tmp_path: Path) -> None:
        """Should skip utterances with invalid time ranges."""
        key = ("2024", "22-123", "oral_argument")
        audio_path = tmp_path / "test.flac"
        _create_test_flac(audio_path, duration_sec=10.0)

        utterances = [
            {
                "term": "2024",
                "docket": "22-123",
                "transcript_type": "oral_argument",
                "text": "valid",
                "start_sec": 0.0,
                "end_sec": 1.0,
            },
            {
                "term": "2024",
                "docket": "22-123",
                "transcript_type": "oral_argument",
                "text": "invalid",
                "start_sec": 2.0,
                "end_sec": 1.0,
            },
            {
                "term": "2024",
                "docket": "22-123",
                "transcript_type": "oral_argument",
                "text": "missing_start",
                "end_sec": 1.0,
            },
        ]

        rows, errors = _process_single_recording_impl(key, utterances, audio_path)

        assert len(rows) == 1
        assert "id" in rows[0] or "sentence" in rows[0]
        assert errors == 0

    def test_handles_audio_extraction_errors(self, tmp_path: Path) -> None:
        """Should handle OSError and ValueError from audio extraction."""
        key = ("2024", "22-123", "oral_argument")
        audio_path = tmp_path / "test.flac"
        _create_test_flac(audio_path, duration_sec=10.0)

        utterances = [
            {
                "term": "2024",
                "docket": "22-123",
                "transcript_type": "oral_argument",
                "text": "test",
                "start_sec": 0.0,
                "end_sec": 1.0,
            }
        ]

        with patch(
            "oyez_sa_asr._cli_dataset_simple_proc_impl.extract_segments_batch",
            side_effect=OSError("Audio file read error"),
        ):
            rows, errors = _process_single_recording_impl(key, utterances, audio_path)

            assert rows == []
            assert errors == len(utterances)
