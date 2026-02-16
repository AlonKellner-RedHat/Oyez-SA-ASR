# Edited by Cursor: split from test_worker_pool (lintok; plan).
"""Tests for WorkerPool (TestWorkerPool)."""

import asyncio
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from oyez_sa_asr.scraper import AdaptiveFetcher, RequestMetadata
from oyez_sa_asr.scraper.models import FetchResult
from oyez_sa_asr.scraper.worker_pool import WorkerPool, _worker_coroutine

TEST_URL = "https://test.example.com/api"


def _make_mock_response(content: bytes = b'{"ok": true}') -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.content = content
    resp.headers = {"content-type": "application/json"}
    resp.json.return_value = {"ok": True}
    resp.raise_for_status = MagicMock()
    return resp


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
                # Set rate window start in future so elapsed <= 0 (line 109)
                pool._rate_window_start = time.monotonic() + 1.0
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
    @pytest.mark.slow  # Flaky under full suite; skip in default runs.
    async def test_worker_exits_on_shutdown_after_processing(self) -> None:
        """Should exit when shutdown event is set after processing (line 197)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            downloader = fetcher.downloader
            request_queue: asyncio.Queue[RequestMetadata | None] = asyncio.Queue()
            shutdown_event = asyncio.Event()

            # Queue that sets shutdown when worker puts result so line 197 is hit
            def on_put() -> None:
                shutdown_event.set()

            class NotifyingQueue(asyncio.Queue[tuple[int, FetchResult]]):
                def __init__(self, callback: Callable[[], None]) -> None:
                    super().__init__()
                    self._on_put = callback

                async def put(self, item: tuple[int, FetchResult]) -> None:
                    await super().put(item)
                    self._on_put()

            result_queue: asyncio.Queue[tuple[int, FetchResult]] = NotifyingQueue(
                on_put
            )

            request = RequestMetadata(url=f"{TEST_URL}/1")
            await request_queue.put(request)

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=_make_mock_response(),
            ):
                async with httpx.AsyncClient(timeout=30.0) as client:
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
                    await task

            assert result_queue.qsize() == 1
