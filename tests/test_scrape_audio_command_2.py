# Edited by Cursor: split from test_scrape_audio (lintok; plan).
"""Tests for scrape audio CLI command (terms, extract, progress, errors)."""

import json
import re
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from oyez_sa_asr.cli import app
from oyez_sa_asr.scraper.models import FetchResult
from oyez_sa_asr.scraper.parser_transcripts import extract_audio_urls


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


runner = CliRunner()


class TestScrapeAudioCommandScrape:
    """Scrape audio CLI: terms/force, extract edge cases, progress, errors."""

    def test_scrape_transcripts_with_terms_and_force(self) -> None:
        """Should display terms and force mode messages (lines 64, 69)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cases_dir = Path(tmpdir) / "cases"
            cases_dir.mkdir()
            cache_dir = Path(tmpdir) / "cache"

            with patch(
                "oyez_sa_asr.cli_scrape_transcripts.extract_media_urls"
            ) as mock_extract:
                mock_extract.return_value = []
                result = runner.invoke(
                    app,
                    [
                        "scrape",
                        "transcripts",
                        "--cases-dir",
                        str(cases_dir),
                        "--cache-dir",
                        str(cache_dir),
                        "--term",
                        "2024",
                        "--force",
                    ],
                )
                output = strip_ansi(result.output)
                assert "Terms: 2024" in output
                assert "Force mode" in output

    def test_extract_audio_urls_skips_non_directories(self) -> None:
        """Should skip non-directory entries (lines 201, 203, 249, 251, 255)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcripts_dir = Path(tmpdir) / "transcripts"
            transcripts_dir.mkdir()

            (transcripts_dir / "not_a_dir.txt").write_text("test")

            term_dir = transcripts_dir / "2024"
            term_dir.mkdir()
            (term_dir / "not_a_dir.json").write_text("test")

            docket_dir = term_dir / "22-123"
            docket_dir.mkdir()
            transcript = {
                "metadata": {"audio_urls": {"mp3": "https://example.com/test.mp3"}}
            }
            (docket_dir / "transcript.json").write_text(json.dumps(transcript))

            urls = extract_audio_urls(transcripts_dir)
            assert len(urls) == 1

    def test_extract_audio_urls_handles_exceptions(self) -> None:
        """Should handle JSONDecodeError, KeyError, TypeError (lines 221-222, 269-270)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcripts_dir = Path(tmpdir) / "transcripts"
            term_dir = transcripts_dir / "2024" / "22-123"
            term_dir.mkdir(parents=True)

            (term_dir / "invalid.json").write_text("{ invalid json }")

            incomplete = {"type": "oral_argument"}
            (term_dir / "incomplete.json").write_text(json.dumps(incomplete))

            transcript = {
                "metadata": {"audio_urls": {"mp3": "https://example.com/test.mp3"}}
            }
            (term_dir / "valid.json").write_text(json.dumps(transcript))

            urls = extract_audio_urls(transcripts_dir)
            assert len(urls) == 1

    def test_scrape_audio_on_progress_callback(self) -> None:
        """Should call on_progress callback during downloading (lines 119-138)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcripts_dir = Path(tmpdir) / "transcripts"
            cache_dir = Path(tmpdir) / "cache"
            term_dir = transcripts_dir / "2024" / "22-123"
            term_dir.mkdir(parents=True)
            transcript = {
                "metadata": {
                    "audio_urls": {
                        "mp3": "https://s3.amazonaws.com/bucket/audio.mp3",
                    }
                }
            }
            (term_dir / "oral_argument.json").write_text(json.dumps(transcript))

            with patch(
                "oyez_sa_asr.cli_scrape_audio.AdaptiveFetcher"
            ) as mock_fetcher_cls:
                mock_fetcher = mock_fetcher_cls.create_s3.return_value
                mock_fetcher.fetch_batch_adaptive = AsyncMock(return_value=[])

                result = runner.invoke(
                    app,
                    [
                        "scrape",
                        "audio",
                        "--transcripts-dir",
                        str(transcripts_dir),
                        "--cache-dir",
                        str(cache_dir),
                    ],
                )

                assert result.exit_code == 0
                mock_fetcher.fetch_batch_adaptive.assert_called_once()
                call_args = mock_fetcher.fetch_batch_adaptive.call_args
                assert len(call_args[0]) >= 2, (
                    "on_progress should be passed as positional arg"
                )
                assert callable(call_args[0][1]), (
                    "Second positional arg should be callable (on_progress)"
                )

    def test_scrape_audio_reports_errors(self) -> None:
        """Should report errors when errors > 0 (line 175)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcripts_dir = Path(tmpdir) / "transcripts"
            cache_dir = Path(tmpdir) / "cache"
            term_dir = transcripts_dir / "2024" / "22-123"
            term_dir.mkdir(parents=True)
            transcript = {
                "metadata": {
                    "audio_urls": {
                        "mp3": "https://s3.amazonaws.com/bucket/audio.mp3",
                    }
                }
            }
            (term_dir / "oral_argument.json").write_text(json.dumps(transcript))

            with patch(
                "oyez_sa_asr.cli_scrape_audio.AdaptiveFetcher"
            ) as mock_fetcher_cls:
                mock_fetcher = mock_fetcher_cls.create_s3.return_value
                error_result = FetchResult(
                    url="https://s3.amazonaws.com/bucket/audio.mp3",
                    success=False,
                    error="Network error",
                )
                mock_fetcher.fetch_batch_adaptive = AsyncMock(
                    return_value=[error_result]
                )

                result = runner.invoke(
                    app,
                    [
                        "scrape",
                        "audio",
                        "--transcripts-dir",
                        str(transcripts_dir),
                        "--cache-dir",
                        str(cache_dir),
                    ],
                )

                output = strip_ansi(result.output)
                assert "Error" in output or "error" in output.lower()
