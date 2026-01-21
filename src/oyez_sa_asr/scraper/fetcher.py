# Edited by Claude
"""Adaptive parallel fetcher with automatic scaling."""

import random
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from .cache import FileCache
from .models import FetchResult, RequestMetadata
from .worker_pool import WorkerPool

if TYPE_CHECKING:
    from .downloader import AsyncDownloader

# Type alias for progress callback: (completed, total, result, parallelism) -> None
ProgressCallback = Callable[[int, int, FetchResult, int], None]


class AdaptiveFetcher:
    """Fetcher with rate-based adaptive parallelism.

    Uses dependency injection for the download backend, supporting
    both HTTP (httpx) and S3 (aiobotocore) backends.
    """

    def __init__(
        self,
        downloader: "AsyncDownloader",
        *,
        max_parallelism: int = 10,
        min_improvement: float = 0.25,
    ) -> None:
        """Initialize the fetcher.

        Args:
            downloader: The async downloader backend.
            max_parallelism: Maximum number of parallel workers.
            min_improvement: Required rate improvement to scale up (0.25 = 25%).
        """
        self.downloader = downloader
        self.max_parallelism = max_parallelism
        self.min_improvement = min_improvement

    def _partition_cached(
        self, requests: Sequence[RequestMetadata], *, force: bool = False
    ) -> tuple[list[FetchResult], list[tuple[RequestMetadata, int]]]:
        """Partition requests into cached results and uncached.

        Args:
            requests: List of requests to partition.
            force: If True, bypass cache and fetch all requests.
        """
        results: list[FetchResult] = []
        needs_fetch: list[tuple[RequestMetadata, int]] = []
        for request in requests:
            if force:
                # Force mode: skip cache, fetch everything
                needs_fetch.append((request, 0))
            else:
                cached = self.downloader.check_cache(request)
                if cached:
                    results.append(cached)
                else:
                    needs_fetch.append((request, 0))
        return results, needs_fetch

    async def fetch_batch_adaptive(
        self,
        requests: Sequence[RequestMetadata],
        on_progress: ProgressCallback | None = None,
        *,
        force: bool = False,
    ) -> list[FetchResult]:
        """Fetch with worker-based adaptive parallelism.

        Args:
            requests: List of requests to fetch.
            on_progress: Optional callback for progress updates.
            force: If True, bypass cache and re-fetch all requests.
        """
        if not requests:
            return []

        shuffled = list(requests)
        random.shuffle(shuffled)
        cached_results, pending = self._partition_cached(shuffled, force=force)
        if not pending:
            return cached_results

        pending_count = len(pending)

        async with self.downloader.create_client() as client:
            pool = WorkerPool(
                self.downloader,
                client,
                max_workers=self.max_parallelism,
                min_improvement=self.min_improvement,
            )
            pool.spawn_workers(1)

            for req, _ in pending:
                await pool.add_request(req)

            fetched_results: list[FetchResult] = []
            while len(fetched_results) < pending_count:
                result = await pool.get_result()
                await pool.check_scaling()
                fetched_results.append(result)
                if on_progress:
                    on_progress(
                        len(fetched_results), pending_count, result, pool.worker_count
                    )

            await pool.shutdown_all()

        return cached_results + fetched_results

    async def fetch_one(
        self, request: RequestMetadata, *, force: bool = False
    ) -> FetchResult:
        """Fetch a single request (convenience wrapper)."""
        results = await self.fetch_batch_adaptive([request], force=force)
        return results[0]

    async def fetch_batch(
        self, requests: Sequence[RequestMetadata], *, force: bool = False
    ) -> list[FetchResult]:
        """Fetch a batch (alias for fetch_batch_adaptive without progress)."""
        return await self.fetch_batch_adaptive(requests, force=force)

    @classmethod
    def create(
        cls,
        cache_dir: Path,
        ttl_days: int = 30,
        max_parallelism: int = 10,
        timeout: float = 30.0,
        max_retries: int = 3,
        min_improvement: float = 0.25,
        expected_unavailable_codes: frozenset[int] | None = None,
    ) -> "AdaptiveFetcher":
        """Create a fetcher with HTTP backend (default)."""
        from .httpx_downloader import HttpxDownloader  # noqa: PLC0415

        cache = FileCache(cache_dir, ttl_days=ttl_days)
        downloader = HttpxDownloader(
            cache,
            timeout=timeout,
            max_retries=max_retries,
            expected_unavailable_codes=expected_unavailable_codes,
        )
        return cls(
            downloader,
            max_parallelism=max_parallelism,
            min_improvement=min_improvement,
        )

    @classmethod
    def create_s3(
        cls,
        cache_dir: Path,
        max_parallelism: int = 64,
        max_retries: int = 3,
        min_improvement: float = 0.25,
        expected_unavailable_codes: frozenset[int] | None = None,
    ) -> "AdaptiveFetcher":
        """Create a fetcher with S3 backend for audio downloads."""
        from .s3_downloader import S3Downloader  # noqa: PLC0415

        downloader = S3Downloader(
            cache_dir,
            max_retries=max_retries,
            expected_unavailable_codes=expected_unavailable_codes,
        )
        return cls(
            downloader,
            max_parallelism=max_parallelism,
            min_improvement=min_improvement,
        )
