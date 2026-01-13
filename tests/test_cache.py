# Edited by Claude
"""Unit tests for FileCache."""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from oyez_sa_asr.scraper import CacheMeta, FileCache, RequestMetadata
from oyez_sa_asr.scraper.models import FetchResult


class TestFileCache:
    """Tests for FileCache."""

    def test_get_returns_none_for_missing(self) -> None:
        """Get should return None for missing entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/missing")
            assert cache.get(request) is None

    def test_set_and_get(self) -> None:
        """Should store and retrieve entries with correct file extensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/test")
            result = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                data={"key": "value"},
                raw_data=b'{"key": "value"}',
                content_type="application/json",
            )
            cache.set(request, result)

            # Verify files exist with correct extension
            meta_path = cache._get_meta_path(request)
            raw_path = cache._get_raw_path(request, "application/json")
            assert meta_path.exists()
            assert raw_path.exists()
            assert raw_path.suffix == ".json"

            # Verify metadata contains raw_path
            with meta_path.open() as f:
                meta_data = json.load(f)
            assert "raw_path" in meta_data
            assert meta_data["raw_path"].endswith(".json")

            # Verify retrieval
            retrieved = cache.get(request)
            assert retrieved is not None
            assert retrieved.url == request.url
            assert retrieved.response == b'{"key": "value"}'

    def test_expired_entry_returns_none(self) -> None:
        """Expired entries should return None and be deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir), ttl_days=0)
            request = RequestMetadata(url="https://example.com/test")

            # Manually create expired meta and raw files with raw_path
            raw_rel_path = f"raw/{request.cache_key()}.json"
            meta = CacheMeta(
                url=request.url,
                fetched_at=datetime.now(timezone.utc) - timedelta(days=2),
                expires_at=datetime.now(timezone.utc) - timedelta(days=1),
                status_code=200,
                raw_path=raw_rel_path,
            )
            meta_path = cache._get_meta_path(request)
            raw_path = cache._get_raw_path(request, "application/json")
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            with meta_path.open("w") as f:
                json.dump(meta.to_dict(), f)
            raw_path.write_bytes(b"{}")

            # Should return None and delete both files
            assert cache.get(request) is None
            assert not meta_path.exists()
            assert not raw_path.exists()

    def test_failed_requests_stored_separately(self) -> None:
        """Failed requests should be stored in the failed directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/error")
            result = FetchResult(url=request.url, success=False, error="Conn failed")
            cache.set(request, result)

            assert cache.get(request) is None
            failed_path = cache._get_failed_path(request)
            assert failed_path.exists()

    def test_delete_entry(self) -> None:
        """Should delete both meta and raw files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/delete")
            result = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                data={},
                raw_data=b"{}",
            )
            cache.set(request, result)
            assert cache.get(request) is not None
            assert cache.delete(request) is True
            assert cache.get(request) is None
            assert cache.delete(request) is False

    def test_corrupted_meta_file_handled(self) -> None:
        """Corrupted meta files should be deleted and return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/corrupted")
            meta_path = cache._get_meta_path(request)
            raw_path = cache._get_raw_path(request, "application/json")
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            with meta_path.open("w") as f:
                f.write("not valid json")
            raw_path.write_bytes(b"{}")

            assert cache.get(request) is None
            assert not meta_path.exists()

    def test_clear_expired(self) -> None:
        """Should clear expired entries from meta and raw directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))

            # Create an expired entry with raw_path
            request1 = RequestMetadata(url="https://example.com/expired")
            raw_rel_path = f"raw/{request1.cache_key()}.json"
            meta1 = CacheMeta(
                url=request1.url,
                fetched_at=datetime.now(timezone.utc) - timedelta(days=60),
                expires_at=datetime.now(timezone.utc) - timedelta(days=30),
                status_code=200,
                raw_path=raw_rel_path,
            )
            meta_path1 = cache._get_meta_path(request1)
            raw_path1 = cache._get_raw_path(request1, "application/json")
            meta_path1.parent.mkdir(parents=True, exist_ok=True)
            raw_path1.parent.mkdir(parents=True, exist_ok=True)
            with meta_path1.open("w") as f:
                json.dump(meta1.to_dict(), f)
            raw_path1.write_bytes(b"{}")

            # Create a valid entry
            request2 = RequestMetadata(url="https://example.com/valid")
            result2 = FetchResult(
                url=request2.url, success=True, status_code=200, data={}, raw_data=b"{}"
            )
            cache.set(request2, result2)

            cleared = cache.clear_expired()
            assert cleared == 1
            assert not meta_path1.exists()
            assert not raw_path1.exists()
            assert cache.get(request2) is not None

    def test_html_content_type_uses_html_extension(self) -> None:
        """Should use .html extension for HTML content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/page")
            result = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                data=None,
                raw_data=b"<html></html>",
                content_type="text/html; charset=utf-8",
            )
            cache.set(request, result)

            raw_path = cache._get_raw_path(request, "text/html")
            assert raw_path.suffix == ".html"
            assert raw_path.exists()
