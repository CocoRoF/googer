"""Main Googer class — the primary public interface.

This module provides the :class:`Googer` class, which is the single
entry point for all Google search functionality.  It manages HTTP
sessions, delegates to the appropriate engine, aggregates results,
and applies ranking.

Example::

    from googer import Googer

    g = Googer()
    results = g.search("python programming")

    # With advanced query
    from googer import Googer, Query
    q = Query("machine learning").site("arxiv.org").filetype("pdf")
    results = Googer().search(q)

    # Context manager for resource cleanup
    with Googer(proxy="socks5://127.0.0.1:9150") as g:
        news = g.news("artificial intelligence", timelimit="d")
"""

import logging
import os
from types import TracebackType
from typing import Any

from .config import (
    DEFAULT_MAX_RESULTS,
    DEFAULT_REGION,
    DEFAULT_SAFESEARCH,
    DEFAULT_TIMEOUT,
)
from .engines import ENGINES
from .engines.base import BaseEngine
from .exceptions import GoogerException, NoResultsException
from .http_client import HttpClient
from .query_builder import Query
from .ranker import Ranker
from .results import (
    BaseResult,
    ImageResult,
    NewsResult,
    ResultsAggregator,
    TextResult,
    VideoResult,
)
from .utils import expand_proxy_alias

logger = logging.getLogger(__name__)


