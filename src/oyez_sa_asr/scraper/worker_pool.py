# Edited by Claude
"""Worker pool for adaptive parallel fetching with rate-based scaling."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx

    from .fetcher import AdaptiveFetcher
    from .models import FetchResult, RequestMetadata


class WorkerPool:
    """Manages a pool of worker coroutines with rate-based adaptive scaling.

    Scaling logic:
    - Doubles workers when throughput improves by >50%
    - Locks scaling when diminishing returns detected (<50% improvement)
    - Errors are handled by retries, not by reducing workers
    """

    def __init__(
        self,
        fetcher: AdaptiveFetcher,
        client: httpx.AsyncClient,
        max_workers: int = 1024,
        min_samples: int = 10,
    ) -> None:
        self.fetcher = fetcher
        self.client = client
        self.max_workers = max_workers
        self.min_samples = min_samples  # Minimum samples before measuring rate
        self.request_queue: asyncio.Queue[RequestMetadata | None] = asyncio.Queue()
        self.result_queue: asyncio.Queue[tuple[int, FetchResult]] = asyncio.Queue()
        self._workers: dict[int, asyncio.Task[None]] = {}
        self._shutdown_events: dict[int, asyncio.Event] = {}
        self._next_worker_id = 0

        # Rate tracking
        self._rate_window_start: float = time.monotonic()
        self._rate_window_count: int = 0
        self._last_rate: float = 0.0
        self._scaling_locked: bool = False  # Stop scaling when diminishing returns

    @property
    def worker_count(self) -> int:
        """Return number of active workers."""
        return len(self._workers)

    def spawn_workers(self, count: int) -> None:
        """Spawn additional workers."""
        to_spawn = min(count, self.max_workers - self.worker_count)
        for _ in range(to_spawn):
            worker_id = self._next_worker_id
            self._next_worker_id += 1
            shutdown_event = asyncio.Event()
            self._shutdown_events[worker_id] = shutdown_event
            task = asyncio.create_task(
                _worker_coroutine(
                    worker_id=worker_id,
                    client=self.client,
                    fetcher=self.fetcher,
                    request_queue=self.request_queue,
                    result_queue=self.result_queue,
                    shutdown_event=shutdown_event,
                )
            )
            self._workers[worker_id] = task

    def record_result(self, worker_id: int, result: FetchResult) -> None:
        """Record a result for rate tracking. Errors do not affect scaling."""
        del worker_id, result  # Unused - we only track count
        self._rate_window_count += 1

    def _reset_rate_window(self) -> None:
        """Reset the rate measurement window."""
        self._rate_window_start = time.monotonic()
        self._rate_window_count = 0

    async def check_scaling(self) -> None:
        """Check if scaling action is needed based on throughput improvement.

        Scales up only if throughput improves by >50%. Locks scaling when
        diminishing returns are detected.
        """
        if self._scaling_locked:
            return

        # Not enough samples yet
        if self._rate_window_count < self.min_samples:
            return

        # Calculate current rate
        elapsed = time.monotonic() - self._rate_window_start
        if elapsed <= 0:
            return

        current_rate = self._rate_window_count / elapsed

        # Check improvement threshold
        if self._last_rate > 0:
            improvement = (current_rate - self._last_rate) / self._last_rate
            if improvement < 0.5:  # Less than 50% improvement
                self._scaling_locked = True  # Diminishing returns - stop scaling
                return

        # Scale up: double workers
        if self.worker_count < self.max_workers:
            self._last_rate = current_rate
            self.spawn_workers(self.worker_count)  # Double
            self._reset_rate_window()

    async def _shutdown_workers(self, worker_ids: list[int]) -> None:
        """Shutdown specific workers by ID."""
        for wid in worker_ids:
            if wid in self._shutdown_events:
                self._shutdown_events[wid].set()
        for wid in worker_ids:
            if wid in self._workers:
                try:
                    await asyncio.wait_for(self._workers[wid], timeout=5.0)
                except asyncio.TimeoutError:
                    self._workers[wid].cancel()
                del self._workers[wid]
                del self._shutdown_events[wid]

    async def shutdown_all(self) -> None:
        """Shutdown all workers."""
        worker_ids = list(self._workers.keys())
        for wid in worker_ids:
            if wid in self._shutdown_events:
                self._shutdown_events[wid].set()
            await self.request_queue.put(None)
        for wid in worker_ids:
            if wid in self._workers:
                try:
                    await asyncio.wait_for(self._workers[wid], timeout=2.0)
                except asyncio.TimeoutError:
                    self._workers[wid].cancel()
        self._workers.clear()
        self._shutdown_events.clear()

    async def add_request(self, request: RequestMetadata) -> None:
        """Add a request to the queue."""
        await self.request_queue.put(request)

    async def get_result(self) -> FetchResult:
        """Get a result from the result queue and record it for scaling."""
        worker_id, result = await self.result_queue.get()
        self.record_result(worker_id, result)
        return result


async def _worker_coroutine(
    worker_id: int,
    client: httpx.AsyncClient,
    fetcher: AdaptiveFetcher,
    request_queue: asyncio.Queue[RequestMetadata | None],
    result_queue: asyncio.Queue[tuple[int, FetchResult]],
    shutdown_event: asyncio.Event,
) -> None:
    """Worker coroutine that fetches requests from queue until shutdown."""
    while not shutdown_event.is_set():
        try:
            request = await asyncio.wait_for(request_queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            continue

        if request is None:
            break

        result = await fetcher._fetch_network(client, request)
        retries = 0
        while fetcher._is_transient_failure(result) and retries < fetcher.max_retries:
            retries += 1
            await asyncio.sleep(0.1 * retries)
            result = await fetcher._fetch_network(client, request)

        await result_queue.put((worker_id, result))

        if shutdown_event.is_set():
            break
