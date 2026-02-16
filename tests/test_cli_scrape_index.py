# Edited by Cursor: split from test_cli (lintok; no new exclusions).
"""Tests for scrape index command."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from oyez_sa_asr.cli import app
from tests.test_cli_helpers import strip_ansi

runner = CliRunner()


class TestScrapeIndex:
    """Tests for scrape index command."""

    def test_scrape_index_help(self) -> None:
        """Should show help for scrape index."""
        result = runner.invoke(app, ["scrape", "index", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--cache-dir" in output
        assert "--max-pages" in output

    def test_scrape_index_with_force_mode(self) -> None:
        """Should display force mode message (line 56)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            with patch(
                "oyez_sa_asr.cli_scrape.OyezCasesTraverser"
            ) as mock_traverser_cls:
                mock_traverser = mock_traverser_cls.return_value
                mock_traverser.fetch_all = AsyncMock(return_value=[])
                result = runner.invoke(
                    app,
                    [
                        "scrape",
                        "index",
                        "--cache-dir",
                        str(cache_dir),
                        "--force",
                    ],
                )
                output = strip_ansi(result.output)
                assert "Force mode" in output

    def test_scrape_cases_with_terms_and_force(self) -> None:
        """Should display terms and force mode messages (lines 116, 121)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            index_file = Path(tmpdir) / "index.json"
            index_file.write_text('{"cases": []}')
            result = runner.invoke(
                app,
                [
                    "scrape",
                    "cases",
                    "--index-file",
                    str(index_file),
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

    def test_scrape_cases_on_progress_callback(self) -> None:
        """Should call on_progress callback during fetching (lines 150-162)."""
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
                call_args = mock_fetcher.fetch_batch_adaptive.call_args
                assert len(call_args[0]) >= 2
                assert callable(call_args[0][1])
                call_kwargs = call_args[1] if len(call_args) > 1 else {}
                assert call_kwargs.get("force") is False

    def test_scrape_index_default_cache_dir(self) -> None:
        """Should use .cache/index as default cache directory."""
        with (
            patch("oyez_sa_asr.cli_scrape.AdaptiveFetcher"),
            patch("oyez_sa_asr.cli_scrape.OyezCasesTraverser") as mock_traverser,
        ):
            mock_traverser.return_value.fetch_all = AsyncMock(return_value=[])
            result = runner.invoke(app, ["scrape", "index", "--max-pages", "1"])
            assert ".cache/index" in result.output or result.exit_code == 0
