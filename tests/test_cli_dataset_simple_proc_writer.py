# Edited by Cursor: split from test_cli_dataset_simple_proc (lintok; plan).
"""Tests for _WorkerShardWriter and _ShardWriter."""

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from oyez_sa_asr.cli_dataset_simple_proc import _ShardWriter, _WorkerShardWriter


class TestWorkerShardWriter:
    """Tests for _WorkerShardWriter class."""

    def test_add_row_increases_size(self, tmp_path: Path) -> None:
        """Should track size when adding rows."""
        writer = _WorkerShardWriter(
            tmp_path, target_bytes=1000, pa=pa, pq=pq, worker_id=1
        )

        row = {"audio": {"bytes": b"test" * 100}}
        writer.add_row(row)

        assert len(writer.current_shard) == 1
        assert writer.current_size > 0

    def test_maybe_flush_with_force(self, tmp_path: Path) -> None:
        """Should flush when force=True."""
        writer = _WorkerShardWriter(
            tmp_path, target_bytes=1000, pa=pa, pq=pq, worker_id=1
        )

        row = {"audio": {"bytes": b"test"}}
        writer.add_row(row)
        writer.maybe_flush(force=True)

        shard_files = list(tmp_path.glob("train-w*.parquet"))
        assert len(shard_files) == 1
        assert writer.current_shard == []

    def test_maybe_flush_after_recording_threshold(self, tmp_path: Path) -> None:
        """Should flush after 1 recording (aggressive threshold)."""
        writer = _WorkerShardWriter(
            tmp_path, target_bytes=1000000, pa=pa, pq=pq, worker_id=1
        )

        row = {"audio": {"bytes": b"test"}}
        writer.add_row(row)
        writer.maybe_flush()

        shard_files = list(tmp_path.glob("train-w*.parquet"))
        assert len(shard_files) == 1

    def test_ensure_flushed_with_data(self, tmp_path: Path) -> None:
        """Should flush remaining data when ensure_flushed is called."""
        writer = _WorkerShardWriter(
            tmp_path, target_bytes=1000, pa=pa, pq=pq, worker_id=1
        )

        row = {"audio": {"bytes": b"test"}}
        writer.add_row(row)
        writer.ensure_flushed()

        shard_files = list(tmp_path.glob("train-w*.parquet"))
        assert len(shard_files) == 1

    def test_ensure_flushed_without_data(self, tmp_path: Path) -> None:
        """Should not create file when ensure_flushed called with no data."""
        writer = _WorkerShardWriter(
            tmp_path, target_bytes=1000, pa=pa, pq=pq, worker_id=1
        )

        writer.ensure_flushed()

        shard_files = list(tmp_path.glob("train-w*.parquet"))
        assert len(shard_files) == 0

    def test_flush_with_empty_shard(self, tmp_path: Path) -> None:
        """Should not write file when flushing empty shard."""
        writer = _WorkerShardWriter(
            tmp_path, target_bytes=1000, pa=pa, pq=pq, worker_id=1
        )

        writer.flush()

        shard_files = list(tmp_path.glob("train-w*.parquet"))
        assert len(shard_files) == 0

    def test_final_flush(self, tmp_path: Path) -> None:
        """Should flush remaining data on final_flush."""
        writer = _WorkerShardWriter(
            tmp_path, target_bytes=1000, pa=pa, pq=pq, worker_id=1
        )

        row = {"audio": {"bytes": b"test"}}
        writer.add_row(row)
        writer.final_flush()

        shard_files = list(tmp_path.glob("train-w*.parquet"))
        assert len(shard_files) == 1

    def test_final_flush_without_data(self, tmp_path: Path) -> None:
        """Should handle final_flush with no data."""
        writer = _WorkerShardWriter(
            tmp_path, target_bytes=1000, pa=pa, pq=pq, worker_id=1
        )

        writer.final_flush()

        shard_files = list(tmp_path.glob("train-w*.parquet"))
        assert len(shard_files) == 0


class TestShardWriter:
    """Tests for _ShardWriter class (compatibility/no-op methods)."""

    def test_add_row_is_noop(self, tmp_path: Path) -> None:
        """Should be a no-op."""
        writer = _ShardWriter(tmp_path, target_bytes=1000, pa=pa, pq=pq)
        writer.add_row({"test": "data"})

    def test_maybe_flush_is_noop(self, tmp_path: Path) -> None:
        """Should be a no-op."""
        writer = _ShardWriter(tmp_path, target_bytes=1000, pa=pa, pq=pq)
        writer.maybe_flush()
        writer.maybe_flush(force=True)

    def test_flush_is_noop(self, tmp_path: Path) -> None:
        """Should be a no-op."""
        writer = _ShardWriter(tmp_path, target_bytes=1000, pa=pa, pq=pq)
        writer.flush()
