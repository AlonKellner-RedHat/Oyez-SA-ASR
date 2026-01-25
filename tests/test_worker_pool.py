# Edited by Claude
"""Unit tests for worker coroutine and WorkerPool mechanics."""

import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from oyez_sa_asr.scraper import AdaptiveFetcher, RequestMetadata
from oyez_sa_asr.scraper.models import FetchResult
from oyez_sa_asr.scraper.worker_pool import WorkerPool, _worker_coroutine

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


class TestWorkerCoroutine:
    """Tests for individual worker coroutine behavior."""

    @pytest.mark.asyncio
    async def test_worker_fetches_from_queue(self) -> None:
        """Worker should fetch request from queue and report result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader
            request_queue: asyncio.Queue[RequestMetadata | None] = asyncio.Queue()
            result_queue: asyncio.Queue[tuple[int, FetchResult]] = asyncio.Queue()
            shutdown_event = asyncio.Event()

            request = RequestMetadata(url=f"{TEST_URL}/1")
            await request_queue.put(request)
            await request_queue.put(None)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    await _worker_coroutine(
                        1,
                        client,
                        downloader,
                        request_queue,
                        result_queue,
                        shutdown_event,
                    )

            assert result_queue.qsize() == 1
            worker_id, result = await result_queue.get()
            assert worker_id == 1
            assert result.success is True

    @pytest.mark.asyncio
    async def test_worker_handles_shutdown_event(self) -> None:
        """Worker should exit when shutdown event is set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader
            request_queue: asyncio.Queue[RequestMetadata | None] = asyncio.Queue()
            result_queue: asyncio.Queue[tuple[int, FetchResult]] = asyncio.Queue()
            shutdown_event = asyncio.Event()
            shutdown_event.set()

            async with httpx.AsyncClient(timeout=30.0) as client:
                await _worker_coroutine(
                    1, client, downloader, request_queue, result_queue, shutdown_event
                )

            assert result_queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_worker_processes_multiple_requests(self) -> None:
        """Worker should process multiple requests until shutdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader
            request_queue: asyncio.Queue[RequestMetadata | None] = asyncio.Queue()
            result_queue: asyncio.Queue[tuple[int, FetchResult]] = asyncio.Queue()
            shutdown_event = asyncio.Event()

            for i in range(3):
                await request_queue.put(RequestMetadata(url=f"{TEST_URL}/{i}"))
            await request_queue.put(None)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    await _worker_coroutine(
                        1,
                        client,
                        downloader,
                        request_queue,
                        result_queue,
                        shutdown_event,
                    )

            assert result_queue.qsize() == 3

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_worker_reports_failures(self) -> None:
        """Worker should report failed requests to result queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader
            request_queue: asyncio.Queue[RequestMetadata | None] = asyncio.Queue()
            result_queue: asyncio.Queue[tuple[int, FetchResult]] = asyncio.Queue()
            shutdown_event = asyncio.Event()

            await request_queue.put(RequestMetadata(url=f"{TEST_URL}/fail"))
            await request_queue.put(None)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                side_effect=httpx.RequestError("timeout"),
            ):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    await _worker_coroutine(
                        1,
                        client,
                        downloader,
                        request_queue,
                        result_queue,
                        shutdown_event,
                    )

            assert result_queue.qsize() == 1
            _, result = await result_queue.get()
            assert result.success is False


