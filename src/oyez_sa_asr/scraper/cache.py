# Edited by Claude
"""File-based cache for HTTP responses with separate metadata and raw storage."""

import json
from pathlib import Path
from urllib.parse import urlparse

from .models import (
    CacheEntry,
    CacheMeta,
    FetchResult,
    RequestMetadata,
    get_extension_for_content_type,
)


class FileCache:
    """File-based cache with separate metadata and raw response storage.

    Directory structure:
        .cache/
            <domain>/
                meta/
                    <hash>.json    # request metadata (timestamps, status, raw_path)
                raw/
                    <hash>.json    # raw response (extension matches content type)
            failed/
                <hash>.json        # failed request info
    """

    def __init__(self, cache_dir: Path, ttl_days: int = 30) -> None:
        """Initialize the cache.

        Args:
            cache_dir: Root directory for cache storage.
            ttl_days: Time-to-live for cache entries in days.
        """
        self.cache_dir = cache_dir
        self.ttl_days = ttl_days
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_domain_dir(self, url: str) -> Path:
        """Get the domain-specific cache directory."""
        parsed = urlparse(url)
        return self.cache_dir / parsed.netloc

    def _get_meta_dir(self, url: str) -> Path:
        """Get the metadata directory for a domain."""
        meta_dir = self._get_domain_dir(url) / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        return meta_dir

    def _get_raw_dir(self, url: str) -> Path:
        """Get the raw response directory for a domain."""
        raw_dir = self._get_domain_dir(url) / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        return raw_dir

    def _get_failed_dir(self) -> Path:
        """Get the directory for failed requests."""
        failed_dir = self.cache_dir / "failed"
        failed_dir.mkdir(parents=True, exist_ok=True)
        return failed_dir

    def _get_meta_path(self, request: RequestMetadata) -> Path:
        """Get the metadata file path for a request."""
        meta_dir = self._get_meta_dir(request.url)
        return meta_dir / f"{request.cache_key()}.json"

    def _get_raw_path(
        self, request: RequestMetadata, content_type: str = "application/json"
    ) -> Path:
        """Get the raw response file path for a request.

        Args:
            request: The request metadata.
            content_type: Content type to determine file extension.

        Returns
        -------
            Path to the raw response file.
        """
        raw_dir = self._get_raw_dir(request.url)
        ext = get_extension_for_content_type(content_type)
        return raw_dir / f"{request.cache_key()}{ext}"

    def _get_raw_path_relative(
        self, request: RequestMetadata, content_type: str
    ) -> str:
        """Get the relative path to raw file (for storing in metadata)."""
        ext = get_extension_for_content_type(content_type)
        return f"raw/{request.cache_key()}{ext}"

    def _get_failed_path(self, request: RequestMetadata) -> Path:
        """Get the failed request file path."""
        failed_dir = self._get_failed_dir()
        return failed_dir / f"{request.cache_key()}.json"

    def get(self, request: RequestMetadata) -> CacheEntry | None:
        """Get a cached entry if it exists and is not expired.

        Args:
            request: The request metadata to look up.

        Returns
        -------
            The cached entry if valid, None otherwise.
        """
        meta_path = self._get_meta_path(request)

        if not meta_path.exists():
            return None

        try:
            with meta_path.open("r") as f:
                meta_data = json.load(f)
            meta = CacheMeta.from_dict(meta_data)

            if meta.is_expired():
                self._delete_entry_by_meta(meta_path, meta, request)
                return None

            # Use raw_path from metadata to find the raw file
            if meta.raw_path:
                raw_path = self._get_domain_dir(request.url) / meta.raw_path
            else:
                # Fallback for old cache entries without raw_path
                raw_path = self._get_raw_path(request, meta.content_type)

            if not raw_path.exists():
                meta_path.unlink(missing_ok=True)
                return None

            raw_response = raw_path.read_bytes()
            return CacheEntry(meta=meta, response=raw_response)

        except (json.JSONDecodeError, KeyError, ValueError):
            meta_path.unlink(missing_ok=True)
            return None

    def _delete_entry_by_meta(
        self, meta_path: Path, meta: CacheMeta, request: RequestMetadata
    ) -> None:
        """Delete cache entry files using metadata info."""
        meta_path.unlink(missing_ok=True)
        if meta.raw_path:
            raw_path = self._get_domain_dir(request.url) / meta.raw_path
            raw_path.unlink(missing_ok=True)

    def _delete_entry_files(self, meta_path: Path, raw_path: Path) -> None:
        """Delete both metadata and raw files for an entry."""
        meta_path.unlink(missing_ok=True)
        raw_path.unlink(missing_ok=True)

    def set(self, request: RequestMetadata, result: FetchResult) -> None:
        """Store a successful fetch result in the cache.

        Args:
            request: The request metadata.
            result: The fetch result to cache.
        """
        if not result.success:
            self._store_failed(request, result)
            return

        # Determine raw path with correct extension
        raw_path_relative = self._get_raw_path_relative(request, result.content_type)

        meta = CacheMeta.create(
            url=request.url,
            status_code=result.status_code or 200,
            raw_path=raw_path_relative,
            ttl_days=self.ttl_days,
            content_type=result.content_type,
        )

        # Write metadata
        meta_path = self._get_meta_path(request)
        with meta_path.open("w") as f:
            json.dump(meta.to_dict(), f, indent=2)

        # Write raw response with correct extension
        raw_path = self._get_raw_path(request, result.content_type)
        raw_data = result.raw_data
        if raw_data is None and result.data is not None:
            # Fallback: serialize data to JSON bytes if no raw_data provided
            raw_data = json.dumps(result.data).encode("utf-8")
        if raw_data is not None:
            raw_path.write_bytes(raw_data)

    def _store_failed(self, request: RequestMetadata, result: FetchResult) -> None:
        """Store a failed request separately.

        Args:
            request: The request metadata.
            result: The failed fetch result.
        """
        failed_path = self._get_failed_path(request)
        with failed_path.open("w") as f:
            json.dump(result.to_dict(), f, indent=2)

    def delete(self, request: RequestMetadata) -> bool:
        """Delete a cache entry.

        Args:
            request: The request metadata.

        Returns
        -------
            True if an entry was deleted, False otherwise.
        """
        meta_path = self._get_meta_path(request)
        deleted = False

        if meta_path.exists():
            try:
                with meta_path.open("r") as f:
                    meta_data = json.load(f)
                meta = CacheMeta.from_dict(meta_data)
                if meta.raw_path:
                    raw_path = self._get_domain_dir(request.url) / meta.raw_path
                    raw_path.unlink(missing_ok=True)
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
            meta_path.unlink()
            deleted = True

        return deleted

    def clear_expired(self) -> int:
        """Clear all expired entries from the cache.

        Returns
        -------
            Number of entries cleared.
        """
        cleared = 0
        for domain_dir in self.cache_dir.iterdir():
            if not domain_dir.is_dir() or domain_dir.name == "failed":
                continue

            meta_dir = domain_dir / "meta"
            if not meta_dir.exists():
                continue

            for meta_file in meta_dir.glob("*.json"):
                try:
                    with meta_file.open("r") as f:
                        data = json.load(f)
                    meta = CacheMeta.from_dict(data)
                    if meta.is_expired():
                        # Delete raw file using path from metadata
                        if meta.raw_path:
                            raw_path = domain_dir / meta.raw_path
                            raw_path.unlink(missing_ok=True)
                        meta_file.unlink()
                        cleared += 1
                except (json.JSONDecodeError, KeyError, ValueError):
                    meta_file.unlink()
                    cleared += 1

        return cleared
