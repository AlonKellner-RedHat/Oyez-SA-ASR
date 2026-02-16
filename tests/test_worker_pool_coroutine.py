# Edited by Cursor: split from test_worker_pool (lintok; plan).
"""Tests for worker coroutine (TestWorkerCoroutine)."""

import asyncio
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from oyez_sa_asr.scraper import AdaptiveFetcher, RequestMetadata
from oyez_sa_asr.scraper.worker_pool import _worker_coroutine

if TYPE_CHECKING:
    from oyez_sa_asr.scraper.models import FetchResult

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
