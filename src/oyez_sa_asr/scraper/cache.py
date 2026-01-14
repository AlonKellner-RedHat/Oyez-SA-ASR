# Edited by Claude
"""File-based cache with versioned content storage."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .models import (
    CacheEntry,
    CacheMeta,
    ContentVersion,
    FetchResult,
    RequestMetadata,
    get_extension_for_content_type,
)


class FileCache:
    """Cache with versioned content tracking keyed by content hash."""

    def __init__(self, cache_dir: Path, ttl_days: int = 30) -> None:
        self.cache_dir = cache_dir
        self.ttl_days = ttl_days
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_domain_dir(self, url: str) -> Path:
        return self.cache_dir / urlparse(url).netloc

    def _get_meta_dir(self, url: str) -> Path:
        d = self._get_domain_dir(url) / "meta"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _get_raw_dir(self, url: str) -> Path:
        d = self._get_domain_dir(url) / "raw"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _get_failed_dir(self) -> Path:
        d = self.cache_dir / "failed"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _get_meta_path(self, request: RequestMetadata) -> Path:
        return self._get_meta_dir(request.url) / f"{request.cache_key()}.json"

    def _get_raw_path(
        self, request: RequestMetadata, ctype: str = "application/json"
    ) -> Path:
        ext = get_extension_for_content_type(ctype)
        return self._get_raw_dir(request.url) / f"{request.cache_key()}{ext}"

    def _get_raw_path_by_hash(self, url: str, chash: str, ctype: str) -> Path:
        return (
            self._get_raw_dir(url) / f"{chash}{get_extension_for_content_type(ctype)}"
        )

    def _get_raw_path_relative_by_hash(self, chash: str, ctype: str) -> str:
        return f"raw/{chash}{get_extension_for_content_type(ctype)}"

    def _get_failed_path(self, request: RequestMetadata) -> Path:
        return self._get_failed_dir() / f"{request.cache_key()}.json"

    @staticmethod
    def _compute_content_hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()[:16]

    def _log_change(self, url: str, req_hash: str, old_h: str, new_h: str) -> None:
        entry = {
            "url": url,
            "request_hash": req_hash,
            "old_hash": old_h,
            "new_hash": new_h,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }
        with (self.cache_dir / "changes.log").open("a") as f:
            f.write(json.dumps(entry) + "\n")

    def get(self, request: RequestMetadata) -> CacheEntry | None:
        """Get latest cached version if exists."""
        meta_path = self._get_meta_path(request)
        if not meta_path.exists():
            return None
        try:
            with meta_path.open("r") as f:
                meta = CacheMeta.from_dict(json.load(f))
            latest = meta.get_latest_version()
            if latest:
                raw_path = self._get_domain_dir(request.url) / latest.raw_path
            elif meta.raw_path:
                raw_path = self._get_domain_dir(request.url) / meta.raw_path
            else:
                raw_path = self._get_raw_path(request, meta.content_type)
            if not raw_path.exists():
                return None
            return CacheEntry(meta=meta, response=raw_path.read_bytes())
        except (json.JSONDecodeError, KeyError, ValueError):
            meta_path.unlink(missing_ok=True)
            return None

    def set(self, request: RequestMetadata, result: FetchResult) -> None:
        """Store result with version tracking. Logs changes to changes.log."""
        if not result.success:
            self._store_failed(request, result)
            return
        raw_data = result.raw_data or (
            json.dumps(result.data).encode() if result.data else None
        )
        if not raw_data:
            return

        chash, now = self._compute_content_hash(raw_data), datetime.now(timezone.utc)
        meta_path = self._get_meta_path(request)

        meta = None
        if meta_path.exists():
            try:
                with meta_path.open("r") as f:
                    meta = CacheMeta.from_dict(json.load(f))
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        if not meta:
            meta = CacheMeta.create(
                request.url,
                result.status_code or 200,
                "",
                self.ttl_days,
                result.content_type,
            )

        existing = next((v for v in meta.versions if v.content_hash == chash), None)
        if existing:
            existing.last_seen = now
        else:
            old = meta.get_latest_version()
            if old:
                self._log_change(
                    request.url, request.cache_key(), old.content_hash, chash
                )
            rpath = self._get_raw_path_relative_by_hash(chash, result.content_type)
            meta.versions.append(ContentVersion(chash, now, now, rpath))
            self._get_raw_path_by_hash(
                request.url, chash, result.content_type
            ).write_bytes(raw_data)

        meta.fetched_at, meta.status_code, meta.content_type = (
            now,
            result.status_code or 200,
            result.content_type,
        )
        # Update raw_path to point to latest version
        latest = meta.get_latest_version()
        meta.raw_path = latest.raw_path if latest else ""

        with meta_path.open("w") as f:
            json.dump(meta.to_dict(), f, indent=2)

    def _store_failed(self, request: RequestMetadata, result: FetchResult) -> None:
        with self._get_failed_path(request).open("w") as f:
            json.dump(result.to_dict(), f, indent=2)

    def delete(self, request: RequestMetadata) -> bool:
        """Delete a cache entry."""
        meta_path = self._get_meta_path(request)
        if not meta_path.exists():
            return False
        try:
            with meta_path.open("r") as f:
                meta = CacheMeta.from_dict(json.load(f))
            if meta.raw_path:
                (self._get_domain_dir(request.url) / meta.raw_path).unlink(
                    missing_ok=True
                )
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
        meta_path.unlink()
        return True

    def clear_expired(self) -> int:
        """Clear expired entries."""
        cleared = 0
        for domain_dir in self.cache_dir.iterdir():
            if not domain_dir.is_dir() or domain_dir.name == "failed":
                continue
            meta_dir = domain_dir / "meta"
            if not meta_dir.exists():
                continue
            for mf in meta_dir.glob("*.json"):
                try:
                    with mf.open("r") as f:
                        meta = CacheMeta.from_dict(json.load(f))
                    if meta.is_expired():
                        if meta.raw_path:
                            (domain_dir / meta.raw_path).unlink(missing_ok=True)
                        mf.unlink()
                        cleared += 1
                except (json.JSONDecodeError, KeyError, ValueError):
                    mf.unlink()
                    cleared += 1
        return cleared
