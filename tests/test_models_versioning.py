# Edited by Claude
"""Unit tests for versioned scraper models."""

from datetime import datetime, timedelta, timezone

from oyez_sa_asr.scraper import CacheMeta
from oyez_sa_asr.scraper.models import ContentVersion


class TestContentVersion:
    """Tests for ContentVersion dataclass."""

    def test_create(self) -> None:
        """Should create ContentVersion with required fields."""
        now = datetime.now(timezone.utc)
        v = ContentVersion(
            content_hash="abc123",
            first_seen=now,
            last_seen=now,
            raw_path="raw/abc.json",
        )
        assert v.content_hash == "abc123"
        assert v.first_seen == now

    def test_to_dict(self) -> None:
        """Should serialize to dict."""
        now = datetime.now(timezone.utc)
        v = ContentVersion(
            content_hash="abc", first_seen=now, last_seen=now, raw_path="raw/abc.json"
        )
        d = v.to_dict()
        assert d["content_hash"] == "abc"
        assert d["first_seen"] == now.isoformat()

    def test_from_dict(self) -> None:
        """Should deserialize from dict."""
        now = datetime.now(timezone.utc)
        d = {
            "content_hash": "xyz",
            "first_seen": now.isoformat(),
            "last_seen": now.isoformat(),
            "raw_path": "raw/x.json",
        }
        v = ContentVersion.from_dict(d)
        assert v.content_hash == "xyz"

    def test_round_trip(self) -> None:
        """Should round-trip through dict."""
        now = datetime.now(timezone.utc)
        orig = ContentVersion(
            content_hash="rt",
            first_seen=now,
            last_seen=now + timedelta(hours=1),
            raw_path="raw/rt.json",
        )
        restored = ContentVersion.from_dict(orig.to_dict())
        assert restored.content_hash == orig.content_hash
        assert restored.last_seen == orig.last_seen


class TestCacheMetaVersioned:
    """Tests for CacheMeta with version tracking."""

    def test_with_versions_list(self) -> None:
        """CacheMeta should support a versions list."""
        now = datetime.now(timezone.utc)
        v = ContentVersion(
            content_hash="h1", first_seen=now, last_seen=now, raw_path="raw/h1.json"
        )
        meta = CacheMeta(
            url="https://example.com",
            fetched_at=now,
            expires_at=now + timedelta(days=30),
            status_code=200,
            versions=[v],
        )
        assert len(meta.versions) == 1

    def test_get_latest_version_single(self) -> None:
        """get_latest_version should return only version."""
        now = datetime.now(timezone.utc)
        v = ContentVersion(
            content_hash="only", first_seen=now, last_seen=now, raw_path="raw/only.json"
        )
        meta = CacheMeta(
            url="https://example.com",
            fetched_at=now,
            expires_at=now + timedelta(days=30),
            status_code=200,
            versions=[v],
        )
        assert meta.get_latest_version().content_hash == "only"

    def test_get_latest_version_multiple(self) -> None:
        """get_latest_version should return version with most recent last_seen."""
        now = datetime.now(timezone.utc)
        old = ContentVersion(
            "old", now - timedelta(days=10), now - timedelta(days=5), "raw/old.json"
        )
        new = ContentVersion("new", now - timedelta(days=2), now, "raw/new.json")
        meta = CacheMeta(
            "https://example.com",
            now,
            now + timedelta(days=30),
            200,
            versions=[old, new],
        )
        assert meta.get_latest_version().content_hash == "new"

    def test_get_latest_version_empty(self) -> None:
        """get_latest_version should return None when no versions."""
        now = datetime.now(timezone.utc)
        meta = CacheMeta(
            "https://example.com", now, now + timedelta(days=30), 200, versions=[]
        )
        assert meta.get_latest_version() is None

    def test_versions_serialization(self) -> None:
        """Versions should be included in to_dict/from_dict."""
        now = datetime.now(timezone.utc)
        v = ContentVersion("set", now, now, "raw/ser.json")
        meta = CacheMeta(
            "https://example.com", now, now + timedelta(days=30), 200, versions=[v]
        )
        data = meta.to_dict()
        assert len(data["versions"]) == 1
        restored = CacheMeta.from_dict(data)
        assert restored.versions[0].content_hash == "set"

    def test_backward_compatible_no_versions(self) -> None:
        """Should handle old cache entries without versions field."""
        now = datetime.now(timezone.utc)
        data = {
            "url": "https://example.com",
            "fetched_at": now.isoformat(),
            "expires_at": (now + timedelta(days=30)).isoformat(),
            "status_code": 200,
            "content_type": "application/json",
            "raw_path": "raw/old.json",
        }
        meta = CacheMeta.from_dict(data)
        assert meta.versions == []
