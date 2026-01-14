# Edited by Claude
"""Tests for worker pool scaling logic and integration."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from oyez_sa_asr.scraper import AdaptiveFetcher, RequestMetadata
from oyez_sa_asr.scraper.models import FetchResult
from oyez_sa_asr.scraper.worker_pool import WorkerPool

TEST_URL = "https://test.example.com/api"


def _make_mock_response(content: bytes = b'{"ok": true}') -> MagicMock:
    """Create a mock successful HTTP response."""
    resp = MagicMock()
    resp.status_code = 200
    resp.content = content
    resp.headers = {"content-type": "application/json"}
    resp.json.return_value = {"ok": True}
    resp.raise_for_status = MagicMock()
    return resp


class TestScaleUp:
    """Tests for scale-up trigger logic."""

    @pytest.mark.asyncio
    async def test_scale_up_when_all_workers_succeeded(self) -> None:
        """Should trigger scale-up when all workers have at least one success."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=16)

            async with httpx.AsyncClient(timeout=30.0) as client:
                pool = WorkerPool(fetcher, client, max_workers=16)
                pool.spawn_workers(2)
                initial_count = pool.worker_count

                pool.record_result(
                    0, FetchResult(url=TEST_URL, success=True, status_code=200)
                )
                pool.record_result(
                    1, FetchResult(url=TEST_URL, success=True, status_code=200)
                )

                await pool.check_scaling()
                assert pool.worker_count > initial_count
                await pool.shutdown_all()

    @pytest.mark.asyncio
    async def test_no_scale_up_before_all_succeeded(self) -> None:
        """Should not scale up until all workers have succeeded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=16)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    pool = WorkerPool(fetcher, client, max_workers=16)
                    pool.spawn_workers(2)

                    await pool.add_request(RequestMetadata(url=f"{TEST_URL}/0"))
                    await asyncio.wait_for(pool.get_result(), timeout=2.0)
                    await pool.check_scaling()

                    assert pool.worker_count == 2
                    await pool.shutdown_all()


class TestScaleDown:
    """Tests for scale-down trigger logic."""

    @pytest.mark.asyncio
    async def test_scale_down_on_failure(self) -> None:
        """Should scale down when a failure occurs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(
                Path(tmpdir), max_parallelism=16, max_retries=0
            )

            mock_response = MagicMock()
            mock_response.status_code = 404
            error = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=mock_response
            )
            call_count = 0

            async def mock_request(*_args: object, **_kwargs: object) -> MagicMock:
                nonlocal call_count
                call_count += 1
                if call_count == 2:
                    raise error
                return _make_mock_response()

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                side_effect=mock_request,
            ):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    pool = WorkerPool(fetcher, client, max_workers=16)
                    pool.spawn_workers(4)
                    initial_count = pool.worker_count

                    for i in range(4):
                        await pool.add_request(RequestMetadata(url=f"{TEST_URL}/{i}"))

                    for _ in range(4):
                        await asyncio.wait_for(pool.get_result(), timeout=2.0)
                        await pool.check_scaling()

                    assert pool.worker_count < initial_count
                    await pool.shutdown_all()

    @pytest.mark.asyncio
    async def test_scale_down_respects_minimum(self) -> None:
        """Scale down should never go below 1 worker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=16)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                side_effect=httpx.RequestError("timeout"),
            ):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    pool = WorkerPool(fetcher, client, max_workers=16)
                    pool.spawn_workers(2)

                    for i in range(4):
                        await pool.add_request(RequestMetadata(url=f"{TEST_URL}/{i}"))

                    for _ in range(4):
                        await asyncio.wait_for(pool.get_result(), timeout=2.0)
                        await pool.check_scaling()

                    assert pool.worker_count >= 1
                    await pool.shutdown_all()


class TestIntegration:
    """Integration tests for full fetch_batch using workers."""

    @pytest.mark.asyncio
    async def test_fetch_batch_with_workers(self) -> None:
        """fetch_batch_adaptive should use worker pool to process requests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=16)
            requests = [RequestMetadata(url=f"{TEST_URL}/{i}") for i in range(10)]

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                results = await fetcher.fetch_batch_adaptive(requests)

            assert len(results) == 10
            assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_fetch_batch_with_progress(self) -> None:
        """fetch_batch_adaptive should report progress."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=16)
            requests = [RequestMetadata(url=f"{TEST_URL}/{i}") for i in range(5)]
            progress_calls: list[int] = []

            def on_progress(c: int, t: int, r: FetchResult, p: int) -> None:
                del t, r, p
                progress_calls.append(c)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                results = await fetcher.fetch_batch_adaptive(requests, on_progress)

            assert len(results) == 5
            assert len(progress_calls) == 5
            assert progress_calls == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_fetch_batch_caches_results(self) -> None:
        """fetch_batch_adaptive should use cache for repeated requests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=16)
            requests = [RequestMetadata(url=f"{TEST_URL}/cached")]

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ) as mock_request:
                results1 = await fetcher.fetch_batch_adaptive(requests)
                assert len(results1) == 1
                assert results1[0].from_cache is False

                results2 = await fetcher.fetch_batch_adaptive(requests)
                assert len(results2) == 1
                assert results2[0].from_cache is True

                assert mock_request.call_count == 1
