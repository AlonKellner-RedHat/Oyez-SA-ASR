# Edited by Claude, Cursor. Edited by Cursor: split impl to _cli_dataset_simple_proc_impl (lintok; plan).
"""Processing helpers for simple dataset with parallel audio embedding."""

import logging
import multiprocessing as mp
import os
import random
from concurrent.futures import BrokenExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from tqdm import tqdm

from ._cli_dataset_simple_proc_impl import (
    _build_work_items,
    _process_single_recording_impl,
    _ShardWriter,
    _WorkerShardWriter,
    group_utterances_by_recording,
)
from .memory_utils import (
    check_oom,
    get_memory_usage_mb,
    get_oom_kill_count,
    get_swap_usage_mb,
    kill_orphan_workers,
    set_pdeathsig,
)

# Re-exported for tests; keep so ruff does not remove as unused.
__all__ = [
    "_ShardWriter",
    "group_utterances_by_recording",
    "process_by_recording",
    "process_single_recording",
]

logger = logging.getLogger(__name__)

try:
    _MP_CONTEXT = mp.get_context("spawn")
except ValueError:
    _MP_CONTEXT = None

_worker_state: dict[str, Any] = {}


def _init_worker() -> None:
    """Initialize worker. Edited by Claude."""
    set_pdeathsig()


def process_single_recording(
    args: tuple[tuple[str, str, str], list[dict[str, Any]], Path, Path, int],
) -> tuple[int, int]:
    """Process a single recording and write shards directly to disk.

    Returns (embedded_count, error_count). Edited by Claude.
    """
    key, rec_utterances, audio_path, data_dir, target_bytes = args

    from oyez_sa_asr.cli_dataset_simple_core import require_pyarrow  # noqa: PLC0415

    pa, pq = require_pyarrow()

    worker_id = os.getpid() % 1000
    writer_key = f"writer_{worker_id}"

    if writer_key not in _worker_state:
        _worker_state[writer_key] = _WorkerShardWriter(
            data_dir, target_bytes, pa, pq, worker_id
        )

    writer = _worker_state[writer_key]

    try:
        rows, errors = _process_single_recording_impl(key, rec_utterances, audio_path)
        if rows:
            for row in rows:
                writer.add_row(row)
            writer.maybe_flush()
        return len(rows), errors
    except Exception as e:
        logger.exception("Worker crashed processing %s: %s", audio_path, e)
        return 0, len(rec_utterances)


def process_by_recording(
    utterances: list[dict[str, Any]],
    audio_paths: dict[tuple[str, str, str], Path],
    output_dir: Path,
    shard_size_mb: int,
    pa: Any,  # noqa: ARG001
    pq: Any,  # noqa: ARG001
    workers: int = 1,
) -> dict[str, int]:
    """Process utterances grouped by recording for efficiency."""
    kill_orphan_workers()

    initial_oom = get_oom_kill_count()
    used_mb, available_mb, _ = get_memory_usage_mb()
    swap_used_mb, swap_total_mb = get_swap_usage_mb()
    logger.info(
        "Starting processing: %d MB used, %d MB available, %d MB swap used/%d MB total, %d workers",
        used_mb,
        available_mb,
        swap_used_mb,
        swap_total_mb,
        workers,
    )

    data_dir = output_dir / "data" / "utterances"
    data_dir.mkdir(parents=True, exist_ok=True)

    work_items, skipped_count = _build_work_items(
        utterances, audio_paths, data_dir, shard_size_mb * 1024 * 1024
    )
    if work_items:
        sorted_keys = sorted(item[0] for item in work_items)
        seed = hash(tuple(sorted_keys)) % (2**31)
        random.seed(seed)
        shuffled = work_items.copy()
        random.shuffle(shuffled)
        work_items = shuffled

    embedded_count = 0
    error_count = 0
    last_path: Path | None = None
    shard_count = 0

    executor = None
    try:
        executor = ProcessPoolExecutor(
            max_workers=workers,
            mp_context=_MP_CONTEXT,
            initializer=_init_worker,
        )

        futures = {
            executor.submit(process_single_recording, item): item for item in work_items
        }

        with tqdm(total=len(futures), desc="Recordings", unit="rec") as pbar:
            for _completed, future in enumerate(as_completed(futures), start=1):
                item = futures[future]
                last_path = item[2]
                embedded, errors = _handle_future_new(future, futures)
                embedded_count += embedded
                error_count += errors
                check_oom(initial_oom, last_path)
                pbar.update(1)

        shard_count = len(list(data_dir.glob("train-w*.parquet")))
    except BrokenExecutor as e:
        check_oom(initial_oom, last_path)
        logger.error(
            "ProcessPool crashed (likely OOM). Last: %s. Error: %s", last_path, e
        )
        raise
    finally:
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)
        kill_orphan_workers()
        check_oom(initial_oom, last_path)

    return {
        "embedded": embedded_count,
        "skipped": skipped_count,
        "errors": error_count,
        "shards": shard_count,
    }


def _handle_future_new(future: Any, futures: dict[Any, Any]) -> tuple[int, int]:
    """Handle a completed future, returning (embedded_count, error_count)."""
    try:
        return future.result()
    except BrokenExecutor as e:
        item = futures[future]
        logger.error("Worker crashed processing %s: %s", item[2], e)
        return 0, len(item[1])
    except Exception as e:
        item = futures[future]
        logger.exception("Error processing %s: %s", item[2], e)
        return 0, len(item[1])
