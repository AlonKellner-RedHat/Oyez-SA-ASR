# Edited by Cursor: split from test_cli_dataset_simple_proc (lintok; plan).
"""Tests for _handle_future_new, process_single_recording, spawn context fallback."""

import importlib
from concurrent.futures import BrokenExecutor
from pathlib import Path
from unittest.mock import MagicMock, patch

import oyez_sa_asr.cli_dataset_simple_proc
from oyez_sa_asr.cli_dataset_simple_proc import (
    _handle_future_new,
    process_single_recording,
)


class TestHandleFutureNew:
    """Tests for _handle_future_new function."""

    def test_returns_result_on_success(self) -> None:
        """Should return future result on success."""
        future = MagicMock()
        future.result.return_value = (5, 2)  # (embedded, errors)
        futures = {future: None}

        embedded, errors = _handle_future_new(future, futures)

        assert embedded == 5
        assert errors == 2

    def test_handles_broken_executor(self) -> None:
        """Should handle BrokenExecutor exception."""
        future = MagicMock()
        future.result.side_effect = BrokenExecutor("executor broken")
        item = (("2024", "22-123", "oral_argument"), [{"text": "test"}] * 3, None)
        futures = {future: item}

        embedded, errors = _handle_future_new(future, futures)

        assert embedded == 0
        assert errors == 3

    def test_handles_generic_exception(self) -> None:
        """Should handle generic exceptions."""
        future = MagicMock()
        future.result.side_effect = ValueError("some error")
        item = (("2024", "22-123", "oral_argument"), [{"text": "test"}] * 2, None)
        futures = {future: item}

        embedded, errors = _handle_future_new(future, futures)

        assert embedded == 0
        assert errors == 2


class TestProcessSingleRecording:
    """Tests for process_single_recording function (worker entry point)."""

    def test_handles_exceptions_gracefully(self, tmp_path: Path) -> None:
        """Should catch all exceptions and return error count."""
        key = ("2024", "22-123", "oral_argument")
        utterances = [{"text": "test"}] * 3
        audio_path = tmp_path / "test.flac"
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        target_bytes = 1000

        args = (key, utterances, audio_path, data_dir, target_bytes)

        with patch(
            "oyez_sa_asr.cli_dataset_simple_proc._process_single_recording_impl",
            side_effect=Exception("worker crash"),
        ):
            embedded, errors = process_single_recording(args)

            assert embedded == 0
            assert errors == len(utterances)


class TestSpawnContextFallback:
    """Tests for spawn context fallback behavior."""

    def test_falls_back_when_spawn_unavailable(self) -> None:
        """Should fall back to default context when spawn is unavailable."""
        with patch(
            "multiprocessing.get_context", side_effect=ValueError("spawn unavailable")
        ):
            importlib.reload(oyez_sa_asr.cli_dataset_simple_proc)
            proc_module = oyez_sa_asr.cli_dataset_simple_proc

            assert hasattr(proc_module, "_MP_CONTEXT")
