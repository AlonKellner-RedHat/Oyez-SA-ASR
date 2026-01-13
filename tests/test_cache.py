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
        """Should store and retrieve entries with versions."""
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
            meta_path = cache._get_meta_path(request)
            assert meta_path.exists()
            with meta_path.open() as f:
                meta_data = json.load(f)
            assert len(meta_data["versions"]) == 1
            retrieved = cache.get(request)
            assert retrieved is not None
            assert retrieved.response == b'{"key": "value"}'

    def test_versioned_entries_never_expire(self) -> None:
        """Versioned entries are kept indefinitely."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir), ttl_days=0)
            request = RequestMetadata(url="https://example.com/test")
            result = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                raw_data=b'{"test": true}',
                content_type="application/json",
            )
            cache.set(request, result)
            retrieved = cache.get(request)
            assert retrieved is not None
            assert retrieved.response == b'{"test": true}'

    def test_failed_requests_stored_separately(self) -> None:
        """Failed requests should be stored in the failed directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/error")
            result = FetchResult(url=request.url, success=False, error="Conn failed")
            cache.set(request, result)
            assert cache.get(request) is None
            assert cache._get_failed_path(request).exists()

    def test_delete_entry(self) -> None:
        """Should delete meta file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/delete")
            result = FetchResult(
                url=request.url, success=True, status_code=200, raw_data=b"{}"
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
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            meta_path.write_text("not valid json")
            assert cache.get(request) is None
            assert not meta_path.exists()

    def test_clear_expired(self) -> None:
        """Should clear expired entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request1 = RequestMetadata(url="https://example.com/expired")
            raw_rel = f"raw/{request1.cache_key()}.json"
            meta1 = CacheMeta(
                url=request1.url,
                fetched_at=datetime.now(timezone.utc) - timedelta(days=60),
                expires_at=datetime.now(timezone.utc) - timedelta(days=30),
                status_code=200,
                raw_path=raw_rel,
            )
            meta_path1 = cache._get_meta_path(request1)
            raw_path1 = cache._get_raw_path(request1, "application/json")
            meta_path1.parent.mkdir(parents=True, exist_ok=True)
            raw_path1.parent.mkdir(parents=True, exist_ok=True)
            meta_path1.write_text(json.dumps(meta1.to_dict()))
            raw_path1.write_bytes(b"{}")
            request2 = RequestMetadata(url="https://example.com/valid")
            result2 = FetchResult(
                url=request2.url, success=True, status_code=200, raw_data=b"{}"
            )
            cache.set(request2, result2)
            cleared = cache.clear_expired()
            assert cleared == 1
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
                raw_data=b"<html></html>",
                content_type="text/html; charset=utf-8",
            )
            cache.set(request, result)
            meta_path = cache._get_meta_path(request)
            with meta_path.open() as f:
                meta_data = json.load(f)
            assert meta_data["versions"][0]["raw_path"].endswith(".html")
