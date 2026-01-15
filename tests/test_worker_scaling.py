# Edited by Claude
"""Tests for worker pool scaling logic and integration."""

import tempfile
import time
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


class TestRateBasedScaling:
    """Tests for rate-based scaling logic."""

    @pytest.mark.asyncio
    async def test_scale_up_when_rate_improves_enough(self) -> None:
        """Should scale up when throughput improves by more than min_improvement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=16)

            async with httpx.AsyncClient(timeout=30.0) as client:
                pool = WorkerPool(
                    fetcher.downloader, client, max_workers=16, min_samples=2
                )
                pool.spawn_workers(1)
                initial_count = pool.worker_count

                # Simulate first rate window: 2 requests in 1 second = 2 req/s
                pool._rate_window_start = time.monotonic() - 1.0
                pool.record_result(
                    0, FetchResult(url=TEST_URL, success=True, status_code=200)
                )
                pool.record_result(
                    0, FetchResult(url=TEST_URL, success=True, status_code=200)
                )

                await pool.check_scaling()
                # First scale-up should happen (no previous rate to compare)
                assert pool.worker_count > initial_count
                await pool.shutdown_all()

    @pytest.mark.asyncio
    async def test_no_scale_up_when_rate_improves_below_threshold(self) -> None:
        """Should lock scaling when improvement is less than min_improvement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=16)

            async with httpx.AsyncClient(timeout=30.0) as client:
                pool = WorkerPool(
                    fetcher.downloader, client, max_workers=16, min_samples=2
                )
                pool.spawn_workers(2)

                # Set a previous rate of 10 req/s
                pool._last_rate = 10.0

                # Simulate current window: 2 requests in 0.2s = 10 req/s (0% improvement)
                pool._rate_window_start = time.monotonic() - 0.2
                pool.record_result(
                    0, FetchResult(url=TEST_URL, success=True, status_code=200)
                )
                pool.record_result(
                    1, FetchResult(url=TEST_URL, success=True, status_code=200)
                )

                count_before = pool.worker_count
                await pool.check_scaling()

                # Should not scale up (no improvement)
                assert pool.worker_count == count_before
                assert pool._scaling_locked is True
                await pool.shutdown_all()

    @pytest.mark.asyncio
    async def test_scaling_locked_persists(self) -> None:
        """Once scaling is locked, no more scaling attempts should occur."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=16)

            async with httpx.AsyncClient(timeout=30.0) as client:
                pool = WorkerPool(
                    fetcher.downloader, client, max_workers=16, min_samples=2
                )
                pool.spawn_workers(2)
                pool._scaling_locked = True  # Pre-lock scaling

                # Even with good conditions, should not scale
                pool._rate_window_start = time.monotonic() - 0.1
                for _ in range(10):
                    pool.record_result(
                        0, FetchResult(url=TEST_URL, success=True, status_code=200)
                    )

                count_before = pool.worker_count
                await pool.check_scaling()

                assert pool.worker_count == count_before
                await pool.shutdown_all()

    @pytest.mark.asyncio
    async def test_errors_do_not_trigger_scale_down(self) -> None:
        """Errors should not trigger scale-down, only retries handle them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(
                Path(tmpdir), max_parallelism=16, max_retries=0
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                pool = WorkerPool(
                    fetcher.downloader, client, max_workers=16, min_samples=10
                )
                pool.spawn_workers(4)
                initial_count = pool.worker_count

                # Record failures - less than min_samples so no scaling happens
                for i in range(4):
                    pool.record_result(
                        i, FetchResult(url=TEST_URL, success=False, status_code=500)
                    )

                await pool.check_scaling()

                # Worker count should NOT decrease due to errors
                # (In old logic, ANY error would halve workers)
                assert pool.worker_count >= initial_count
                await pool.shutdown_all()

    @pytest.mark.asyncio
    async def test_scale_up_requires_min_samples(self) -> None:
        """Should not scale up until min_samples are collected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir), max_parallelism=16)

            async with httpx.AsyncClient(timeout=30.0) as client:
                pool = WorkerPool(
                    fetcher.downloader, client, max_workers=16, min_samples=5
                )
                pool.spawn_workers(1)

                # Only 2 samples (less than min_samples=5)
                pool._rate_window_start = time.monotonic() - 1.0
                pool.record_result(
                    0, FetchResult(url=TEST_URL, success=True, status_code=200)
                )
                pool.record_result(
                    0, FetchResult(url=TEST_URL, success=True, status_code=200)
                )

                count_before = pool.worker_count
                await pool.check_scaling()

                # Should not scale (not enough samples)
                assert pool.worker_count == count_before
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
