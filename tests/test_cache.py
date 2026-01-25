# Edited by Claude
"""Unit tests for FileCache."""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from oyez_sa_asr.scraper import CacheMeta, ContentVersion, FileCache, RequestMetadata
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

    def test_get_uses_latest_version_raw_path(self) -> None:
        """Should use latest version raw_path when available (lines 92-95)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/test")
            meta_path = cache._get_meta_path(request)
            raw_dir = cache._get_domain_dir(request.url) / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)

            # Create meta with latest version
            latest_raw = raw_dir / "latest.json"
            latest_raw.write_bytes(b'{"latest": true}')
            meta = CacheMeta(
                url=request.url,
                fetched_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                status_code=200,
                raw_path="",  # Empty, should use latest version
            )
            meta.versions.append(
                ContentVersion(
                    content_hash="abc123",
                    first_seen=datetime.now(timezone.utc),
                    last_seen=datetime.now(timezone.utc),
                    raw_path="raw/latest.json",
                )
            )
            meta_path.write_text(json.dumps(meta.to_dict()))

            result = cache.get(request)
            # Should use latest version raw_path
            assert result is not None

    def test_get_uses_meta_raw_path_when_no_latest(self) -> None:
        """Should use meta.raw_path when no latest version (line 93)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/test")
            meta_path = cache._get_meta_path(request)
            raw_dir = cache._get_domain_dir(request.url) / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)

            # Create meta with raw_path but no versions
            old_raw = raw_dir / "old.json"
            old_raw.write_bytes(b'{"old": true}')
            meta = CacheMeta(
                url=request.url,
                fetched_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                status_code=200,
                raw_path="raw/old.json",  # Use this when no latest
            )
            meta_path.write_text(json.dumps(meta.to_dict()))

            result = cache.get(request)
            # Should use meta.raw_path
            assert result is not None

    def test_get_uses_raw_path_fallback(self) -> None:
        """Should use _get_raw_path when no latest version and no meta.raw_path (line 95)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/test")
            meta_path = cache._get_meta_path(request)
            raw_dir = cache._get_domain_dir(request.url) / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)

            # Create meta with no versions and no raw_path
            meta = CacheMeta(
                url=request.url,
                fetched_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                status_code=200,
                raw_path="",  # Empty
                content_type="application/json",
            )
            # No versions
            meta_path.write_text(json.dumps(meta.to_dict()))

            # Should use _get_raw_path fallback (line 95)
            result = cache.get(request)
            # Should return None since the generated path doesn't exist
            assert result is None

    def test_get_handles_missing_raw_path(self) -> None:
        """Should handle missing raw_path in cache entry (lines 92-95, 97)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/test")
            meta_path = cache._get_meta_path(request)
            meta_path.parent.mkdir(parents=True, exist_ok=True)

            # Create meta file with latest version but missing raw_path
            meta = CacheMeta(
                url=request.url,
                fetched_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                status_code=200,
                raw_path="",  # Empty raw_path
            )
            meta.versions.append(
                ContentVersion(
                    content_hash="abc123",
                    first_seen=datetime.now(timezone.utc),
                    last_seen=datetime.now(timezone.utc),
                    raw_path="raw/test.json",
                )
            )
            meta_path.write_text(json.dumps(meta.to_dict()))

            # Should return None when raw_path doesn't exist
            result = cache.get(request)
            assert result is None

    def test_set_handles_no_raw_data(self) -> None:
        """Should return early when no raw_data (line 112)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/test")
            result = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                data=None,  # No data
                raw_data=None,  # No raw_data
            )
            cache.set(request, result)
            # Should not create cache entry
            assert cache.get(request) is None

    def test_set_handles_corrupted_meta_on_read(self) -> None:
        """Should handle corrupted meta file when reading (lines 122-123)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/test")
            meta_path = cache._get_meta_path(request)
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            # Create corrupted meta file
            meta_path.write_text("{ invalid json }")

            result = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                raw_data=b'{"test": true}',
                content_type="application/json",
            )
            # Should handle exception and create new meta
            cache.set(request, result)
            retrieved = cache.get(request)
            assert retrieved is not None

    def test_delete_handles_exceptions(self) -> None:
        """Should handle exceptions when deleting (lines 176-177)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/test")
            meta_path = cache._get_meta_path(request)
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            # Create corrupted meta file
            meta_path.write_text("{ invalid json }")

            # Should handle exception gracefully
            result = cache.delete(request)
            assert result is True
            assert not meta_path.exists()

    def test_clear_expired_skips_non_directories(self) -> None:
        """Should skip non-directory entries (line 186)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            # Create a file (not a directory) in cache_dir
            (cache.cache_dir / "not_a_dir.txt").write_text("test")

            cleared = cache.clear_expired()
            # Should handle gracefully
            assert cleared == 0

    def test_clear_expired_handles_missing_meta_dir(self) -> None:
        """Should handle missing meta directory (line 189)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            # Create domain directory but no meta subdirectory
            domain_dir = cache.cache_dir / "example.com"
            domain_dir.mkdir(parents=True)

            cleared = cache.clear_expired()
            # Should handle gracefully
            assert cleared == 0

    def test_clear_expired_handles_exceptions(self) -> None:
        """Should handle exceptions when clearing expired (lines 199-201)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            domain_dir = cache.cache_dir / "example.com"
            meta_dir = domain_dir / "meta"
            meta_dir.mkdir(parents=True)

            # Create invalid JSON meta file
            (meta_dir / "invalid.json").write_text("{ invalid json }")

            cleared = cache.clear_expired()
            # Should handle exception and delete corrupted file
            assert cleared == 1
            assert not (meta_dir / "invalid.json").exists()
