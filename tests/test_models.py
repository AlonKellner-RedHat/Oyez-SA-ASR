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

    def test_json_content_type(self) -> None:
        """Should return .json for JSON content types."""
        assert get_extension_for_content_type("application/json") == ".json"
        assert get_extension_for_content_type("text/json") == ".json"
        assert (
            get_extension_for_content_type("application/json; charset=utf-8") == ".json"
        )

    def test_html_content_type(self) -> None:
        """Should return .html for HTML content types."""
        assert get_extension_for_content_type("text/html") == ".html"
        assert get_extension_for_content_type("text/html; charset=utf-8") == ".html"

    def test_partial_match(self) -> None:
        """Should match partial content types like vnd.api+json."""
        assert get_extension_for_content_type("application/vnd.api+json") == ".json"

    def test_unknown_type(self) -> None:
        """Should return .bin for unknown types."""
        assert get_extension_for_content_type("application/unknown") == ".bin"


class TestCacheMeta:
    """Tests for CacheMeta."""

    def test_is_expired_false_for_future(self) -> None:
        """Entry should not be expired if expires_at is in the future."""
        meta = CacheMeta(
            url="https://example.com",
            fetched_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            status_code=200,
        )
        assert not meta.is_expired()

    def test_is_expired_true_for_past(self) -> None:
        """Entry should be expired if expires_at is in the past."""
        meta = CacheMeta(
            url="https://example.com",
            fetched_at=datetime.now(timezone.utc) - timedelta(days=2),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            status_code=200,
        )
        assert meta.is_expired()

    def test_to_dict_and_from_dict(self) -> None:
        """Should round-trip through dict serialization."""
        original = CacheMeta.create(
            url="https://example.com",
            status_code=200,
            raw_path="raw/abc123.json",
            ttl_days=30,
        )
        data = original.to_dict()
        restored = CacheMeta.from_dict(data)

        assert restored.url == original.url
        assert restored.status_code == original.status_code
        assert restored.content_type == original.content_type
        assert restored.raw_path == original.raw_path

    def test_create_sets_expiration(self) -> None:
        """Create should set correct expiration time."""
        meta = CacheMeta.create(
            url="https://example.com",
            status_code=200,
            raw_path="raw/x.json",
            ttl_days=7,
        )
        expected_expires = meta.fetched_at + timedelta(days=7)
        assert meta.expires_at == expected_expires


class TestCacheEntry:
    """Tests for CacheEntry (combined metadata + response)."""

    def test_cache_entry_properties(self) -> None:
        """CacheEntry should expose metadata properties."""
        meta = CacheMeta.create(
            url="https://example.com", status_code=200, raw_path="raw/abc.json"
        )
        entry = CacheEntry(meta=meta, response=b'{"test": true}')

        assert entry.url == "https://example.com"
        assert entry.status_code == 200
        assert not entry.is_expired()
