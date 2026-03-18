"""Googer — A powerful, multi-engine search library for Python.

Googer provides an elegant, type-safe interface for web search using
multiple providers (DuckDuckGo, Brave Search, Google) with automatic
fallback and concurrent multi-engine mode.

Features beyond DDGS:

* **3 search engines** — DuckDuckGo, Brave Search, Google
* **Multi-engine mode** — concurrent search across all engines + merge
* **Suggestions** — autocomplete via ``suggest()``
* **Instant Answers** — structured answers via ``answers()``
* **Result caching** — TTL-based in-memory cache
* **Provider metadata** — every result has a ``provider`` field
* **Query builder** — ``Query("term").site("x.com").filetype("pdf")``

Quick start::

    from googer import Googer

    # Default: DuckDuckGo with fallback to Brave, then Google
    results = Googer().search("python programming")
    for r in results:
        print(f"[{r.provider}] {r.title} - {r.href}")

Multi-engine concurrent search::

    results = Googer(engine="multi").search("python", max_results=20)

Suggestions and answers::

    suggestions = Googer().suggest("python prog")
    answer = Googer().answers("python programming language")

Choose a specific engine::

    # Brave Search
    results = Googer(engine="brave").search("python")

    # Google with browser backend
    results = Googer(engine="google", backend="browser").search("python")

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
    "AnswerResult",
    "Googer",
    "ImageResult",
    "NewsResult",
    "Query",
    "TextResult",
    "VideoResult",
)

# A do-nothing logging handler — library users can configure as they wish
logging.getLogger("googer").addHandler(logging.NullHandler())

if TYPE_CHECKING:
    from .googer import Googer
    from .query_builder import Query
    from .results import AnswerResult, ImageResult, NewsResult, TextResult, VideoResult


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
    if name in ("TextResult", "ImageResult", "NewsResult", "VideoResult", "AnswerResult"):
        from . import results as _results

        cls = getattr(_results, name)
        globals()[name] = cls
        return cls
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
