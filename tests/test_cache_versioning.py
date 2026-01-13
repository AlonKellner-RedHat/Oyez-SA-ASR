# Edited by Claude
"""Unit tests for FileCache content versioning."""

import json
import tempfile
from pathlib import Path

from oyez_sa_asr.scraper import FileCache, RequestMetadata
from oyez_sa_asr.scraper.models import FetchResult


class TestFileCacheVersioning:
    """Tests for FileCache content versioning."""

    def test_set_creates_version_with_content_hash(self) -> None:
        """set() should create a version entry with content hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/versioned")
            result = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                data={"v": 1},
                raw_data=b'{"v": 1}',
                content_type="application/json",
            )
            cache.set(request, result)
            meta_path = cache._get_meta_path(request)
            with meta_path.open() as f:
                data = json.load(f)
            assert "versions" in data
            assert len(data["versions"]) == 1
            assert len(data["versions"][0]["content_hash"]) > 0

    def test_same_content_updates_last_seen(self) -> None:
        """Same content should update last_seen, not add new version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/same")
            result = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                data={"same": True},
                raw_data=b'{"same": true}',
                content_type="application/json",
            )
            cache.set(request, result)
            cache.set(request, result)
            meta_path = cache._get_meta_path(request)
            with meta_path.open() as f:
                data = json.load(f)
            assert len(data["versions"]) == 1

    def test_different_content_adds_new_version(self) -> None:
        """Different content should add a new version, keeping old ones."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/changing")
            r1 = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                raw_data=b'{"version": 1}',
                content_type="application/json",
            )
            r2 = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                raw_data=b'{"version": 2}',
                content_type="application/json",
            )
            cache.set(request, r1)
            cache.set(request, r2)
            meta_path = cache._get_meta_path(request)
            with meta_path.open() as f:
                data = json.load(f)
            assert len(data["versions"]) == 2
            raw_dir = cache._get_raw_dir(request.url)
            assert len(list(raw_dir.glob("*.json"))) == 2

    def test_get_returns_latest_version(self) -> None:
        """get() should return the content of the latest version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/latest")
            r1 = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                raw_data=b'{"v": "old"}',
                content_type="application/json",
            )
            r2 = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                raw_data=b'{"v": "new"}',
                content_type="application/json",
            )
            cache.set(request, r1)
            cache.set(request, r2)
            entry = cache.get(request)
            assert entry is not None
            assert entry.response == b'{"v": "new"}'

    def test_change_logged_to_file(self) -> None:
        """Content changes should be logged to changes.log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/logged")
            r1 = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                raw_data=b'{"logged": 1}',
                content_type="application/json",
            )
            r2 = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                raw_data=b'{"logged": 2}',
                content_type="application/json",
            )
            cache.set(request, r1)
            cache.set(request, r2)
            changes_log = Path(tmpdir) / "changes.log"
            assert changes_log.exists()
            with changes_log.open() as f:
                lines = f.readlines()
            assert len(lines) >= 1
            change = json.loads(lines[-1])
            assert change["url"] == request.url
            assert change["old_hash"] != change["new_hash"]

    def test_first_version_no_change_log(self) -> None:
        """First version should not log a change."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileCache(Path(tmpdir))
            request = RequestMetadata(url="https://example.com/first")
            result = FetchResult(
                url=request.url,
                success=True,
                status_code=200,
                raw_data=b'{"first": true}',
                content_type="application/json",
            )
            cache.set(request, result)
            changes_log = Path(tmpdir) / "changes.log"
            if changes_log.exists():
                assert changes_log.read_text().strip() == ""
