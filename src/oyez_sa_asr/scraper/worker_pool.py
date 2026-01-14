# Edited by Claude
"""Worker pool for adaptive parallel fetching."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx

    from .fetcher import AdaptiveFetcher
    from .models import FetchResult, RequestMetadata


class WorkerPool:
    """Manages a pool of worker coroutines for parallel fetching."""

    def __init__(
        self,
        fetcher: AdaptiveFetcher,
        client: httpx.AsyncClient,
        max_workers: int = 1024,
    ) -> None:
        self.fetcher = fetcher
        self.client = client
        self.max_workers = max_workers
        self.request_queue: asyncio.Queue[RequestMetadata | None] = asyncio.Queue()
        self.result_queue: asyncio.Queue[tuple[int, FetchResult]] = asyncio.Queue()
        self._workers: dict[int, asyncio.Task[None]] = {}
        self._shutdown_events: dict[int, asyncio.Event] = {}
        self._next_worker_id = 0
        self._worker_successes: dict[int, bool] = {}
        self._had_failure = False
        self._pending_scale_down = False

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
            self._worker_successes[worker_id] = False
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
        """Record a result from a worker for scaling decisions."""
        if result.success:
            if worker_id in self._worker_successes:
                self._worker_successes[worker_id] = True
        else:
            self._had_failure = True
            self._pending_scale_down = True

    async def check_scaling(self) -> None:
        """Check if scaling action is needed and trigger it."""
        if self._pending_scale_down:
            self._pending_scale_down = False
            await self.shutdown_half()
            return

        if self.worker_count > 0 and all(self._worker_successes.values()):
            current = self.worker_count
            if current < self.max_workers:
                self.spawn_workers(current)
                for wid in self._worker_successes:
                    self._worker_successes[wid] = False
                self._had_failure = False

    async def shutdown_half(self) -> None:
        """Shutdown half of the workers (minimum 1 remains)."""
        current = self.worker_count
        to_shutdown = current // 2
        if current - to_shutdown < 1:
            to_shutdown = current - 1
        if to_shutdown <= 0:
            return
        worker_ids = list(self._workers.keys())[:to_shutdown]
        await self._shutdown_workers(worker_ids)

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
                if wid in self._worker_successes:
                    del self._worker_successes[wid]

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
        self._worker_successes.clear()

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
