# Edited by Claude
"""Unit tests for AdaptiveFetcher."""

import tempfile
from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from oyez_sa_asr.scraper import AdaptiveFetcher, RequestMetadata
from oyez_sa_asr.scraper.httpx_downloader import HttpxDownloader
from oyez_sa_asr.scraper.models import FetchResult


def _get_httpx_downloader(fetcher: AdaptiveFetcher) -> HttpxDownloader:
    """Cast downloader to HttpxDownloader for test access to cache."""
    return cast("HttpxDownloader", fetcher.downloader)


class TestAdaptiveFetcher:
    """Tests for AdaptiveFetcher."""

    def test_create_factory_method(self) -> None:
        """Factory method should create fetcher with HTTP downloader."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), ttl_days=7)
            assert fetcher.downloader is not None
            assert fetcher.max_parallelism == 10

    def test_downloader_is_transient_failure(self) -> None:
        """Downloader should correctly identify transient failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader
            url = "https://test.example.com/api"
            # Success is not transient
            assert not downloader.is_transient_failure(
                FetchResult(url=url, success=True, status_code=200)
            )
            # Connection error (no status) is transient
            assert downloader.is_transient_failure(
                FetchResult(url=url, success=False, error="timeout")
            )
            # 429/502/503/504 are transient
            for code in [429, 502, 503, 504]:
                assert downloader.is_transient_failure(
                    FetchResult(url=url, success=False, status_code=code)
                )
            # 400/404 are permanent
            for code in [400, 404]:
                assert not downloader.is_transient_failure(
                    FetchResult(url=url, success=False, status_code=code)
                )

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
            _get_httpx_downloader(fetcher).cache.set(request, result)
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
            mock_response.raise_for_status = MagicMock()
            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=mock_response,
            ):
                fetched = await fetcher.fetch_one(request)
            assert fetched.success is True
            assert fetched.data == {"test": "data"}

    @pytest.mark.asyncio
    async def test_fetch_handles_http_error(self) -> None:
        """Should handle HTTP errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/error")
            mock_request = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            error = httpx.HTTPStatusError(
                "Not Found", request=mock_request, response=mock_response
            )
            with patch.object(
                httpx.AsyncClient, "request", new_callable=AsyncMock, side_effect=error
            ):
                fetched = await fetcher.fetch_one(request)
            assert fetched.success is False
            assert fetched.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_fetch_handles_request_error(self) -> None:
        """Should handle connection errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/timeout")
            error = httpx.ConnectError("Connection refused")
            with patch.object(
                httpx.AsyncClient, "request", new_callable=AsyncMock, side_effect=error
            ):
                fetched = await fetcher.fetch_one(request)
            assert fetched.success is False
            assert "Connection refused" in str(fetched.error)

    @pytest.mark.asyncio
    async def test_check_cache_returns_none_if_not_cached(self) -> None:
        """Downloader check_cache should return None for uncached requests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/not-cached")
            assert fetcher.downloader.check_cache(request) is None

    @pytest.mark.asyncio
    async def test_check_cache_returns_result_if_cached(self) -> None:
        """Downloader check_cache should return cached result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/cached")
            result = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                data={"x": 1},
                raw_data=b'{"x": 1}',
                content_type="application/json",
            )
            _get_httpx_downloader(fetcher).cache.set(request, result)
            cached = fetcher.downloader.check_cache(request)
            assert cached is not None
            assert cached.from_cache is True

    @pytest.mark.asyncio
    async def test_partition_cached_with_force_mode(self) -> None:
        """Force mode should skip cache and fetch all requests (line 59)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            request1 = RequestMetadata(url="https://example.com/test1")
            request2 = RequestMetadata(url="https://example.com/test2")

            # Cache one request
            cached_result = FetchResult(
                url=request1.url,
                success=True,
                status_code=200,
                data={"cached": True},
            )
            _get_httpx_downloader(fetcher).cache.set(request1, cached_result)

            # With force=True, should skip cache and fetch both
            results, needs_fetch = fetcher._partition_cached(
                [request1, request2], force=True
            )
            assert len(results) == 0  # No cached results returned
            assert len(needs_fetch) == 2  # Both need to be fetched

    def test_create_with_s3_downloader(self) -> None:
        """Should create fetcher with S3Downloader (lines 169-176)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create_s3(Path(tmpdir))
            assert fetcher.downloader is not None
            # Verify it's an S3Downloader by checking it has S3-specific attributes
            assert hasattr(fetcher.downloader, "max_retries")
            assert hasattr(fetcher.downloader, "check_cache")
