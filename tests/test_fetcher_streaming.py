# Edited by Claude
"""Unit tests for AdaptiveFetcher adaptive streaming functionality."""

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


class TestIsTransientFailure:
    """Tests for _is_transient_failure method."""

    def test_success_not_transient(self) -> None:
        """Success results are not transient."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            result = FetchResult(url=TEST_URL, success=True, status_code=200)
            assert fetcher._is_transient_failure(result) is False

    def test_connection_error_transient(self) -> None:
        """Connection errors are transient."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            result = FetchResult(url=TEST_URL, success=False, error="timeout")
            assert fetcher._is_transient_failure(result) is True

    def test_transient_status_codes(self) -> None:
        """429, 502, 503, 504 are transient."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            for code in [429, 502, 503, 504]:
                result = FetchResult(url=TEST_URL, success=False, status_code=code)
                assert fetcher._is_transient_failure(result) is True

    def test_permanent_status_codes(self) -> None:
        """400, 401, 403, 404 are permanent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            for code in [400, 401, 403, 404]:
                result = FetchResult(url=TEST_URL, success=False, status_code=code)
                assert fetcher._is_transient_failure(result) is False


class TestFetchBatchAdaptive:
    """Tests for fetch_batch_adaptive method."""

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        """Empty list returns empty results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            assert await fetcher.fetch_batch_adaptive([]) == []

    @pytest.mark.asyncio
    async def test_increases_parallelism_on_success(self) -> None:
        """Increases parallelism on successful waves (rate-based)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=64)
            requests = [RequestMetadata(url=f"{TEST_URL}/{i}") for i in range(7)]
            parallelism_values: list[int] = []

            def on_progress(_c: int, _t: int, _r: FetchResult, p: int) -> None:
                parallelism_values.append(p)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                results = await fetcher.fetch_batch_adaptive(requests, on_progress)

            assert len(results) == 7
            # Parallelism should have some values recorded
            assert len(parallelism_values) == 7

    @pytest.mark.asyncio
    async def test_halves_on_failure(self) -> None:
        """Halves parallelism when transient failure occurs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=64)
            requests = [RequestMetadata(url=f"{TEST_URL}/{i}") for i in range(10)]
            call_count = 0

            async def mock_request(*_args: object, **_kwargs: object) -> MagicMock:
                nonlocal call_count
                call_count += 1
                if call_count == 4:
                    raise httpx.RequestError("timeout")
                return _make_mock_response()

            parallelism_values: list[int] = []

            def on_progress(_c: int, _t: int, _r: FetchResult, p: int) -> None:
                parallelism_values.append(p)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                side_effect=mock_request,
            ):
                results = await fetcher.fetch_batch_adaptive(requests, on_progress)

            assert len(results) == 10
            assert 2 in parallelism_values

    @pytest.mark.asyncio
    async def test_retries_transient(self) -> None:
        """Retries requests that fail with transient errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=64)
            requests = [RequestMetadata(url=f"{TEST_URL}/1")]
            attempt = 0

            async def mock_request(*_args: object, **_kwargs: object) -> MagicMock:
                nonlocal attempt
                attempt += 1
                if attempt == 1:
                    raise httpx.RequestError("timeout")
                return _make_mock_response()

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                side_effect=mock_request,
            ):
                results = await fetcher.fetch_batch_adaptive(requests)

            assert len(results) == 1
            assert results[0].success
            assert attempt == 2

    @pytest.mark.asyncio
    async def test_respects_max(self) -> None:
        """Does not exceed max_parallelism."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=4)
            requests = [RequestMetadata(url=f"{TEST_URL}/{i}") for i in range(20)]
            max_seen = 0

            def on_progress(_c: int, _t: int, _r: FetchResult, p: int) -> None:
                nonlocal max_seen
                max_seen = max(max_seen, p)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                await fetcher.fetch_batch_adaptive(requests, on_progress)

            assert max_seen <= 8

    @pytest.mark.asyncio
    async def test_no_callback(self) -> None:
        """Works without progress callback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            requests = [RequestMetadata(url=f"{TEST_URL}/1")]
            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                results = await fetcher.fetch_batch_adaptive(requests)
            assert len(results) == 1
            assert results[0].success
