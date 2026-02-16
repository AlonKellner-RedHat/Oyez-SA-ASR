# Edited by Cursor: split from test_cache (lintok; plan).
"""FileCache edge cases: raw path resolution, set/delete/clear exceptions."""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from oyez_sa_asr.scraper import CacheMeta, ContentVersion, FileCache, RequestMetadata
from oyez_sa_asr.scraper.models import FetchResult


class TestFileCacheAdvanced:
    """FileCache edge cases and invalidation behavior."""

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

            latest_raw = raw_dir / "latest.json"
            latest_raw.write_bytes(b'{"latest": true}')
            meta = CacheMeta(
                url=request.url,
                fetched_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                status_code=200,
                raw_path="",
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
            assert result is not None

    def test_get_uses_meta_raw_path_when_no_latest(self) -> None:
        """Should use meta.raw_path when no latest version (line 93)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/test")
            meta_path = cache._get_meta_path(request)
            raw_dir = cache._get_domain_dir(request.url) / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)

            old_raw = raw_dir / "old.json"
            old_raw.write_bytes(b'{"old": true}')
            meta = CacheMeta(
                url=request.url,
                fetched_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                status_code=200,
                raw_path="raw/old.json",
            )
            meta_path.write_text(json.dumps(meta.to_dict()))

            result = cache.get(request)
            assert result is not None

    def test_get_uses_raw_path_fallback(self) -> None:
        """Should use _get_raw_path when no latest and no meta.raw_path (line 95)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/test")
            meta_path = cache._get_meta_path(request)
            raw_dir = cache._get_domain_dir(request.url) / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)

            meta = CacheMeta(
                url=request.url,
                fetched_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                status_code=200,
                raw_path="",
                content_type="application/json",
            )
            meta_path.write_text(json.dumps(meta.to_dict()))

            result = cache.get(request)
            assert result is None

    def test_get_handles_missing_raw_path(self) -> None:
        """Should handle missing raw_path in cache entry (lines 92-95, 97)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/test")
            meta_path = cache._get_meta_path(request)
            meta_path.parent.mkdir(parents=True, exist_ok=True)

            meta = CacheMeta(
                url=request.url,
                fetched_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                status_code=200,
                raw_path="",
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
                data=None,
                raw_data=None,
            )
            cache.set(request, result)
            assert cache.get(request) is None

    def test_set_handles_corrupted_meta_on_read(self) -> None:
        """Should handle corrupted meta file when reading (lines 122-123)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/test")
            meta_path = cache._get_meta_path(request)
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            meta_path.write_text("{ invalid json }")

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

    def test_delete_handles_exceptions(self) -> None:
        """Should handle exceptions when deleting (lines 176-177)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/test")
            meta_path = cache._get_meta_path(request)
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            meta_path.write_text("{ invalid json }")

            result = cache.delete(request)
            assert result is True
            assert not meta_path.exists()

    def test_clear_expired_skips_non_directories(self) -> None:
        """Should skip non-directory entries (line 186)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            (cache.cache_dir / "not_a_dir.txt").write_text("test")

            cleared = cache.clear_expired()
            assert cleared == 0

    def test_clear_expired_handles_missing_meta_dir(self) -> None:
        """Should handle missing meta directory (line 189)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            domain_dir = cache.cache_dir / "example.com"
            domain_dir.mkdir(parents=True)

            cleared = cache.clear_expired()
            assert cleared == 0

    def test_clear_expired_handles_exceptions(self) -> None:
        """Should handle exceptions when clearing expired (lines 199-201)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            domain_dir = cache.cache_dir / "example.com"
            meta_dir = domain_dir / "meta"
            meta_dir.mkdir(parents=True)

            (meta_dir / "invalid.json").write_text("{ invalid json }")

            cleared = cache.clear_expired()
            assert cleared == 1
            assert not (meta_dir / "invalid.json").exists()
