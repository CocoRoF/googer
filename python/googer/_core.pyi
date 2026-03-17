"""Type stubs for the native Rust extension module ``googer._core``.

This file provides type information for IDE autocompletion and static
analysis tools (mypy, pyright, etc.).
"""

from typing import Optional


class GoogerException(Exception):
    """Base exception for all Googer errors."""
    ...

class HttpException(GoogerException):
    """Raised when an HTTP request fails unexpectedly."""
    ...

class TimeoutException(GoogerException):
    """Raised when a request exceeds the configured timeout."""
    ...

class RateLimitException(GoogerException):
    """Raised when Google returns a rate-limit / CAPTCHA response."""
    ...

class ParseException(GoogerException):
    """Raised when HTML parsing fails to extract expected data."""
    ...

class QueryBuildException(GoogerException):
    """Raised when a search query cannot be constructed."""
    ...

class NoResultsException(GoogerException):
    """Raised when a search returns zero results."""
    ...


class TextResult:
    """A single text/web search result."""

    title: str
    href: str
    body: str

    def __init__(self, title: str = "", href: str = "", body: str = "") -> None: ...
    def to_dict(self) -> dict[str, str]: ...
    def keys(self) -> list[str]: ...
    def values(self) -> list[str]: ...
    def items(self) -> list[tuple[str, str]]: ...
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]: ...
    def __getitem__(self, key: str) -> str: ...
    def __contains__(self, key: str) -> bool: ...
    def __len__(self) -> int: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...


class ImageResult:
    """A single image search result."""

    title: str
    image: str
    thumbnail: str
    url: str
    height: str
    width: str
    source: str

    def __init__(
        self,
        title: str = "",
        image: str = "",
        thumbnail: str = "",
        url: str = "",
        height: str = "",
        width: str = "",
        source: str = "",
    ) -> None: ...
    def to_dict(self) -> dict[str, str]: ...
    def keys(self) -> list[str]: ...
    def values(self) -> list[str]: ...
    def items(self) -> list[tuple[str, str]]: ...
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]: ...
    def __getitem__(self, key: str) -> str: ...
    def __contains__(self, key: str) -> bool: ...
    def __len__(self) -> int: ...
    def __repr__(self) -> str: ...


class NewsResult:
    """A single news search result."""

    title: str
    url: str
    body: str
    source: str
    date: str
    image: str

    def __init__(
        self,
        title: str = "",
        url: str = "",
        body: str = "",
        source: str = "",
        date: str = "",
        image: str = "",
    ) -> None: ...
    def to_dict(self) -> dict[str, str]: ...
    def keys(self) -> list[str]: ...
    def values(self) -> list[str]: ...
    def items(self) -> list[tuple[str, str]]: ...
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]: ...
    def __getitem__(self, key: str) -> str: ...
    def __contains__(self, key: str) -> bool: ...
    def __len__(self) -> int: ...
    def __repr__(self) -> str: ...


class VideoResult:
    """A single video search result."""

    title: str
    url: str
    body: str
    duration: str
    source: str
    date: str
    thumbnail: str

    def __init__(
        self,
        title: str = "",
        url: str = "",
        body: str = "",
        duration: str = "",
        source: str = "",
        date: str = "",
        thumbnail: str = "",
    ) -> None: ...
    def to_dict(self) -> dict[str, str]: ...
    def keys(self) -> list[str]: ...
    def values(self) -> list[str]: ...
    def items(self) -> list[tuple[str, str]]: ...
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]: ...
    def __getitem__(self, key: str) -> str: ...
    def __contains__(self, key: str) -> bool: ...
    def __len__(self) -> int: ...
    def __repr__(self) -> str: ...


class Query:
    """Fluent builder for Google search queries."""

    def __init__(self, base: str = "") -> None: ...
    def exact(self, phrase: str) -> "Query": ...
    def or_term(self, term: str) -> "Query": ...
    def exclude(self, term: str) -> "Query": ...
    def site(self, domain: str) -> "Query": ...
    def filetype(self, ext: str) -> "Query": ...
    def intitle(self, text: str) -> "Query": ...
    def inurl(self, text: str) -> "Query": ...
    def intext(self, text: str) -> "Query": ...
    def related(self, url: str) -> "Query": ...
    def cache(self, url: str) -> "Query": ...
    def date_range(self, start: str, end: str) -> "Query": ...
    def raw(self, fragment: str) -> "Query": ...
    def build(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __bool__(self) -> bool: ...


class Googer:
    """Main search facade — the primary public interface.

    All search methods return lists of typed result objects.
    The core HTTP requests and HTML parsing are performed in Rust.
    """

    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: Optional[int] = None,
        *,
        verify: bool = True,
        max_retries: int = 3,
    ) -> None: ...

    def __enter__(self) -> "Googer": ...
    def __exit__(
        self,
        exc_type: Optional[type] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: object = None,
    ) -> None: ...

    def search(
        self,
        query: str,
        *,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: int = 10,
        page: int = 1,
        rank: bool = True,
    ) -> list[TextResult]: ...

    def images(
        self,
        query: str,
        *,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: int = 10,
        size: Optional[str] = None,
        color: Optional[str] = None,
        image_type: Optional[str] = None,
        license_type: Optional[str] = None,
    ) -> list[ImageResult]: ...

    def news(
        self,
        query: str,
        *,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: int = 10,
    ) -> list[NewsResult]: ...

    def videos(
        self,
        query: str,
        *,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: int = 10,
        duration: Optional[str] = None,
    ) -> list[VideoResult]: ...
