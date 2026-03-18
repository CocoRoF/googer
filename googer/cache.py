"""In-memory TTL cache for Googer search results.

Provides a thread-safe, TTL-based cache that avoids redundant searches
for the same query within a configurable time window.
"""

import hashlib
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from .config import DEFAULT_CACHE_TTL

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _CacheEntry:
    """A single cached value with expiration."""

    value: Any
    expires_at: float


class SearchCache:
    """Thread-safe, TTL-based in-memory cache for search results.

    Args:
        ttl: Time-to-live in seconds for cache entries.  Defaults to 300 (5 min).
        max_size: Maximum number of entries.  When exceeded the oldest entries are evicted.

    Example::

        cache = SearchCache(ttl=60)
        cache.set("key", results)
        cached = cache.get("key")   # returns results or None

    """

    def __init__(self, ttl: int = DEFAULT_CACHE_TTL, *, max_size: int = 256) -> None:
        self._ttl = ttl
        self._max_size = max_size
        self._store: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()

    # -- public API ---------------------------------------------------------

    def get(self, key: str) -> Any | None:
        """Retrieve a cached value, or ``None`` if expired/missing."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.monotonic() > entry.expires_at:
                del self._store[key]
                return None
            logger.debug("Cache hit: %s", key[:40])
            return entry.value

    def set(self, key: str, value: Any) -> None:
        """Store a value with the configured TTL."""
        with self._lock:
            if len(self._store) >= self._max_size:
                self._evict_expired()
            if len(self._store) >= self._max_size:
                self._evict_oldest()
            self._store[key] = _CacheEntry(
                value=value,
                expires_at=time.monotonic() + self._ttl,
            )

    def clear(self) -> None:
        """Remove all cached entries."""
        with self._lock:
            self._store.clear()

    @property
    def size(self) -> int:
        """Number of entries currently in the cache."""
        return len(self._store)

    # -- key building -------------------------------------------------------

    @staticmethod
    def make_key(**kwargs: Any) -> str:
        """Build a deterministic cache key from keyword arguments.

        Uses SHA-256 of the sorted, stringified keyword arguments.
        """
        parts = sorted(f"{k}={v}" for k, v in kwargs.items() if v is not None)
        raw = "|".join(parts)
        return hashlib.sha256(raw.encode()).hexdigest()

    # -- internal -----------------------------------------------------------

    def _evict_expired(self) -> None:
        """Remove all expired entries (caller must hold lock)."""
        now = time.monotonic()
        expired = [k for k, e in self._store.items() if now > e.expires_at]
        for k in expired:
            del self._store[k]

    def _evict_oldest(self) -> None:
        """Remove the oldest entry (caller must hold lock)."""
        if self._store:
            oldest_key = min(self._store, key=lambda k: self._store[k].expires_at)
            del self._store[oldest_key]
