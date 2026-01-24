# Edited by Claude, Cursor
"""Processing helpers for simple dataset with parallel audio embedding."""

import gc
import logging
import multiprocessing as mp
import os
import random
from collections import defaultdict
from concurrent.futures import BrokenExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from tqdm import tqdm

from .audio_segment import extract_segments_batch
from .memory_utils import (
    check_oom,
    get_memory_usage_mb,
    get_oom_kill_count,
    get_swap_usage_mb,
    kill_orphan_workers,
    set_pdeathsig,
)

logger = logging.getLogger(__name__)

# Use spawn context to avoid issues with forking multithreaded programs
# and ensure proper PR_SET_PDEATHSIG behavior (workers die when main dies).
# Falls back to default context if spawn is unavailable.
try:
    _MP_CONTEXT = mp.get_context("spawn")
except ValueError:
    _MP_CONTEXT = None  # Will use default context

# Global worker state for per-worker shard writing
# Edited by Claude: Workers write shards directly to disk to reduce memory usage
_worker_state: dict[str, Any] = {}


def group_utterances_by_recording(
    utterances: list[dict[str, Any]],
) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    """Group utterances by recording (term, docket, transcript_type)."""
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for utt in utterances:
        key = (utt["term"], utt["docket"], utt.get("transcript_type", "unknown"))
        grouped[key].append(utt)
    return dict(grouped)


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

    # Import PyArrow in worker (not serializable across process boundaries)
    # PLC0415: Import must be here, not at module level, because it's in worker process
    from oyez_sa_asr.cli_dataset_simple_core import require_pyarrow  # noqa: PLC0415

    pa, pq = require_pyarrow()

    # Get or create worker-specific shard writer
    worker_id = os.getpid() % 1000  # Use PID mod 1000 as unique worker ID
    writer_key = f"writer_{worker_id}"

    if writer_key not in _worker_state:
        _worker_state[writer_key] = _WorkerShardWriter(
            data_dir, target_bytes, pa, pq, worker_id
        )

    writer = _worker_state[writer_key]

    try:
        rows, errors = _process_single_recording_impl(key, rec_utterances, audio_path)
        if rows:
            # Write rows directly to shard in this worker
            for row in rows:
                writer.add_row(row)
            # Flush if threshold reached
            writer.maybe_flush()
        return len(rows), errors
    except Exception as e:
        # Catch ALL exceptions to prevent worker crashes
        logger.exception("Worker crashed processing %s: %s", audio_path, e)
        return 0, len(rec_utterances)


def _process_single_recording_impl(
    key: tuple[str, str, str],
    rec_utterances: list[dict[str, Any]],
    audio_path: Path,
) -> tuple[list[dict[str, Any]], int]:
    """Process a single recording (implementation)."""
    # Filter out utterances with missing or invalid time ranges
    valid_utterances = []
    segments = []
    for utt in rec_utterances:
        start = utt.get("start_sec")
        end = utt.get("end_sec")
        if start is None or end is None or start >= end:
            continue  # Skip invalid utterances
        valid_utterances.append(utt)
        segments.append((start, end))

    if not segments:
        return [], 0

    rec_utterances = valid_utterances

    try:
        segment_bytes_list = extract_segments_batch(audio_path, segments)
    except (OSError, ValueError) as e:
        logger.warning("Failed to process %s: %s", audio_path, e)
        return [], len(rec_utterances)

    rows = []
    for utt, audio_bytes in zip(rec_utterances, segment_bytes_list, strict=True):
        term = utt.get("term", key[0])
        docket = utt.get("docket", key[1])
        start_sec = utt.get("start_sec", 0)
        end_sec = utt.get("end_sec", 0)
        segment_name = f"{term}_{docket}_{start_sec:.2f}.flac"
        # HuggingFace-aligned schema (Edited by Claude, Cursor)
        row = {
            "id": f"{term}_{docket}_{start_sec:.2f}",
            "audio": {"bytes": audio_bytes, "path": segment_name},
            "sentence": utt.get("text", ""),
            "speaker": utt.get("speaker_name"),
            "duration": (end_sec - start_sec)
            if end_sec is not None and start_sec is not None
            else 0.0,
            "term": term,
            "docket": docket,
            "start_sec": start_sec,
            "end_sec": end_sec,
        }
        rows.append(row)

    return rows, 0


def _build_work_items(
    utterances: list[dict[str, Any]],
    audio_paths: dict[tuple[str, str, str], Path],
    data_dir: Path,
    target_bytes: int,
) -> tuple[
    list[tuple[tuple[str, str, str], list[dict[str, Any]], Path, Path, int]], int
]:
    """Build work items for parallel processing.

    Edited by Claude: Include shard writer params in work items for worker-side writing.
    PyArrow is imported in workers to avoid serialization issues.
    """
    grouped = group_utterances_by_recording(utterances)
    work_items = []
    skipped_count = 0
    for key, rec_utterances in grouped.items():
        audio_path = audio_paths.get(key)
        if audio_path is None or not audio_path.exists():
            skipped_count += len(rec_utterances)
            continue
        work_items.append((key, rec_utterances, audio_path, data_dir, target_bytes))
    return work_items, skipped_count


