# Edited by Claude
"""Tests for progress reporting in fetch_batch_adaptive."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from oyez_sa_asr.scraper import AdaptiveFetcher, RequestMetadata
from oyez_sa_asr.scraper.models import FetchResult

TEST_URL = "https://test.example.com/api"


def _make_mock_response() -> MagicMock:
    """Create a mock successful HTTP response."""
    resp = MagicMock()
    resp.status_code = 200
    resp.content = b'{"ok": true}'
    resp.headers = {"content-type": "application/json"}
    resp.json.return_value = {"ok": True}
    resp.raise_for_status = MagicMock()
    return resp


class TestProgressReporting:
    """Tests for progress reporting with correct totals."""

    @pytest.mark.asyncio
    async def test_progress_reports_uncached_total(self) -> None:
        """Progress callback should report uncached count as total."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=16)

            # First, cache some requests
            to_cache = [RequestMetadata(url=f"{TEST_URL}/cached-{i}") for i in range(3)]
            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                await fetcher.fetch_batch_adaptive(to_cache)

            # Fetch mix of cached and new
            all_reqs = to_cache + [
                RequestMetadata(url=f"{TEST_URL}/new-{i}") for i in range(5)
            ]

            totals: list[int] = []

            def on_progress(c: int, t: int, r: FetchResult, p: int) -> None:
                del c, r, p
                totals.append(t)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                results = await fetcher.fetch_batch_adaptive(all_reqs, on_progress)

            assert len(results) == 8
            assert all(t == 5 for t in totals), f"Expected total=5, got {set(totals)}"

    @pytest.mark.asyncio
    async def test_progress_completed_counts_from_one(self) -> None:
        """Progress completed count should start from 1, not include cached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=16)

            # Cache 2 requests first
            cached = [RequestMetadata(url=f"{TEST_URL}/pre-{i}") for i in range(2)]
            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                await fetcher.fetch_batch_adaptive(cached)

            # Fetch cached + 3 new
            all_reqs = cached + [
                RequestMetadata(url=f"{TEST_URL}/fresh-{i}") for i in range(3)
            ]

            completed: list[int] = []

            def on_progress(c: int, t: int, r: FetchResult, p: int) -> None:
                del t, r, p
                completed.append(c)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                await fetcher.fetch_batch_adaptive(all_reqs, on_progress)

            assert completed == [1, 2, 3], f"Expected [1,2,3], got {completed}"
