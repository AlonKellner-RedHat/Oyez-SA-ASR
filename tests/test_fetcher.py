# Edited by Claude
"""Unit tests for AdaptiveFetcher."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from oyez_sa_asr.scraper import AdaptiveFetcher, RequestMetadata
from oyez_sa_asr.scraper.models import FetchResult  # Used by cache.set


class TestAdaptiveFetcher:
    """Tests for AdaptiveFetcher."""

    def test_create_factory_method(self) -> None:
        """Factory method should create fetcher with cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), ttl_days=7)
            assert fetcher.cache is not None
            assert fetcher.parallelism == 1
            assert fetcher.max_parallelism == 10

    def test_increase_parallelism(self) -> None:
        """Should increase parallelism up to max."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(
                Path(tmpdir), initial_parallelism=1, max_parallelism=3
            )
            assert fetcher.parallelism == 1
            fetcher._increase_parallelism()
            assert fetcher.parallelism == 2
            fetcher._increase_parallelism()
            assert fetcher.parallelism == 3
            fetcher._increase_parallelism()
            assert fetcher.parallelism == 3

    def test_increase_parallelism_capped_by_batch_size(self) -> None:
        """Should not increase parallelism beyond batch size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(
                Path(tmpdir), initial_parallelism=1, max_parallelism=10
            )
            fetcher._increase_parallelism(batch_size=2)
            assert fetcher.parallelism == 2
            fetcher._increase_parallelism(batch_size=2)
            assert fetcher.parallelism == 2
            fetcher._increase_parallelism(batch_size=5)
            assert fetcher.parallelism == 3

    def test_decrease_parallelism_and_freeze(self) -> None:
        """Should halve parallelism and freeze increases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(
                Path(tmpdir), initial_parallelism=4, max_parallelism=10
            )
            fetcher._decrease_parallelism()
            assert fetcher.parallelism == 2
            assert fetcher._frozen is True
            fetcher._increase_parallelism()
            assert fetcher.parallelism == 2

    def test_decrease_parallelism_minimum_one(self) -> None:
        """Parallelism should not go below 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), initial_parallelism=1)
            fetcher._decrease_parallelism()
            assert fetcher.parallelism == 1

    @pytest.mark.asyncio
    async def test_fetch_batch_empty(self) -> None:
        """Empty batch should return empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            results = await fetcher.fetch_batch([])
            assert results == []

    @pytest.mark.asyncio
    async def test_fetch_one_from_cache(self) -> None:
        """Should return cached result without network request."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/cached")
            result = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                data={"cached": True},
                raw_data=b'{"cached": true}',
                content_type="application/json",
            )
            fetcher.cache.set(request, result)
            fetched = await fetcher.fetch_one(request)
            assert fetched.success is True
            assert fetched.from_cache is True

    @pytest.mark.asyncio
    async def test_fetch_one_network_success(self) -> None:
        """Should fetch from network and cache result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            request = RequestMetadata(url="https://httpbin.org/json")
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b'{"test": "data"}'
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"test": "data"}
            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=mock_response,
            ):
                fetched = await fetcher.fetch_one(request)
            assert fetched.success is True
            assert fetched.data == {"test": "data"}
            assert fetched.raw_data == b'{"test": "data"}'

    @pytest.mark.asyncio
    async def test_fetch_batch_adjusts_parallelism(self) -> None:
        """Successful batch should increase parallelism up to batch size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(
                Path(tmpdir), initial_parallelism=1, max_parallelism=5
            )
            requests = [
                RequestMetadata(url=f"https://example.com/test{i}") for i in range(3)
            ]
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"[]"
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = []
            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=mock_response,
            ):
                await fetcher.fetch_batch(requests)
            assert fetcher.parallelism == 2

    @pytest.mark.asyncio
    async def test_fetch_handles_http_error(self) -> None:
        """Should handle HTTP errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), initial_parallelism=4)
            request = RequestMetadata(url="https://example.com/error")
            mock_request = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            error = httpx.HTTPStatusError(
                "Server Error", request=mock_request, response=mock_response
            )
            with patch.object(
                httpx.AsyncClient, "request", new_callable=AsyncMock, side_effect=error
            ):
                fetched = await fetcher.fetch_one(request)
            assert fetched.success is False
            assert fetcher._frozen is True

    @pytest.mark.asyncio
    async def test_fetch_handles_request_error(self) -> None:
        """Should handle connection errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), initial_parallelism=2)
            request = RequestMetadata(url="https://example.com/timeout")
            error = httpx.ConnectError("Connection refused")
            with patch.object(
                httpx.AsyncClient, "request", new_callable=AsyncMock, side_effect=error
            ):
                fetched = await fetcher.fetch_one(request)
            assert fetched.success is False
            assert "Connection refused" in str(fetched.error)
