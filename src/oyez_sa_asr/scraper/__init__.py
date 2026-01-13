# Edited by Claude
"""Scraper module for Oyez API."""

from .cache import FileCache
from .fetcher import AdaptiveFetcher
from .models import (
    CacheEntry,
    CacheMeta,
    ContentVersion,
    FetchResult,
    RequestMetadata,
    get_extension_for_content_type,
)
from .parser import (
    CasesIndex,
    CaseSummary,
    Citation,
    TimelineEvent,
    parse_cached_cases,
)
from .traverser import OyezCasesTraverser

__all__ = [
    "AdaptiveFetcher",
    "CacheEntry",
    "CacheMeta",
    "CaseSummary",
    "CasesIndex",
    "Citation",
    "ContentVersion",
    "FetchResult",
    "FileCache",
    "OyezCasesTraverser",
    "RequestMetadata",
    "TimelineEvent",
    "get_extension_for_content_type",
    "parse_cached_cases",
]
