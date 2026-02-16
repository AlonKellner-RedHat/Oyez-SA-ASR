# Edited by Cursor: split from test_scrape_audio (lintok; plan).
"""Tests for scrape audio CLI command (TestScrapeAudioCommand)."""

import re
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from oyez_sa_asr.cli import app
from oyez_sa_asr.cli_scrape_audio import _is_expected_skip
from oyez_sa_asr.scraper.models import FetchResult


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


runner = CliRunner()


class TestScrapeAudioCommand:
    """Tests for scrape audio CLI command."""

    def test_help(self) -> None:
        """Show help for scrape audio command."""
        result = runner.invoke(app, ["scrape", "audio", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--transcripts-dir" in output
        assert "--cache-dir" in output
        assert "--max-parallelism" in output

    def test_empty_transcripts(self) -> None:
        """Handle empty transcripts directory gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcripts_dir = Path(tmpdir) / "transcripts"
            transcripts_dir.mkdir()
            cache_dir = Path(tmpdir) / "cache"

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
            assert "No audio URLs found" in result.output

    @patch("oyez_sa_asr.cli_scrape_audio.AdaptiveFetcher")
    @patch("oyez_sa_asr.cli_scrape_audio.extract_audio_urls")
    def test_fetches_urls(
        self, mock_extract: MagicMock, mock_fetcher_cls: MagicMock
    ) -> None:
        """Extract URLs and use AdaptiveFetcher to download them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcripts_dir = Path(tmpdir) / "transcripts"
            transcripts_dir.mkdir()
            cache_dir = Path(tmpdir) / "cache"

            # Mock URL extraction
            mock_extract.return_value = [
                "https://s3.amazonaws.com/bucket/audio1.mp3",
                "https://s3.amazonaws.com/bucket/audio2.mp3",
            ]

            # Mock fetcher
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
            mock_extract.assert_called_once_with(transcripts_dir, None)
            mock_fetcher_cls.create_s3.assert_called_once()
            mock_fetcher.fetch_batch_adaptive.assert_called_once()

    def test_is_expected_skip_checks_error_string(self) -> None:
        """Should check error string for expected skip conditions (lines 26-27)."""
        # Test NoSuchKey in error string
        result = FetchResult(
            url="https://example.com/test.mp3",
            success=False,
            error="NoSuchKey: The specified key does not exist",
        )
        assert _is_expected_skip(result) is True

        # Test AccessDenied in error string
        result = FetchResult(
            url="https://example.com/test.mp3",
            success=False,
            error="AccessDenied: Access Denied",
        )
        assert _is_expected_skip(result) is True

        # Test Unrecognized S3 URL in error string
        result = FetchResult(
            url="https://example.com/test.mp3",
            success=False,
            error="Unrecognized S3 URL",
        )
        assert _is_expected_skip(result) is True

    def test_scrape_audio_with_terms_and_force(self) -> None:
        """Should display terms and force mode messages (lines 80, 84)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            transcripts_dir = Path(tmpdir) / "transcripts"
            transcripts_dir.mkdir()
            cache_dir = Path(tmpdir) / "cache"

            with patch(
                "oyez_sa_asr.cli_scrape_audio.extract_audio_urls"
            ) as mock_extract:
                mock_extract.return_value = []
                result = runner.invoke(
                    app,
                    [
                        "scrape",
                        "audio",
                        "--transcripts-dir",
                        str(transcripts_dir),
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
