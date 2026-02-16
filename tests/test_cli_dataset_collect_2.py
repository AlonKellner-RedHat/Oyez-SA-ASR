# Edited by Cursor: split from test_cli_dataset (lintok; no new exclusions).
"""Tests for dataset collect: speakers, flex speakers parquet."""

import json
import tempfile
from pathlib import Path

import pyarrow.parquet as pq
from typer.testing import CliRunner

from oyez_sa_asr.cli import app
from oyez_sa_asr.cli_dataset_helpers import collect_speakers, collect_utterances

runner = CliRunner()


class TestCollectFunctions2:
    """Collect utterances with speakers, collect_speakers, flex speakers.parquet."""

    def test_collect_utterances_with_speakers_dir(self) -> None:
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
                        "speaker_id": 123,
                        "speaker_name": "Roberts",
                        "text": "Test",
                        "word_count": 1,
                    }
                ],
            }
            (docket_dir / "argument.json").write_text(json.dumps(transcript))
            speakers_dir = Path(tmpdir) / "speakers"
            justices_dir = speakers_dir / "justices"
            justices_dir.mkdir(parents=True)
            speaker_data = {"id": 123, "name": "Roberts", "role": "justice"}
            (justices_dir / "123_roberts.json").write_text(json.dumps(speaker_data))
            result = collect_utterances(trans_dir, None, speakers_dir)
            assert len(result) == 1
            assert result[0]["is_justice"] is True

    def test_collect_speakers_basic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            speakers_dir = Path(tmpdir) / "speakers"
            justices_dir = speakers_dir / "justices"
            justices_dir.mkdir(parents=True)
            speaker_data = {
                "id": 123,
                "name": "Test Justice",
                "role": "justice",
                "totals": {
                    "recordings": 10,
                    "cases": 5,
                    "turns": 100,
                    "duration_seconds": 3600.0,
                    "word_count": 5000,
                },
                "first_appearance": "2020",
                "last_appearance": "2024",
                "by_term": {
                    "2020": {
                        "recordings": 5,
                        "turns": 50,
                        "duration_seconds": 1800.0,
                        "word_count": 2500,
                    }
                },
                "cases": ["2020/20-123"],
                "recordings": [],
            }
            (justices_dir / "123_test_justice.json").write_text(
                json.dumps(speaker_data)
            )
            result = collect_speakers(speakers_dir, None)
            assert len(result) == 1
            assert result[0]["speaker_id"] == 123
            assert result[0]["name"] == "Test Justice"

    def test_collect_speakers_with_term_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            speakers_dir = Path(tmpdir) / "speakers"
            justices_dir = speakers_dir / "justices"
            justices_dir.mkdir(parents=True)
            speaker_data = {
                "id": 123,
                "name": "Test Justice",
                "role": "justice",
                "totals": {
                    "recordings": 10,
                    "cases": 5,
                    "turns": 100,
                    "duration_seconds": 3600.0,
                    "word_count": 5000,
                },
                "first_appearance": "2020",
                "last_appearance": "2024",
                "by_term": {
                    "2020": {
                        "recordings": 5,
                        "turns": 50,
                        "duration_seconds": 1800.0,
                        "word_count": 2500,
                    },
                    "2024": {
                        "recordings": 5,
                        "turns": 50,
                        "duration_seconds": 1800.0,
                        "word_count": 2500,
                    },
                },
                "cases": ["2020/20-123", "2024/24-456"],
                "recordings": [],
            }
            (justices_dir / "123_test_justice.json").write_text(
                json.dumps(speaker_data)
            )
            result = collect_speakers(speakers_dir, ["2024"])
            assert len(result) == 1
            assert "2024" in result[0]["by_term"]
            assert "2020" not in result[0]["by_term"]

    def test_flex_generates_speakers_parquet(self) -> None:
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
            (trans_dir / "argument.json").write_text(
                json.dumps(
                    {
                        "term": "2024",
                        "case_docket": "22-123",
                        "type": "argument",
                        "turns": [],
                    }
                )
            )
            speakers_dir = data_dir / "speakers"
            justices_dir = speakers_dir / "justices"
            justices_dir.mkdir(parents=True)
            speaker_data = {
                "id": 123,
                "name": "Test Justice",
                "role": "justice",
                "totals": {
                    "recordings": 10,
                    "cases": 5,
                    "turns": 100,
                    "duration_seconds": 3600.0,
                    "word_count": 5000,
                },
                "first_appearance": "2024",
                "last_appearance": "2024",
                "by_term": {
                    "2024": {
                        "recordings": 5,
                        "turns": 50,
                        "duration_seconds": 1800.0,
                        "word_count": 2500,
                    }
                },
                "cases": ["2024/22-123"],
                "recordings": [],
            }
            (justices_dir / "123_test_justice.json").write_text(
                json.dumps(speaker_data)
            )
            result = runner.invoke(
                app,
                ["dataset", "flex", "-d", str(data_dir), "-o", str(output_dir)],
            )
            assert result.exit_code == 0
            speakers_pq = output_dir / "data" / "speakers.parquet"
            assert speakers_pq.exists()
            speakers_table = pq.read_table(speakers_pq)
            assert len(speakers_table) > 0
