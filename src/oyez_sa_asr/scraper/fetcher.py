# Edited by Claude
"""Adaptive parallel fetcher with automatic scaling."""

import json
import random
from collections.abc import Callable, Sequence
from pathlib import Path

import httpx

from .cache import FileCache
from .models import FetchResult, RequestMetadata
from .worker_pool import WorkerPool

# Type alias for progress callback: (completed, total, result, parallelism) -> None
ProgressCallback = Callable[[int, int, FetchResult, int], None]


class AdaptiveFetcher:
    """HTTP fetcher with rate-based adaptive parallelism."""

    def __init__(
        self,
        cache: FileCache,
        *,
        max_parallelism: int = 10,
        timeout: float = 30.0,
        max_retries: int = 3,
        min_improvement: float = 0.25,
    ) -> None:
        """Initialize the fetcher."""
        self.cache = cache
        self.max_parallelism = max_parallelism
        self.timeout = timeout
        self.max_retries = max_retries
        self.min_improvement = min_improvement  # Required rate improvement to scale up

    def _parse_cached_response(self, raw_bytes: bytes, content_type: str) -> object:
        """Parse cached raw bytes based on content type."""
        if "json" in content_type:
            return json.loads(raw_bytes.decode("utf-8"))
        return raw_bytes

    def _is_transient_failure(self, result: FetchResult) -> bool:
        """Check if failure is transient (429, 502-504, connection errors)."""
        if result.success:
            return False
        transient_codes = {429, 502, 503, 504}
        return result.status_code in transient_codes or result.status_code is None

    def _check_cache(self, request: RequestMetadata) -> FetchResult | None:
        """Check cache for a request, return result if cached."""
        cached = self.cache.get(request)
        if cached is None:
            return None
        content_type = cached.meta.content_type
        data = self._parse_cached_response(cached.response, content_type)
        return FetchResult(
            url=request.url,
            success=True,
            status_code=cached.status_code,
            data=data,
            raw_data=cached.response,
            content_type=content_type,
            from_cache=True,
        )

    async def _fetch_network(
        self, client: httpx.AsyncClient, request: RequestMetadata
    ) -> FetchResult:
        """Fetch from network only (no cache check)."""
        try:
            response = await client.request(
                method=request.method, url=request.url, headers=request.headers
            )
            response.raise_for_status()
            raw_bytes = response.content
            content_type = response.headers.get("content-type", "application/json")
            data = response.json() if "json" in content_type else raw_bytes
            result = FetchResult(
                url=request.url,
                success=True,
                status_code=response.status_code,
                data=data,
                raw_data=raw_bytes,
                content_type=content_type,
                from_cache=False,
            )
            self.cache.set(request, result)
            return result

        except httpx.HTTPStatusError as e:
            result = FetchResult(
                url=request.url,
                success=False,
                status_code=e.response.status_code,
                error=str(e),
            )
            if not self._is_transient_failure(result):
                self.cache.set(request, result)
            return result

        except httpx.RequestError as e:
            return FetchResult(url=request.url, success=False, error=str(e))

    def _partition_cached(
        self, requests: Sequence[RequestMetadata]
    ) -> tuple[list[FetchResult], list[tuple[RequestMetadata, int]]]:
        """Partition requests into cached results and uncached (with retry count 0)."""
        results: list[FetchResult] = []
        needs_fetch: list[tuple[RequestMetadata, int]] = []
        for request in requests:
            cached = self._check_cache(request)
            if cached:
                results.append(cached)
            else:
                needs_fetch.append((request, 0))
        return results, needs_fetch

    async def fetch_batch_adaptive(
        self,
        requests: Sequence[RequestMetadata],
        on_progress: ProgressCallback | None = None,
    ) -> list[FetchResult]:
        """Fetch with worker-based adaptive parallelism."""
        if not requests:
            return []

        shuffled = list(requests)
        random.shuffle(shuffled)
        cached_results, pending = self._partition_cached(shuffled)
        if not pending:
            return cached_results

        pending_count = len(pending)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            pool = WorkerPool(
                self,
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
                    # Report: completed uncached, total uncached, result, parallelism
                    on_progress(
                        len(fetched_results), pending_count, result, pool.worker_count
                    )

            await pool.shutdown_all()

        return cached_results + fetched_results

    async def fetch_one(self, request: RequestMetadata) -> FetchResult:
        """Fetch a single request (convenience wrapper)."""
        results = await self.fetch_batch_adaptive([request])
        return results[0]

    async def fetch_batch(
        self, requests: Sequence[RequestMetadata]
    ) -> list[FetchResult]:
        """Fetch a batch (alias for fetch_batch_adaptive without progress)."""
        return await self.fetch_batch_adaptive(requests)

    @classmethod
    def create(
        cls,
        cache_dir: Path,
        ttl_days: int = 30,
        max_parallelism: int = 10,
        timeout: float = 30.0,
        max_retries: int = 3,
        min_improvement: float = 0.25,
    ) -> "AdaptiveFetcher":
        """Create a fetcher with a new cache."""
        cache = FileCache(cache_dir, ttl_days=ttl_days)
        return cls(
            cache,
            max_parallelism=max_parallelism,
            timeout=timeout,
            max_retries=max_retries,
            min_improvement=min_improvement,
        )
