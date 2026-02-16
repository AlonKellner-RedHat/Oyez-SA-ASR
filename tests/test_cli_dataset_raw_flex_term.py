# Edited by Cursor: split from test_cli_dataset (lintok; no new exclusions).
"""Tests for dataset CLI: raw, flex, term filter."""

import json
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from oyez_sa_asr.cli import app

runner = CliRunner()


class TestDatasetRaw:
    """Tests for dataset raw command."""

    def test_help(self) -> None:
        result = runner.invoke(app, ["dataset", "raw", "--help"])
        assert result.exit_code == 0
        assert "oyez-sa-asr-raw" in result.output

    def test_creates_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "output"
            (cache_dir / "audio").mkdir(parents=True)
            result = runner.invoke(
                app,
                ["dataset", "raw", "-c", str(cache_dir), "-o", str(output_dir)],
            )
            assert result.exit_code == 0
            assert output_dir.exists()
            assert (output_dir / "index.json").exists()


class TestDatasetFlex:
    """Tests for dataset flex command."""

    def test_help(self) -> None:
        result = runner.invoke(app, ["dataset", "flex", "--help"])
        assert result.exit_code == 0
        assert "oyez-sa-asr-flex" in result.output

    @pytest.mark.slow
    def test_creates_parquets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            output_dir = Path(tmpdir) / "output"
            audio_dir = data_dir / "audio" / "2024" / "22-123"
            audio_dir.mkdir(parents=True)
            meta = {
                "duration": 100.0,
                "sample_rate": 16000,
                "channels": 1,
                "source_format": "mp3",
                "source_era": "digital",
            }
            (audio_dir / "20240101a_22-123.metadata.json").write_text(json.dumps(meta))
            (audio_dir / "20240101a_22-123.flac").write_bytes(b"fake flac")
            trans_dir = data_dir / "transcripts" / "2024" / "22-123"
            trans_dir.mkdir(parents=True)
            transcript = {
                "term": "2024",
                "case_docket": "22-123",
                "type": "argument",
                "turns": [
                    {
                        "index": 0,
                        "is_valid": True,
                        "start": 0.0,
                        "stop": 10.0,
                        "duration": 10.0,
                        "speaker_id": 1,
                        "speaker_name": "John Roberts",
                        "text": "We will hear argument.",
                        "word_count": 4,
                    }
                ],
            }
            (trans_dir / "argument.json").write_text(json.dumps(transcript))
            result = runner.invoke(
                app,
                ["dataset", "flex", "-d", str(data_dir), "-o", str(output_dir)],
            )
            assert result.exit_code == 0
            assert (output_dir / "data" / "recordings.parquet").exists()
            assert (output_dir / "data" / "utterances.parquet").exists()


class TestTermFilter:
    """Tests for --term filter on dataset commands."""

    def test_raw_with_term_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            output_dir = Path(tmpdir) / "output"
            for term in ["2023", "2024"]:
                audio_term = (
                    cache_dir / "audio" / "oyez.case-media.mp3" / "case_data" / term
                )
                audio_term.mkdir(parents=True)
                (audio_term / "docket").mkdir()
                (audio_term / "docket" / "test.mp3").write_bytes(b"mp3")
            result = runner.invoke(
                app,
                [
                    "dataset",
                    "raw",
                    "-c",
                    str(cache_dir),
                    "-o",
                    str(output_dir),
                    "-T",
                    "2024",
                ],
            )
            assert result.exit_code == 0
            assert (output_dir / "audio" / "2024").exists()
            assert not (output_dir / "audio" / "2023").exists()
