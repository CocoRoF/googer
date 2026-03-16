"""Googer — A powerful Google Search library for Python.

Googer provides an elegant, type-safe interface for querying Google
and parsing structured results.

Quick start::

    from googer import Googer

    results = Googer().search("python programming")
    for r in results:
        print(r["title"], r["href"])

Advanced query::

    from googer import Googer, Query

    q = Query("machine learning").site("arxiv.org").filetype("pdf")
    results = Googer().search(q, max_results=20)

"""

import logging
from importlib.metadata import version
from typing import TYPE_CHECKING

__version__ = version("googer")
__all__ = ("Googer", "Query")

# A do-nothing logging handler — library users can configure as they wish
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger("googer").addHandler(logging.NullHandler())

if TYPE_CHECKING:
    from .googer import Googer
    from .query_builder import Query


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
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
