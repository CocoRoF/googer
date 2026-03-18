"""Googer — A powerful Google Search library for Python.

Googer provides an elegant, type-safe interface for querying Google
and parsing structured results.

Quick start::

    from googer import Googer

    results = Googer().search("python programming")
    for r in results:
        print(r.title, r.href)

Advanced query::

    from googer import Googer, Query

    q = Query("machine learning").site("arxiv.org").filetype("pdf")
    results = Googer().search(q, max_results=20)

"""

import logging
from importlib.metadata import version
from typing import TYPE_CHECKING

__version__ = version("googer")
__all__ = (
    "Googer",
    "ImageResult",
    "NewsResult",
    "Query",
    "TextResult",
    "VideoResult",
)

# A do-nothing logging handler — library users can configure as they wish
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger("googer").addHandler(logging.NullHandler())

if TYPE_CHECKING:
    from .googer import Googer
    from .query_builder import Query
    from .results import ImageResult, NewsResult, TextResult, VideoResult


def __getattr__(name: str) -> object:
    """Lazy-load heavy modules on first access."""
    if name == "Googer":
        from .googer import Googer

        globals()["Googer"] = Googer
        return Googer
    if name == "Query":
        from .query_builder import Query

        globals()["Query"] = Query
        return Query
    if name in ("TextResult", "ImageResult", "NewsResult", "VideoResult"):
        from . import results as _results

        cls = getattr(_results, name)
        globals()[name] = cls
        return cls
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
