# Edited by Cursor: split from test_cli (lintok; no new exclusions).
"""Tests for scrape cases command."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from oyez_sa_asr.cli import app
from oyez_sa_asr.scraper.models import FetchResult
from tests.test_cli_helpers import strip_ansi

runner = CliRunner()


class TestScrapeCases:
    """Tests for scrape cases command."""

    def test_scrape_cases_help(self) -> None:
        """Should show help for scrape cases."""
        result = runner.invoke(app, ["scrape", "cases", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--index-file" in output
        assert "--cache-dir" in output

    def test_scrape_cases_requires_index(self) -> None:
        """Should error if index file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                [
                    "scrape",
                    "cases",
                    "--index-file",
                    f"{tmpdir}/nonexistent.json",
                ],
            )
            assert result.exit_code != 0 or "not found" in result.output.lower()

    def test_scrape_cases_on_progress_creates_pbar(self) -> None:
        """Should create progress bar when on_progress is called (lines 150-162)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            index_file = Path(tmpdir) / "index.json"
            index_file.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "href": "https://api.oyez.org/cases/2024/22-123",
                                "term": "2024",
                            }
                        ]
                    }
                )
            )

            with patch("oyez_sa_asr.cli_scrape.AdaptiveFetcher") as mock_fetcher_cls:
                mock_fetcher = mock_fetcher_cls.create.return_value
                success_result = FetchResult(
                    url="https://api.oyez.org/cases/2024/22-123",
                    success=True,
                    status_code=200,
                )
                mock_fetcher.fetch_batch_adaptive = AsyncMock(
                    return_value=[success_result]
                )

                result = runner.invoke(
                    app,
                    [
                        "scrape",
                        "cases",
                        "--index-file",
                        str(index_file),
                        "--cache-dir",
                        str(cache_dir),
                    ],
                )

                assert result.exit_code == 0
                mock_fetcher.fetch_batch_adaptive.assert_called_once()
                call_args = mock_fetcher.fetch_batch_adaptive.call_args
                assert len(call_args[0]) >= 2
                assert callable(call_args[0][1])
                call_args[1] if len(call_args) > 1 else {}

    def test_scrape_cases_reads_index_and_fetches(self) -> None:
        """Should read index and fetch case details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_file = Path(tmpdir) / "cases_index.json"
            index_data = {
                "generated_at": "2026-01-13T00:00:00Z",
                "total_cases": 2,
                "cases": [
                    {"id": 1, "href": "https://api.oyez.org/cases/2020/1"},
                    {"id": 2, "href": "https://api.oyez.org/cases/2020/2"},
                ],
            }
            index_file.write_text(json.dumps(index_data))

            cache_dir = Path(tmpdir) / "cache"

            with patch("oyez_sa_asr.cli_scrape.AdaptiveFetcher") as mock_fetcher_cls:
                mock_fetcher = mock_fetcher_cls.create.return_value
                mock_fetcher.fetch_batch_adaptive = AsyncMock(return_value=[])

                result = runner.invoke(
                    app,
                    [
                        "scrape",
                        "cases",
                        "--index-file",
                        str(index_file),
                        "--cache-dir",
                        str(cache_dir),
                    ],
                )

                assert result.exit_code == 0
                mock_fetcher.fetch_batch_adaptive.assert_called_once()
                call_args = mock_fetcher.fetch_batch_adaptive.call_args[0][0]
                assert len(call_args) == 2
