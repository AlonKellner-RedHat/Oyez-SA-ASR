# Edited by Claude
"""Unit tests for AdaptiveFetcher streaming functionality."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from oyez_sa_asr.scraper import AdaptiveFetcher, RequestMetadata
from oyez_sa_asr.scraper.models import FetchResult


class TestFetchBatchStreaming:
    """Tests for fetch_batch_streaming method."""

    @pytest.mark.asyncio
    async def test_calls_progress_callback(self) -> None:
        """Should call progress callback for each completed request."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            requests = [
                RequestMetadata(url="https://example.com/1"),
                RequestMetadata(url="https://example.com/2"),
            ]

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b'{"test": true}'
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"test": True}
            mock_response.raise_for_status = MagicMock()

            progress_calls: list[tuple[int, int, FetchResult]] = []

            def on_progress(completed: int, total: int, result: FetchResult) -> None:
                progress_calls.append((completed, total, result))

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=mock_response,
            ):
                results = await fetcher.fetch_batch_streaming(requests, on_progress)

            assert len(results) == 2
            assert len(progress_calls) == 2
            assert progress_calls[-1][0] == 2
            assert progress_calls[-1][1] == 2

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        """Should handle empty request list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            results = await fetcher.fetch_batch_streaming([])
            assert results == []

    @pytest.mark.asyncio
    async def test_without_callback(self) -> None:
        """Should work without progress callback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = AdaptiveFetcher.create(Path(tmpdir))
            requests = [RequestMetadata(url="https://example.com/1")]

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b'{"ok": true}'
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"ok": True}
            mock_response.raise_for_status = MagicMock()

            with patch.object(
                httpx.AsyncClient,
                "request",
                new_callable=AsyncMock,
                return_value=mock_response,
            ):
                results = await fetcher.fetch_batch_streaming(requests)

            assert len(results) == 1
            assert results[0].success is True