class _WorkerShardWriter:
    """Per-worker shard writer that writes directly to disk.

    Edited by Claude: Each worker writes its own shards to reduce memory pressure.
    Uses worker_id in filename to avoid conflicts.
    """

    def __init__(
        self, data_dir: Path, target_bytes: int, pa: Any, pq: Any, worker_id: int
    ) -> None:
        self.data_dir = data_dir
        self.target_bytes = target_bytes
        self.pa = pa
        self.pq = pq
        self.worker_id = worker_id
        self.current_shard: list[dict[str, Any]] = []
        self.current_size = 0
        self.shard_num = 0
        self.recs_in_shard = 0

    def add_row(self, row: dict[str, Any]) -> None:
        """Add a row to the current shard."""
        self.current_shard.append(row)
        self.current_size += len(row["audio"]["bytes"])

    def maybe_flush(self, force: bool = False) -> None:
        """Flush shard if size or recording count threshold reached.

        Edited by Claude: Flush aggressively to reduce memory usage.
        Always flush if force=True or after 1 recording (for immediate disk writes).
        """
        self.recs_in_shard += 1
        # Flush if: forced, size threshold, or after 1 recording (aggressive for memory reduction)
        if force or self.current_size >= self.target_bytes or self.recs_in_shard >= 1:
            self.flush()

    def ensure_flushed(self) -> None:
        """Ensure any remaining data is flushed. Edited by Claude."""
        if self.current_shard:
            self.flush()

    def flush(self) -> None:
        """Write current shard to disk and reset state."""
        if self.current_shard:
            # Use worker_id in filename to avoid conflicts
            shard_name = f"train-w{self.worker_id:02d}-{self.shard_num:05d}.parquet"
            self.pq.write_table(
                self.pa.Table.from_pylist(self.current_shard),
                self.data_dir / shard_name,
            )
            self.shard_num += 1
            self.current_shard = []
            self.current_size = 0
            self.recs_in_shard = 0
            gc.collect()

    def final_flush(self) -> None:
        """Flush any remaining data. Called at worker shutdown."""
        if self.current_shard:
            self.flush()


class _ShardWriter:
    """Main process shard writer (kept for compatibility, but not used in new flow)."""

    def __init__(self, data_dir: Path, target_bytes: int, pa: Any, pq: Any) -> None:
        self.data_dir = data_dir
        self.target_bytes = target_bytes
        self.pa = pa
        self.pq = pq
        self.shard_num = 0

    def add_row(self, row: dict[str, Any]) -> None:
        """No-op in new flow (workers write directly)."""
        pass

    def maybe_flush(self, force: bool = False) -> None:
        """No-op in new flow (workers write directly)."""
        pass

    def flush(self) -> None:
        """No-op in new flow (workers write directly)."""
        pass


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
    # Deterministic shuffle: same recordings = same order
    # Edited by Claude: Use hash of sorted keys for reproducible randomization
    if work_items:
        # Create deterministic seed from sorted recording keys
        sorted_keys = sorted(item[0] for item in work_items)
        seed = hash(tuple(sorted_keys)) % (2**31)  # Limit to 32-bit signed int
        random.seed(seed)
        shuffled = work_items.copy()
        random.shuffle(shuffled)
        work_items = shuffled

    embedded_count = 0
    error_count = 0
    last_path: Path | None = None

    executor = None
    try:
        # Edited by Claude: Each worker writes shards directly to disk
        executor = ProcessPoolExecutor(
            max_workers=workers,
            mp_context=_MP_CONTEXT,
            initializer=_init_worker,
        )

        # Submit all work items - workers write directly to disk
        futures = {
            executor.submit(process_single_recording, item): item for item in work_items
        }

        # Track progress - workers write shards independently
        with tqdm(total=len(futures), desc="Recordings", unit="rec") as pbar:
            for _completed, future in enumerate(as_completed(futures), start=1):
                item = futures[future]
                last_path = item[2]
                embedded, errors = _handle_future_new(future, futures)
                embedded_count += embedded
                error_count += errors
                check_oom(initial_oom, last_path)
                pbar.update(1)

                # Workers flush based on their own thresholds
                # Edited by Claude: Workers write shards independently

        # Count shards written by workers
        # Note: Workers flush when thresholds are met (size or 3 recordings)
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
        # Explicit cleanup of orphan workers (including resource_tracker)
        # Edited by Claude: Ensure cleanup even after OOM kills
        kill_orphan_workers()
        check_oom(initial_oom, last_path)

    return {
        "embedded": embedded_count,
        "skipped": skipped_count,
        "errors": error_count,
        "shards": shard_count,
    }


def _handle_future_new(future: Any, futures: dict[Any, Any]) -> tuple[int, int]:
    """Handle a completed future, returning (embedded_count, error_count).

    Edited by Claude: Workers now write shards directly, so we just track counts.
    """
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
