# Edited by Claude, Cursor
"""Processing helpers for simple dataset with parallel audio embedding."""

import gc
import logging
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
    kill_orphan_workers,
    set_pdeathsig,
)

logger = logging.getLogger(__name__)


def group_utterances_by_recording(
    utterances: list[dict[str, Any]],
) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    """Group utterances by recording (term, docket, transcript_type)."""
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for utt in utterances:
        key = (utt["term"], utt["docket"], utt.get("transcript_type", "unknown"))
        grouped[key].append(utt)
    return dict(grouped)


def process_single_recording(
    args: tuple[tuple[str, str, str], list[dict[str, Any]], Path],
) -> tuple[list[dict[str, Any]], int]:
    """Process a single recording (parallel worker). Returns (rows, error_count)."""
    key, rec_utterances, audio_path = args

    try:
        return _process_single_recording_impl(key, rec_utterances, audio_path)
    except Exception as e:
        # Catch ALL exceptions to prevent worker crashes
        logger.exception("Worker crashed processing %s: %s", audio_path, e)
        return [], len(rec_utterances)


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
) -> tuple[list[tuple[tuple[str, str, str], list[dict[str, Any]], Path]], int]:
    """Build work items for parallel processing."""
    grouped = group_utterances_by_recording(utterances)
    work_items = []
    skipped_count = 0
    for key, rec_utterances in grouped.items():
        audio_path = audio_paths.get(key)
        if audio_path is None or not audio_path.exists():
            skipped_count += len(rec_utterances)
            continue
        work_items.append((key, rec_utterances, audio_path))
    return work_items, skipped_count


class _ShardWriter:
    """Encapsulates shard writing state and logic."""

    def __init__(self, data_dir: Path, target_bytes: int, pa: Any, pq: Any) -> None:
        self.data_dir = data_dir
        self.target_bytes = target_bytes
        self.pa = pa
        self.pq = pq
        self.current_shard: list[dict[str, Any]] = []
        self.current_size = 0
        self.shard_num = 0
        self.recs_in_shard = 0

    def add_row(self, row: dict[str, Any]) -> None:
        """Add a row to the current shard."""
        self.current_shard.append(row)
        self.current_size += len(row["audio"]["bytes"])

    def maybe_flush(self) -> None:
        """Flush shard if size or recording count threshold reached."""
        self.recs_in_shard += 1
        if self.current_size >= self.target_bytes or self.recs_in_shard >= 5:
            self.flush()

    def flush(self) -> None:
        """Write current shard to disk and reset state."""
        if self.current_shard:
            self.pq.write_table(
                self.pa.Table.from_pylist(self.current_shard),
                self.data_dir / f"train-{self.shard_num:05d}.parquet",
            )
            self.shard_num += 1
            self.current_shard = []
            self.current_size = 0
            self.recs_in_shard = 0
            gc.collect()


def process_by_recording(
    utterances: list[dict[str, Any]],
    audio_paths: dict[tuple[str, str, str], Path],
    output_dir: Path,
    shard_size_mb: int,
    pa: Any,
    pq: Any,
    workers: int = 1,
) -> dict[str, int]:
    """Process utterances grouped by recording for efficiency."""
    kill_orphan_workers()

    initial_oom = get_oom_kill_count()
    used_mb, available_mb, _ = get_memory_usage_mb()
    logger.info(
        "Starting processing: %d MB used, %d MB available, %d workers",
        used_mb,
        available_mb,
        workers,
    )

    data_dir = output_dir / "data" / "utterances"
    data_dir.mkdir(parents=True, exist_ok=True)

    work_items, skipped_count = _build_work_items(utterances, audio_paths)
    writer = _ShardWriter(data_dir, shard_size_mb * 1024 * 1024, pa, pq)

    embedded_count = 0
    error_count = 0
    last_path: Path | None = None

    executor = None
    try:
        executor = ProcessPoolExecutor(max_workers=workers, initializer=set_pdeathsig)
        futures = {
            executor.submit(process_single_recording, item): item for item in work_items
        }
        with tqdm(total=len(futures), desc="Recordings", unit="rec") as pbar:
            for future in as_completed(futures):
                item = futures[future]
                last_path = item[2]
                rows, errors = _handle_future(future, futures)
                if rows is None:
                    error_count += errors
                    check_oom(initial_oom, last_path)
                    pbar.update(1)
                    continue

                error_count += errors
                for row in rows:
                    writer.add_row(row)
                    embedded_count += 1

                writer.maybe_flush()
                del rows
                gc.collect()
                pbar.update(1)

        writer.flush()
    except BrokenExecutor as e:
        check_oom(initial_oom, last_path)
        logger.error(
            "ProcessPool crashed (likely OOM). Last: %s. Error: %s", last_path, e
        )
        raise
    finally:
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)
        check_oom(initial_oom, last_path)

    return {
        "embedded": embedded_count,
        "skipped": skipped_count,
        "errors": error_count,
        "shards": writer.shard_num,
    }


def _handle_future(
    future: Any, futures: dict[Any, Any]
) -> tuple[list[dict[str, Any]] | None, int]:
    """Handle a completed future, returning (rows, errors) or (None, count)."""
    try:
        return future.result()
    except BrokenExecutor as e:
        item = futures[future]
        logger.error("Worker crashed processing %s: %s", item[2], e)
        return None, len(item[1])
    except Exception as e:
        item = futures[future]
        logger.exception("Error processing %s: %s", item[2], e)
        return None, len(item[1])
