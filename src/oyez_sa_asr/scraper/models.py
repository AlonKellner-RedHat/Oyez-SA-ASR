# Edited by Claude
"""Data models for the scraper module."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

# Mapping of content types to file extensions
CONTENT_TYPE_EXTENSIONS: dict[str, str] = {
    "application/json": ".json",
    "text/json": ".json",
    "text/html": ".html",
    "text/plain": ".txt",
    "text/xml": ".xml",
    "application/xml": ".xml",
    "text/css": ".css",
    "text/javascript": ".js",
    "application/javascript": ".js",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "video/mp4": ".mp4",
    "application/pdf": ".pdf",
    "application/octet-stream": ".bin",
}


def get_extension_for_content_type(content_type: str) -> str:
    """Get file extension for a content type.

    Args:
        content_type: The MIME content type (may include parameters).

    Returns
    -------
        File extension including the dot (e.g., '.json').
    """
    # Strip parameters like charset
    base_type = content_type.split(";")[0].strip().lower()

    # Check exact match first
    if base_type in CONTENT_TYPE_EXTENSIONS:
        return CONTENT_TYPE_EXTENSIONS[base_type]

    # Check for partial matches (e.g., "application/vnd.api+json" -> .json)
    if "json" in base_type:
        return ".json"
    if "xml" in base_type:
        return ".xml"
    if "html" in base_type:
        return ".html"

    # Default to .bin for unknown types
    return ".bin"


@dataclass
class ContentVersion:
    """Represents a unique version of cached content identified by hash."""

    content_hash: str  # SHA256 of raw content
    first_seen: datetime  # When this version first appeared
    last_seen: datetime  # When this version was last seen
    raw_path: str  # Relative path to raw file

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "content_hash": self.content_hash,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "raw_path": self.raw_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContentVersion":
        """Create a ContentVersion from a dictionary."""
        return cls(
            content_hash=data["content_hash"],
            first_seen=datetime.fromisoformat(data["first_seen"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
            raw_path=data["raw_path"],
        )


@dataclass
class RequestMetadata:
    """Metadata about a request."""

    url: str
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)

    def cache_key(self) -> str:
        """Generate a cache key from the request metadata."""
        key_str = f"{self.method}:{self.url}"
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]


@dataclass
class CacheMeta:
    """Metadata for a cached response with version tracking."""

    url: str
    fetched_at: datetime
    expires_at: datetime
    status_code: int
    content_type: str = "application/json"
    raw_path: str = ""  # Points to latest version's raw file for quick access
    versions: list[ContentVersion] = field(default_factory=list)

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def get_latest_version(self) -> ContentVersion | None:
        """Get the version with the most recent last_seen timestamp."""
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.last_seen)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "fetched_at": self.fetched_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status_code": self.status_code,
            "content_type": self.content_type,
            "raw_path": self.raw_path,
            "versions": [v.to_dict() for v in self.versions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheMeta":
        """Create a CacheMeta from a dictionary."""
        versions_data = data.get("versions", [])
        versions = [ContentVersion.from_dict(v) for v in versions_data]
        return cls(
            url=data["url"],
            fetched_at=datetime.fromisoformat(data["fetched_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            status_code=data["status_code"],
            content_type=data.get("content_type", "application/json"),
            raw_path=data.get("raw_path", ""),
            versions=versions,
        )

    @classmethod
    def create(
        cls,
        url: str,
        status_code: int,
        raw_path: str,
        ttl_days: int = 30,
        content_type: str = "application/json",
    ) -> "CacheMeta":
        """Create new cache metadata with the given TTL."""
        now = datetime.now(timezone.utc)
        return cls(
            url=url,
            fetched_at=now,
            expires_at=now + timedelta(days=ttl_days),
            status_code=status_code,
            content_type=content_type,
            raw_path=raw_path,
        )


@dataclass
class CacheEntry:
    """A complete cached response (metadata + raw response)."""

    meta: CacheMeta
    response: bytes

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return self.meta.is_expired()

    @property
    def url(self) -> str:
        """Get the URL from metadata."""
        return self.meta.url

    @property
    def status_code(self) -> int:
        """Get the status code from metadata."""
        return self.meta.status_code


@dataclass
class FetchResult:
    """Result of a fetch operation."""

    url: str
    success: bool
    status_code: int | None = None
    data: Any = None
    raw_data: bytes | None = None
    content_type: str = "application/json"
    error: str | None = None
    from_cache: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "success": self.success,
            "status_code": self.status_code,
            "error": self.error,
            "from_cache": self.from_cache,
            "content_type": self.content_type,
        }
