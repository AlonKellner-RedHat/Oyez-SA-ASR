# Edited by Cursor: split from cli_dataset_simple_proc (lintok; plan).
"""Implementation: group_utterances, _process_single_recording_impl, writers, _build_work_items."""

import gc
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from .audio_segment import extract_segments_batch

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


def _process_single_recording_impl(
    key: tuple[str, str, str],
    rec_utterances: list[dict[str, Any]],
    audio_path: Path,
) -> tuple[list[dict[str, Any]], int]:
    """Process a single recording (implementation)."""
    valid_utterances = []
    segments = []
    for utt in rec_utterances:
        start = utt.get("start_sec")
        end = utt.get("end_sec")
        if start is None or end is None or start >= end:
            continue
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
        recording_type = utt.get(
            "transcript_type", key[2] if len(key) > 2 else "unknown"
        )
        # Validated above: only utterances with start_sec/end_sec are in rec_utterances.
        start_sec = utt["start_sec"]
        end_sec = utt["end_sec"]
        segment_name = f"{term}_{docket}_{recording_type}_{start_sec:.2f}.flac"
        row = {
            "id": f"{term}_{docket}_{recording_type}_{start_sec:.2f}",
            "audio": {"bytes": audio_bytes, "path": segment_name},
            "sentence": utt.get("text", ""),
            "speaker": utt.get("speaker_name"),
            "speaker_id": utt.get("speaker_id"),
            "is_justice": utt.get("is_justice", False),
            "duration": end_sec - start_sec,
            "term": term,
            "docket": docket,
            "recording_type": recording_type,
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
    """Build work items for parallel processing."""
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
    """Per-worker shard writer that writes directly to disk."""

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
        """Flush shard if size or recording count threshold reached."""
        self.recs_in_shard += 1
        if force or self.current_size >= self.target_bytes or self.recs_in_shard >= 1:
            self.flush()

    def ensure_flushed(self) -> None:
        """Ensure any remaining data is flushed."""
        if self.current_shard:
            self.flush()

    def flush(self) -> None:
        """Write current shard to disk and reset state."""
        if self.current_shard:
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