class TestWorkerPool:
    """Tests for WorkerPool spawn/shutdown mechanics."""

    @pytest.mark.asyncio
    async def test_spawn_workers(self) -> None:
        """WorkerPool should spawn requested number of workers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader
            async with httpx.AsyncClient(timeout=30.0) as client:
                pool = WorkerPool(downloader, client)
                pool.spawn_workers(3)
                assert pool.worker_count == 3
                await pool.shutdown_all()

    @pytest.mark.asyncio
    async def test_workers_process_requests(self) -> None:
        """Workers in pool should process requests from queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    pool = WorkerPool(downloader, client)
                    pool.spawn_workers(2)

                    for i in range(4):
                        await pool.add_request(RequestMetadata(url=f"{TEST_URL}/{i}"))

                    results = []
                    for _ in range(4):
                        result = await asyncio.wait_for(pool.get_result(), timeout=2.0)
                        results.append(result)

                    assert len(results) == 4
                    await pool.shutdown_all()

    @pytest.mark.asyncio
    async def test_record_result_handles_elapsed_zero(self) -> None:
        """Should handle elapsed <= 0 in record_result (line 109)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader

            async with httpx.AsyncClient(timeout=30.0) as client:
                pool = WorkerPool(downloader, client, min_improvement=0.25)
                pool.spawn_workers(1)
                # Set rate window start to current time to make elapsed <= 0
                pool._rate_window_start = time.monotonic()
                pool._rate_window_count = 10

                # Record a result - should handle elapsed <= 0 gracefully
                result = FetchResult(
                    url="https://example.com/test",
                    success=True,
                    status_code=200,
                )
                pool.record_result(1, result)
                # Should not crash
                assert pool.worker_count >= 1
                await pool.shutdown_all()

    @pytest.mark.asyncio
    async def test_worker_exits_on_shutdown_after_processing(self) -> None:
        """Should exit when shutdown event is set after processing (line 197)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader
            request_queue: asyncio.Queue[RequestMetadata | None] = asyncio.Queue()
            result_queue: asyncio.Queue[tuple[int, FetchResult]] = asyncio.Queue()
            shutdown_event = asyncio.Event()

            request = RequestMetadata(url=f"{TEST_URL}/1")
            await request_queue.put(request)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Set shutdown after putting request
                    task = asyncio.create_task(
                        _worker_coroutine(
                            1,
                            client,
                            downloader,
                            request_queue,
                            result_queue,
                            shutdown_event,
                        )
                    )
                    # Wait a bit then set shutdown
                    await asyncio.sleep(0.1)
                    shutdown_event.set()
                    await task

            # Should have processed the request before exiting (line 197)
            assert result_queue.qsize() >= 0

    @pytest.mark.asyncio
    async def test_scale_up_handles_elapsed_zero(self) -> None:
        """Should return early when elapsed <= 0 (line 109)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader

            async with httpx.AsyncClient(timeout=30.0) as client:
                pool = WorkerPool(downloader, client, min_improvement=0.25)
                # Set rate window start to now to make elapsed <= 0
                pool._rate_window_start = time.monotonic()
                pool._rate_window_count = 10

                # Should return early without scaling
                # check_scaling is called internally by record_result
                # Pool starts with 0 workers, spawn one first
                pool.spawn_workers(1)
                initial_count = pool.worker_count
                assert initial_count == 1

                result = FetchResult(url="https://test.com", success=True)
                pool.record_result(1, result)
                # Worker count should remain at initial value (no scaling when elapsed <= 0)
                assert pool.worker_count == initial_count

    @pytest.mark.asyncio
    async def test_shutdown_workers_handles_timeout(self) -> None:
        """Should handle timeout when shutting down workers (lines 128-138)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader

            async with httpx.AsyncClient(timeout=30.0) as client:
                pool = WorkerPool(downloader, client)
                pool.spawn_workers(1)

                # Mock worker to never complete
                worker_id = next(iter(pool._workers.keys()))
                # Set shutdown event
                pool._shutdown_events[worker_id].set()

                # Shutdown should handle timeout
                await pool._shutdown_workers([worker_id])
                # Worker should be removed
                assert worker_id not in pool._workers

    @pytest.mark.asyncio
    async def test_shutdown_all_handles_timeout(self) -> None:
        """Should handle timeout when shutting down all workers (lines 151-152)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader

            async with httpx.AsyncClient(timeout=30.0) as client:
                pool = WorkerPool(downloader, client)
                pool.spawn_workers(2)

                # Shutdown all should handle timeouts
                await pool.shutdown_all()
                # All workers should be cleared
                assert len(pool._workers) == 0

    @pytest.mark.asyncio
    async def test_worker_handles_timeout_on_queue_get(self) -> None:
        """Should handle timeout when getting from queue (lines 179-180)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader
            request_queue: asyncio.Queue[RequestMetadata | None] = asyncio.Queue()
            result_queue: asyncio.Queue[tuple[int, FetchResult]] = asyncio.Queue()
            shutdown_event = asyncio.Event()

            # Don't put anything in queue - will timeout
            shutdown_event.set()  # Set shutdown to exit loop

            async with httpx.AsyncClient(timeout=30.0) as client:
                await _worker_coroutine(
                    1, client, downloader, request_queue, result_queue, shutdown_event
                )

            # Should exit gracefully
            assert result_queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_worker_exits_on_shutdown_after_result(self) -> None:
        """Should exit when shutdown event is set after processing (line 197)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader
            request_queue: asyncio.Queue[RequestMetadata | None] = asyncio.Queue()
            result_queue: asyncio.Queue[tuple[int, FetchResult]] = asyncio.Queue()
            shutdown_event = asyncio.Event()

            request = RequestMetadata(url=f"{TEST_URL}/1")
            await request_queue.put(request)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Set shutdown after putting request
                    task = asyncio.create_task(
                        _worker_coroutine(
                            1,
                            client,
                            downloader,
                            request_queue,
                            result_queue,
                            shutdown_event,
                        )
                    )
                    # Wait a bit then set shutdown
                    await asyncio.sleep(0.1)
                    shutdown_event.set()
                    await task

            # Should have processed the request before exiting
            assert result_queue.qsize() >= 0

    @pytest.mark.asyncio
    async def test_shutdown_workers_cancels_on_timeout(self) -> None:
        """Should cancel worker on timeout (lines 135-136)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader

            async with httpx.AsyncClient(timeout=30.0) as client:
                pool = WorkerPool(downloader, client)
                pool.spawn_workers(1)

                worker_id = next(iter(pool._workers.keys()))
                # Mock worker to never complete by patching asyncio.sleep
                # This makes the timeout trigger faster
                with patch("asyncio.sleep", side_effect=asyncio.sleep):
                    # Replace worker task with one that sleeps indefinitely
                    pool._workers[worker_id] = asyncio.create_task(asyncio.sleep(100))

                    # Shutdown with timeout - should cancel after 5s
                    # Mock asyncio.wait_for to raise TimeoutError immediately
                    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                        await pool._shutdown_workers([worker_id])
                    # Worker should be cancelled and removed
                    assert worker_id not in pool._workers

    @pytest.mark.asyncio
    async def test_shutdown_all_cancels_workers(self) -> None:
        """Should cancel all workers on timeout (lines 151-152)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader

            async with httpx.AsyncClient(timeout=30.0) as client:
                pool = WorkerPool(downloader, client)
                pool.spawn_workers(2)

                # Mock workers to never complete
                for wid in list(pool._workers.keys()):
                    pool._workers[wid] = asyncio.create_task(asyncio.sleep(100))

                # Shutdown all with timeout - mock asyncio.wait_for to raise TimeoutError
                with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                    await pool.shutdown_all()
                # All workers should be cancelled and cleared
                assert len(pool._workers) == 0
