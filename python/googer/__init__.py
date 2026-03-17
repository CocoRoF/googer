"""Googer — A powerful Google Search library for Python, powered by Rust.

Googer provides an elegant, type-safe interface for querying Google
and parsing structured results. The core engine is written in Rust
for maximum performance.

Quick start::

    from googer import Googer

    results = Googer().search("python programming")
    for r in results:
        print(r.title, r.href)

Advanced query::

    from googer import Googer, Query

    q = Query("machine learning").site("arxiv.org").filetype("pdf")
    results = Googer().search(str(q), max_results=20)

"""

import importlib
import logging
from importlib.metadata import version as _pkg_version
from typing import TYPE_CHECKING

try:
    __version__ = _pkg_version("googer")
except Exception:
    __version__ = "0.0.0"
__all__ = (
    "Googer",
    "ImageResult",
    "NewsResult",
    "Query",
    "TextResult",
    "VideoResult",
    # Exceptions
    "GoogerException",
    "HttpException",
    "TimeoutException",
    "RateLimitException",
    "ParseException",
    "QueryBuildException",
    "NoResultsException",
)

# A do-nothing logging handler — library users can configure as they wish
logging.getLogger("googer").addHandler(logging.NullHandler())

if TYPE_CHECKING:
    from ._core import (
        Googer,
        GoogerException,
        HttpException,
        ImageResult,
        NewsResult,
        NoResultsException,
        ParseException,
        Query,
        QueryBuildException,
        RateLimitException,
        TextResult,
        TimeoutException,
        VideoResult,
    )


def __getattr__(name: str) -> object:
    """Lazy-load from the native Rust extension module."""
    _core = importlib.import_module("googer._core")

    if hasattr(_core, name):
        obj = getattr(_core, name)
        globals()[name] = obj
        return obj

    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