class Googer:
    """Google Search client — search the web, images, news, and videos.

    Args:
        proxy: Proxy URL (``http://``, ``https://``, ``socks5://``).
            Also reads from ``GOOGER_PROXY`` env var.
            Special shorthand ``"tb"`` expands to the Tor Browser SOCKS5 proxy.
        timeout: Request timeout in seconds.  Defaults to 10.
        verify: SSL verification — ``True``, ``False``, or path to a PEM file.
        max_retries: Maximum number of retry attempts per request.

    Example::

        >>> from googer import Googer
        >>> results = Googer().search("python", max_results=5)

    """

    def __init__(
        self,
        proxy: str | None = None,
        timeout: int | None = DEFAULT_TIMEOUT,
        *,
        verify: bool | str = True,
        max_retries: int = 3,
    ) -> None:
        resolved_proxy = expand_proxy_alias(proxy) or os.environ.get("GOOGER_PROXY")
        self._http = HttpClient(
            proxy=resolved_proxy,
            timeout=timeout,
            verify=verify,
            max_retries=max_retries,
        )
        self._engine_cache: dict[str, BaseEngine[Any]] = {}
        self._ranker = Ranker()

    # -- context manager ----------------------------------------------------

    def __enter__(self) -> "Googer":
        """Enter the context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        """Exit the context manager."""

    # -- engine management --------------------------------------------------

    def _get_engine(self, name: str) -> BaseEngine[Any]:
        """Return a cached engine instance for *name*.

        Args:
            name: Engine identifier (``"text"``, ``"images"``, ``"news"``, ``"videos"``).

        Returns:
            An initialised engine instance.

        Raises:
            GoogerException: If the engine name is unknown.

        """
        if name not in self._engine_cache:
            engine_cls = ENGINES.get(name)
            if engine_cls is None:
                available = ", ".join(sorted(ENGINES))
                msg = f"Unknown engine {name!r}. Available: {available}"
                raise GoogerException(msg)
            self._engine_cache[name] = engine_cls(http_client=self._http)
        return self._engine_cache[name]

    # -- internal search orchestrator ---------------------------------------

    def _search(
        self,
        engine_name: str,
        query: str | Query,
        *,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        page: int = 1,
        rank: bool = True,
        **kwargs: Any,
    ) -> list[BaseResult]:
        """Internal search dispatcher.

        Args:
            engine_name: Which engine to use.
            query: Search terms — either a string or a :class:`Query`.
            region: Locale code (e.g. ``"us-en"``, ``"ko-kr"``).
            safesearch: ``"on"``, ``"moderate"``, or ``"off"``.
            timelimit: Time filter shorthand (``"h"``, ``"d"``, ``"w"``, ``"m"``, ``"y"``).
            max_results: Maximum number of results to return.
            page: Starting page (1-based).
            rank: Whether to apply the relevance ranker.
            **kwargs: Engine-specific keyword arguments.

        Returns:
            List of result objects (e.g. :class:`TextResult`).

        Raises:
            GoogerException: On empty query.
            NoResultsException: When no results are found.

        """
        # Resolve Query objects
        query_str = str(query) if isinstance(query, Query) else query
        if not query_str or not query_str.strip():
            msg = "Search query must not be empty."
            raise GoogerException(msg)

        engine = self._get_engine(engine_name)

        # Remove keys that are handled at this level, not by the engine
        kwargs.pop("rank", None)

        # Perform multi-page search
        results = engine.search_pages(
            query=query_str,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            **kwargs,
        )

        if not results:
            msg = f"No results found for query: {query_str!r}"
            raise NoResultsException(msg)

        # Aggregate & deduplicate
        aggregator = ResultsAggregator({"href", "url", "image"})
        aggregator.extend(results)
        result_objects = aggregator.extract()

        # Rank
        if rank:
            result_objects = self._ranker.rank(result_objects, query_str)

        return result_objects[:max_results]

    # -- public search methods ----------------------------------------------

    def search(
        self,
        query: str | Query,
        *,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        page: int = 1,
        rank: bool = True,
    ) -> list[TextResult]:
        """Perform a Google web/text search.

        Args:
            query: Search terms (string or :class:`Query` object).
            region: Locale code (e.g. ``"us-en"``, ``"ko-kr"``).
            safesearch: Safe-search level (``"on"``, ``"moderate"``, ``"off"``).
            timelimit: Time filter (``"h"`` hour, ``"d"`` day, ``"w"`` week, ``"m"`` month, ``"y"`` year).
            max_results: Maximum number of results.  Defaults to 10.
            page: Starting page number.  Defaults to 1.
            rank: Apply relevance ranking.  Defaults to ``True``.

        Returns:
            List of :class:`TextResult` objects with ``title``, ``href``, ``body`` attributes.

        Raises:
            GoogerException: On invalid input.
            NoResultsException: When no results are found.

        Example::

            >>> results = Googer().search("python tutorial", max_results=5)
            >>> results[0].title
            'Python Tutorial'

        """
        return self._search(  # type: ignore[return-value]
            "text",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            page=page,
            rank=rank,
        )

    def images(
        self,
        query: str | Query,
        *,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        size: str | None = None,
        color: str | None = None,
        image_type: str | None = None,
        license_type: str | None = None,
    ) -> list[ImageResult]:
        """Perform a Google image search.

        Args:
            query: Search terms.
            region: Locale code.
            safesearch: Safe-search level.
            timelimit: Time filter.
            max_results: Maximum number of results.
            size: Image size filter (``"large"``, ``"medium"``, ``"icon"``).
            color: Color filter (``"color"``, ``"gray"``, ``"mono"``, ``"trans"``).
            image_type: Type filter (``"face"``, ``"photo"``, ``"clipart"``, ``"lineart"``, ``"animated"``).
            license_type: License filter (``"creative_commons"``, ``"commercial"``).

        Returns:
            List of :class:`ImageResult` objects with ``title``, ``image``,
            ``thumbnail``, ``url``, ``height``, ``width``, ``source`` attributes.

        """
        return self._search(  # type: ignore[return-value]
            "images",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            size=size,
            color=color,
            image_type=image_type,
            license_type=license_type,
        )

    def news(
        self,
        query: str | Query,
        *,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
    ) -> list[NewsResult]:
        """Perform a Google news search.

        Args:
            query: Search terms.
            region: Locale code.
            safesearch: Safe-search level.
            timelimit: Time filter.
            max_results: Maximum number of results.

        Returns:
            List of :class:`NewsResult` objects with ``title``, ``url``,
            ``body``, ``source``, ``date``, ``image`` attributes.

        """
        return self._search(  # type: ignore[return-value]
            "news",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
        )

    def videos(
        self,
        query: str | Query,
        *,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        duration: str | None = None,
    ) -> list[VideoResult]:
        """Perform a Google video search.

        Args:
            query: Search terms.
            region: Locale code.
            safesearch: Safe-search level.
            timelimit: Time filter.
            max_results: Maximum number of results.
            duration: Duration filter (``"short"``, ``"medium"``, ``"long"``).

        Returns:
            List of :class:`VideoResult` objects with ``title``, ``url``,
            ``body``, ``duration``, ``source``, ``date``, ``thumbnail`` attributes.

        """
        return self._search(  # type: ignore[return-value]
            "videos",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            duration=duration,
        )
