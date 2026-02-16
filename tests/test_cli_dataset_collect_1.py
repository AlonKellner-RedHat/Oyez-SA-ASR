# Edited by Cursor: split from test_cli_dataset (lintok; no new exclusions).
"""Tests for dataset collect helpers (recordings, utterances, copy_tree)."""

import json
import tempfile
from pathlib import Path

from oyez_sa_asr.cli_dataset import (
    _collect_recordings,
    _collect_utterances,
    _copy_tree,
)
from oyez_sa_asr.cli_dataset_helpers import collect_recordings


class TestCollectFunctions1:
    """Collect recordings, utterances, copy_tree."""

    def test_collect_recordings_empty(self) -> None:
        result = _collect_recordings(Path("/nonexistent"), None)
        assert result == []

    def test_collect_utterances_empty(self) -> None:
        result = _collect_utterances(Path("/nonexistent"), None)
        assert result == []

    def test_copy_tree_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _copy_tree(Path("/nonexistent"), Path(tmpdir) / "dst")
            assert result == 0

    def test_collect_recordings_with_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_dir = Path(tmpdir)
            term_dir = audio_dir / "2024" / "22-123"
            term_dir.mkdir(parents=True)
            meta = {
                "duration": 100.0,
                "sample_rate": 16000,
                "channels": 1,
                "source_format": "mp3",
                "source_era": "digital",
            }
            (term_dir / "rec.metadata.json").write_text(json.dumps(meta))
            (term_dir / "rec.flac").write_bytes(b"fLaC\x00\x00\x00")
            result = _collect_recordings(audio_dir, None)
            assert len(result) == 1
            assert result[0]["term"] == "2024"

    def test_collect_utterances_with_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trans_dir = Path(tmpdir)
            docket_dir = trans_dir / "2024" / "22-123"
            docket_dir.mkdir(parents=True)
            transcript = {
                "term": "2024",
                "case_docket": "22-123",
                "type": "argument",
                "turns": [
                    {
                        "is_valid": True,
                        "index": 0,
                        "start": 0.0,
                        "stop": 5.0,
                        "duration": 5.0,
                        "speaker_name": "Roberts",
                        "text": "Test",
                        "word_count": 1,
                    }
                ],
            }
            (docket_dir / "argument.json").write_text(json.dumps(transcript))
            result = _collect_utterances(trans_dir, None)
            assert len(result) == 1
            assert result[0]["speaker_name"] == "Roberts"

    def test_collect_recordings_with_term_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_dir = Path(tmpdir)
            for term in ["2023", "2024"]:
                term_dir = audio_dir / term / "22-123"
                term_dir.mkdir(parents=True)
                meta = {
                    "duration": 100.0,
                    "sample_rate": 16000,
                    "channels": 1,
                    "source_format": "mp3",
                    "source_era": "digital",
                }
                (term_dir / "rec.metadata.json").write_text(json.dumps(meta))
                (term_dir / "rec.flac").write_bytes(b"fLaC\x00\x00\x00")
            result = collect_recordings(audio_dir, ["2024"])
            assert len(result) == 1
            assert result[0]["term"] == "2024"

    def test_collect_recordings_skips_non_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_dir = Path(tmpdir)
            term_dir = audio_dir / "2024"
            term_dir.mkdir()
            (term_dir / "file.txt").write_text("not a directory")
            result = collect_recordings(audio_dir, None)
            assert isinstance(result, list)
