"""Result dataclasses for Googer.

Each search category has its own strongly-typed dataclass.
A :class:`BaseResult` mixin auto-normalises fields on assignment so
that consumers always receive clean data.
"""

from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from .utils import normalize_date, normalize_text, normalize_url


# ---------------------------------------------------------------------------
# Base mixin — auto-normalisation on ``__setattr__``
# ---------------------------------------------------------------------------


class BaseResult:
    """Mixin that normalises common fields on assignment.

    Subclasses gain automatic cleaning of titles, bodies, URLs, and dates
    simply by inheriting from this class.
    """

    _normalizers: ClassVar[Mapping[str, Callable[[Any], str]]] = {
        "title": normalize_text,
        "body": normalize_text,
        "description": normalize_text,
        "snippet": normalize_text,
        "href": normalize_url,
        "url": normalize_url,
        "thumbnail": normalize_url,
        "image": normalize_url,
        "date": normalize_date,
        "author": normalize_text,
        "publisher": normalize_text,
        "source": normalize_text,
        "content": normalize_text,
    }

    def __setattr__(self, name: str, value: str) -> None:
        """Apply normaliser when setting a known field."""
        if value and (normalizer := self._normalizers.get(name)):
            value = normalizer(value)
        object.__setattr__(self, name, value)

    # -- dict-like access (backward compatibility) --------------------------

    def __getitem__(self, key: str) -> Any:
        """Allow ``result["title"]`` style access."""
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key) from None

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and not key.startswith("_") and hasattr(self, key)

    def __iter__(self):
        """Iterate over field names (enables ``dict(result)``)."""
        return (k for k in self.__dict__ if not k.startswith("_"))

    def __len__(self) -> int:
        return sum(1 for k in self.__dict__ if not k.startswith("_"))

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-style ``.get()`` with optional default."""
        return getattr(self, key, default)

    def keys(self) -> list[str]:
        """Return field names."""
        return [k for k in self.__dict__ if not k.startswith("_")]

    def values(self) -> list[Any]:
        """Return field values."""
        return [v for k, v in self.__dict__.items() if not k.startswith("_")]

    def items(self) -> list[tuple[str, Any]]:
        """Return ``(field, value)`` pairs."""
        return [(k, v) for k, v in self.__dict__.items() if not k.startswith("_")]

    # -- serialization ------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary representation."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# Concrete result types
# ---------------------------------------------------------------------------


@dataclass
class TextResult(BaseResult):
    """A single text/web search result."""

    title: str = ""
    href: str = ""
    body: str = ""


@dataclass
class ImageResult(BaseResult):
    """A single image search result."""

    title: str = ""
    image: str = ""
    thumbnail: str = ""
    url: str = ""
    height: str = ""
    width: str = ""
    source: str = ""


@dataclass
class NewsResult(BaseResult):
    """A single news search result."""

    title: str = ""
    url: str = ""
    body: str = ""
    source: str = ""
    date: str = ""
    image: str = ""


@dataclass
class VideoResult(BaseResult):
    """A single video search result."""

    title: str = ""
    url: str = ""
    body: str = ""
    duration: str = ""
    source: str = ""
    date: str = ""
    thumbnail: str = ""


# ---------------------------------------------------------------------------
# Aggregator — deduplication + frequency-based ordering
# ---------------------------------------------------------------------------


class ResultsAggregator:
    """Deduplicates results by a set of cache fields and orders by frequency.

    Attributes:
        cache_fields: Set of field names used to compute a dedup key.

    """

    def __init__(self, cache_fields: set[str]) -> None:
        if not cache_fields:
            msg = "At least one cache_field must be provided"
            raise ValueError(msg)
        self.cache_fields = cache_fields
        self._counter: Counter[str] = Counter()
        self._cache: dict[str, BaseResult] = {}

    # -- internal helpers ---------------------------------------------------

    def _get_key(self, item: BaseResult) -> str:
        for key in item.__dict__:
            if key in self.cache_fields:
                val = str(item.__dict__[key])
                if val:
                    return val
        msg = f"Item {item!r} has none of the cache fields {self.cache_fields}"
        raise AttributeError(msg)

    # -- public API ---------------------------------------------------------

    def __len__(self) -> int:
        """Number of unique results accumulated so far."""
        return len(self._cache)

    def append(self, item: BaseResult) -> None:
        """Add *item*, deduplicating and preferring longer ``body``."""
        key = self._get_key(item)
        existing = self._cache.get(key)
        if existing is None or len(item.__dict__.get("body", "")) > len(
            existing.__dict__.get("body", ""),
        ):
            self._cache[key] = item
        self._counter[key] += 1

    def extend(self, items: list[BaseResult]) -> None:
        """Append every item in *items*."""
        for item in items:
            self.append(item)

    def extract(self) -> list[BaseResult]:
        """Return accumulated result objects sorted by descending frequency."""
        return [self._cache[key] for key, _ in self._counter.most_common()]

    def extract_dicts(self) -> list[dict[str, Any]]:
        """Return accumulated results as dicts sorted by descending frequency."""
        return [self._cache[key].to_dict() for key, _ in self._counter.most_common()]
