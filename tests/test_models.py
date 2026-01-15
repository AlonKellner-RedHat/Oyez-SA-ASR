# Edited by Claude
"""Unit tests for scraper models."""

from datetime import datetime, timedelta, timezone

from oyez_sa_asr.scraper import (
    CacheEntry,
    CacheMeta,
    RequestMetadata,
    get_extension_for_content_type,
)


class TestRequestMetadata:
    """Tests for RequestMetadata."""

    def test_cache_key_deterministic(self) -> None:
        """Cache key should be deterministic for same URL."""
        req1 = RequestMetadata(url="https://example.com/test")
        req2 = RequestMetadata(url="https://example.com/test")
        assert req1.cache_key() == req2.cache_key()

    def test_cache_key_unique_for_different_urls(self) -> None:
        """Cache key should differ for different URLs."""
        req1 = RequestMetadata(url="https://example.com/test1")
        req2 = RequestMetadata(url="https://example.com/test2")
        assert req1.cache_key() != req2.cache_key()

    def test_cache_key_includes_method(self) -> None:
        """Cache key should include HTTP method."""
        req1 = RequestMetadata(url="https://example.com/test", method="GET")
        req2 = RequestMetadata(url="https://example.com/test", method="POST")
        assert req1.cache_key() != req2.cache_key()


class TestGetExtensionForContentType:
    """Tests for get_extension_for_content_type."""

    def test_json(self) -> None:
        """JSON content types should return .json extension."""
        assert get_extension_for_content_type("application/json") == ".json"
        assert (
            get_extension_for_content_type("application/json; charset=utf-8") == ".json"
        )

    def test_html(self) -> None:
        """HTML content type should return .html extension."""
        assert get_extension_for_content_type("text/html") == ".html"

    def test_partial_match(self) -> None:
        """Content types containing json should return .json extension."""
        assert get_extension_for_content_type("application/vnd.api+json") == ".json"

    def test_unknown(self) -> None:
        """Unknown content types should return .bin extension."""
        assert get_extension_for_content_type("application/unknown") == ".bin"


class TestCacheMeta:
    """Tests for CacheMeta."""

    def test_is_expired_false(self) -> None:
        """Non-expired cache should return False."""
        meta = CacheMeta(
            url="https://example.com",
            fetched_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            status_code=200,
        )
        assert not meta.is_expired()

    def test_is_expired_true(self) -> None:
        """Expired cache should return True."""
        meta = CacheMeta(
            url="https://example.com",
            fetched_at=datetime.now(timezone.utc) - timedelta(days=2),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            status_code=200,
        )
        assert meta.is_expired()

    def test_to_dict_and_from_dict(self) -> None:
        """CacheMeta should round-trip through dict serialization."""
        orig = CacheMeta.create(
            url="https://example.com",
            status_code=200,
            raw_path="raw/abc.json",
            ttl_days=30,
        )
        restored = CacheMeta.from_dict(orig.to_dict())
        assert restored.url == orig.url

    def test_create_sets_expiration(self) -> None:
        """Create should set expires_at based on ttl_days."""
        meta = CacheMeta.create(
            url="https://example.com",
            status_code=200,
            raw_path="raw/x.json",
            ttl_days=7,
        )
        assert meta.expires_at == meta.fetched_at + timedelta(days=7)


class TestCacheEntry:
    """Tests for CacheEntry."""

    def test_properties(self) -> None:
        """CacheEntry should expose meta properties."""
        meta = CacheMeta.create(
            url="https://example.com", status_code=200, raw_path="raw/abc.json"
        )
        entry = CacheEntry(meta=meta, response=b'{"test": true}')
        assert entry.url == "https://example.com"
        assert entry.status_code == 200
        assert not entry.is_expired()
