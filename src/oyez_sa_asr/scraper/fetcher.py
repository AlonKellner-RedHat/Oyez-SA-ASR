# Edited by Claude
"""Adaptive parallel fetcher with automatic scaling."""

import asyncio
import json
from collections.abc import Sequence
from pathlib import Path

import httpx

from .cache import FileCache
from .models import FetchResult, RequestMetadata


class AdaptiveFetcher:
    """HTTP fetcher with adaptive parallelism.

    Starts with parallelism=1 and increases on success.
    On any error, halves parallelism and freezes increases.
    """

    def __init__(
        self,
        cache: FileCache,
        *,
        initial_parallelism: int = 1,
        max_parallelism: int = 10,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the fetcher.

        Args:
            cache: The file cache to use.
            initial_parallelism: Starting parallelism level.
            max_parallelism: Maximum parallelism level.
            timeout: Request timeout in seconds.
        """
        self.cache = cache
        self.parallelism = initial_parallelism
        self.max_parallelism = max_parallelism
        self.timeout = timeout
        self._frozen = False
        self._semaphore: asyncio.Semaphore | None = None

    def _update_semaphore(self) -> None:
        """Update the semaphore to match current parallelism."""
        self._semaphore = asyncio.Semaphore(self.parallelism)

    def _increase_parallelism(self, batch_size: int | None = None) -> None:
        """Increase parallelism if not frozen and below max.

        Args:
            batch_size: Current batch size to cap parallelism at.
        """
        if self._frozen:
            return
        max_allowed = self.max_parallelism
        if batch_size is not None:
            max_allowed = min(max_allowed, batch_size)
        if self.parallelism < max_allowed:
            self.parallelism += 1
            self._update_semaphore()

    def _decrease_parallelism(self) -> None:
        """Decrease parallelism and freeze further increases."""
        self._frozen = True
        self.parallelism = max(1, self.parallelism // 2)
        self._update_semaphore()

    def _parse_cached_response(self, raw_bytes: bytes, content_type: str) -> object:
        """Parse cached raw bytes based on content type."""
        if "json" in content_type:
            return json.loads(raw_bytes.decode("utf-8"))
        return raw_bytes

    async def _fetch_one(
        self,
        client: httpx.AsyncClient,
        request: RequestMetadata,
    ) -> FetchResult:
        """Fetch a single request, using cache if available.

        Args:
            client: The HTTP client to use.
            request: The request to fetch.

        Returns
        -------
            The fetch result.
        """
        # Check cache first
        cached = self.cache.get(request)
        if cached is not None:
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

        # Fetch from network
        try:
            response = await client.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
            )
            response.raise_for_status()

            # Capture raw bytes and content type
            raw_bytes = response.content
            content_type = response.headers.get("content-type", "application/json")

            # Parse data based on content type
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
            self.cache.set(request, result)
            return result

        except httpx.RequestError as e:
            result = FetchResult(
                url=request.url,
                success=False,
                error=str(e),
            )
            self.cache.set(request, result)
            return result

    async def _fetch_with_semaphore(
        self,
        client: httpx.AsyncClient,
        request: RequestMetadata,
    ) -> FetchResult:
        """Fetch with semaphore-controlled concurrency."""
        if self._semaphore is None:
            self._update_semaphore()

        async with self._semaphore:  # type: ignore[union-attr]
            return await self._fetch_one(client, request)

    async def fetch_batch(
        self,
        requests: Sequence[RequestMetadata],
    ) -> list[FetchResult]:
        """Fetch a batch of requests with adaptive parallelism.

        Args:
            requests: The requests to fetch.

        Returns
        -------
            List of fetch results.
        """
        if not requests:
            return []

        self._update_semaphore()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = [self._fetch_with_semaphore(client, req) for req in requests]
            results = await asyncio.gather(*tasks)

        # Adjust parallelism based on results
        has_errors = any(not r.success and not r.from_cache for r in results)
        has_new_successes = any(r.success and not r.from_cache for r in results)

        if has_errors:
            self._decrease_parallelism()
        elif has_new_successes:
            self._increase_parallelism(batch_size=len(requests))

        return list(results)

    async def fetch_one(self, request: RequestMetadata) -> FetchResult:
        """Fetch a single request.

        Args:
            request: The request to fetch.

        Returns
        -------
            The fetch result.
        """
        results = await self.fetch_batch([request])
        return results[0]

    @classmethod
    def create(
        cls,
        cache_dir: Path,
        ttl_days: int = 30,
        initial_parallelism: int = 1,
        max_parallelism: int = 10,
        timeout: float = 30.0,
    ) -> "AdaptiveFetcher":
        """Create a fetcher with a new cache.

        Args:
            cache_dir: Directory for the cache.
            ttl_days: Cache TTL in days.
            initial_parallelism: Starting parallelism level.
            max_parallelism: Maximum parallelism level.
            timeout: Request timeout in seconds.

        Returns
        -------
            A new AdaptiveFetcher instance.
        """
        cache = FileCache(cache_dir, ttl_days=ttl_days)
        return cls(
            cache,
            initial_parallelism=initial_parallelism,
            max_parallelism=max_parallelism,
            timeout=timeout,
        )
