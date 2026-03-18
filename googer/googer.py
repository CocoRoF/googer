"""Main Googer class — the primary public interface.

This module provides the :class:`Googer` class, which is the single
entry point for all search functionality.  It manages HTTP sessions,
delegates to the appropriate engine, aggregates results, and applies
ranking.

Googer supports multiple search providers (DuckDuckGo, Brave, Google)
with automatic fallback and optional concurrent multi-engine search.

Features beyond DDGS:

* **Multi-engine**: DuckDuckGo, Brave Search, and Google as backends.
* **Concurrent multi-engine search**: ``engine="multi"`` queries all providers
  in parallel and merges results with cross-engine frequency boosting.
* **Suggestions**: Autocomplete via DuckDuckGo.
* **Instant Answers**: Structured answers via DuckDuckGo Instant Answer API.
* **Caching**: TTL-based in-memory cache to avoid redundant queries.
* **Provider metadata**: Every result carries a ``provider`` field.

Example::

    from googer import Googer

    # Default: DuckDuckGo with fallback to Brave, then Google
    results = Googer().search("python programming")

    # Multi-engine concurrent search (all engines at once)
    results = Googer(engine="multi").search("python")

    # Autocomplete suggestions
    suggestions = Googer().suggest("python prog")

    # Instant answers
    answer = Googer().answers("python programming language")

"""

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Literal
from types import TracebackType

from .cache import SearchCache
from .config import (
    DDG_ANSWER_URL,
    DDG_SUGGEST_URL,
    DEFAULT_CACHE_TTL,
    DEFAULT_ENGINE,
    DEFAULT_MAX_RESULTS,
    DEFAULT_REGION,
    DEFAULT_SAFESEARCH,
    DEFAULT_TIMEOUT,
    ENGINE_FALLBACK_ORDER,
)
from .engines import ENGINES
from .engines.base import BaseEngine
from .exceptions import (
    GoogerException,
    HttpException,
    NoResultsException,
    RateLimitException,
    TimeoutException,
)
from .http_client import HttpClient
from .query_builder import Query
from .ranker import Ranker
from .results import (
    AnswerResult,
    BaseResult,
    ImageResult,
    NewsResult,
    ResultsAggregator,
    TextResult,
    VideoResult,
)
from .utils import expand_proxy_alias

logger = logging.getLogger(__name__)

# Providers that support each search type
_MULTI_PROVIDERS: dict[str, list[str]] = {
    "text": ["duckduckgo", "brave", "google", "ecosia", "yahoo", "naver"],
    "images": ["duckduckgo", "google"],
    "news": ["duckduckgo", "brave", "google"],
    "videos": ["duckduckgo", "brave", "google"],
}


class Googer:
    """Multi-engine search client — search the web, images, news, and videos.

    Supports DuckDuckGo (default), Brave Search, and Google as search
    providers, with automatic fallback and concurrent multi-engine mode.

    Unlike DDGS, Googer offers:

    * **3 search engines** — DuckDuckGo, Brave Search, Google
    * **Multi-engine mode** — ``engine="multi"`` for concurrent search + merge
    * **Suggestions** — autocomplete via ``suggest()``
    * **Instant Answers** — structured answers via ``answers()``
    * **Result caching** — TTL-based in-memory cache
    * **Provider metadata** — every result has a ``provider`` field
    * **Cross-engine ranking** — results from multiple engines are frequency-boosted
    * **Query builder** — fluent ``Query("term").site("x.com").filetype("pdf")``

    Args:
        proxy: Proxy URL (``http://``, ``https://``, ``socks5://``).
            Also reads from ``GOOGER_PROXY`` env var.
            Special shorthand ``"tb"`` expands to the Tor Browser SOCKS5 proxy.
        timeout: Request timeout in seconds.  Defaults to 10.
        verify: SSL verification — ``True``, ``False``, or path to a PEM file.
            Ignored when *backend* is ``"browser"``.
        max_retries: Maximum number of retry attempts per request.
        backend: Client backend for Google searches:

            * ``"http"`` (default) — lightweight HTTP-only mode using primp.
            * ``"browser"`` — Chromium via patchright for JS rendering.
        headless: Run browser headlessly.  Defaults to ``True``.
        engine: Search provider to use:

            * ``"auto"`` (default) — tries DuckDuckGo → Brave → Google.
            * ``"multi"`` — **concurrent** search across all providers, merged.
            * ``"duckduckgo"`` — DuckDuckGo only.
            * ``"brave"`` — Brave Search only.
            * ``"google"`` — Google only.
        cache_ttl: Cache time-to-live in seconds.  0 disables caching.

    Example::

        >>> from googer import Googer
        >>> with Googer(engine="multi") as g:
        ...     results = g.search("python", max_results=10)
        ...     for r in results:
        ...         print(f"[{r.provider}] {r.title}")

    """

    def __init__(
        self,
        proxy: str | None = None,
        timeout: int | None = DEFAULT_TIMEOUT,
        *,
        verify: bool | str = True,
        max_retries: int = 3,
        backend: Literal["browser", "http"] = "http",
        headless: bool = True,
        engine: Literal["auto", "multi", "duckduckgo", "brave", "google", "ecosia", "yahoo", "aol", "naver"] = DEFAULT_ENGINE,
        cache_ttl: int = DEFAULT_CACHE_TTL,
    ) -> None:
        resolved_proxy = expand_proxy_alias(proxy) or os.environ.get("GOOGER_PROXY")
        self._backend = backend
        self._engine_preference = engine

        # HTTP client — always available
        self._http_client = HttpClient(
            proxy=resolved_proxy,
            timeout=timeout,
            verify=verify,
            max_retries=max_retries,
        )

        # Browser client — lazily initialised for Google browser backend
        self._browser_kwargs: dict[str, Any] = {
            "proxy": resolved_proxy,
            "timeout": timeout,
            "headless": headless,
        }
        self._browser_client: Any = None

        self._engine_cache: dict[str, BaseEngine[Any]] = {}
        self._ranker = Ranker()
        self._cache = SearchCache(ttl=cache_ttl) if cache_ttl > 0 else None

    # -- lazy browser client ------------------------------------------------

    def _get_browser_client(self) -> Any:
        """Lazily create and return a BrowserClient for Google."""
        if self._browser_client is None:
            from .browser_client import BrowserClient  # noqa: PLC0415

            self._browser_client = BrowserClient(**self._browser_kwargs)
        return self._browser_client

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
        """Exit the context manager and clean up resources."""
        self.close()

    def close(self) -> None:
        """Release underlying client resources (browser, HTTP session)."""
        if hasattr(self._http_client, "close"):
            self._http_client.close()
        if self._browser_client is not None and hasattr(self._browser_client, "close"):
            self._browser_client.close()

    # -- cache management ---------------------------------------------------

    def clear_cache(self) -> None:
        """Clear the search results cache."""
        if self._cache:
            self._cache.clear()

    # -- engine management --------------------------------------------------

    def _get_client_for_provider(self, provider: str) -> Any:
        """Return the appropriate HTTP client for *provider*."""
        if provider == "google" and self._backend == "browser":
            return self._get_browser_client()
        return self._http_client

    def _get_engine(self, provider: str, search_type: str) -> BaseEngine[Any]:
        """Return a cached engine instance for *provider* and *search_type*."""
        key = f"{provider}.{search_type}"
        if key not in self._engine_cache:
            provider_engines = ENGINES.get(provider)
            if provider_engines is None:
                available = ", ".join(sorted(ENGINES))
                msg = f"Unknown provider {provider!r}. Available: {available}"
                raise GoogerException(msg)
            engine_cls = provider_engines.get(search_type)
            if engine_cls is None:
                available = ", ".join(sorted(provider_engines))
                msg = f"Provider {provider!r} has no {search_type!r} engine. Available: {available}"
                raise GoogerException(msg)
            client = self._get_client_for_provider(provider)
            self._engine_cache[key] = engine_cls(http_client=client)
        return self._engine_cache[key]

    def _resolve_providers(self, engine_override: str | None = None) -> list[str]:
        """Return the ordered list of providers to try."""
        engine = engine_override or self._engine_preference
        if engine == "auto":
            return list(ENGINE_FALLBACK_ORDER)
        if engine == "multi":
            return ["multi"]
        return [engine]

    # -- internal search orchestrator ---------------------------------------

    def _search_single_provider(
        self,
        provider: str,
        search_type: str,
        query_str: str,
        *,
        region: str,
        safesearch: str,
        timelimit: str | None,
        max_results: int,
        **kwargs: Any,
    ) -> list[BaseResult]:
        """Execute search on a single provider and tag results."""
        engine_obj = self._get_engine(provider, search_type)
        results = engine_obj.search_pages(
            query=query_str,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            **kwargs,
        )
        # Tag results with provider
        for r in results:
            r.provider = provider
        return results

    def _search_multi(
        self,
        search_type: str,
        query_str: str,
        *,
        region: str,
        safesearch: str,
        timelimit: str | None,
        max_results: int,
        rank: bool,
        **kwargs: Any,
    ) -> list[BaseResult]:
        """Concurrent multi-engine search — queries all compatible providers.

        Results are merged, deduplicated, and ranked with cross-engine
        frequency boosting.
        """
        providers = _MULTI_PROVIDERS.get(search_type, [])
        if not providers:
            msg = f"No providers support search type {search_type!r}"
            raise GoogerException(msg)

        all_results: list[BaseResult] = []

        def _do_search(provider: str) -> list[BaseResult]:
            try:
                return self._search_single_provider(
                    provider,
                    search_type,
                    query_str,
                    region=region,
                    safesearch=safesearch,
                    timelimit=timelimit,
                    max_results=max_results,
                    **kwargs,
                )
            except (RateLimitException, TimeoutException, HttpException, GoogerException) as exc:
                logger.warning("Multi-engine: provider '%s' failed: %s", provider, exc)
                return []

        with ThreadPoolExecutor(max_workers=len(providers)) as executor:
            futures = {executor.submit(_do_search, p): p for p in providers}
            for future in as_completed(futures):
                provider_name = futures[future]
                try:
                    results = future.result()
                    if results:
                        logger.info(
                            "Multi-engine: '%s' returned %d results",
                            provider_name,
                            len(results),
                        )
                        all_results.extend(results)
                except Exception:  # noqa: BLE001
                    logger.exception("Multi-engine: unexpected error from '%s'", provider_name)

        if not all_results:
            msg = f"No results found from any provider for query: {query_str!r}"
            raise NoResultsException(msg)

        # Aggregate & deduplicate with cross-engine frequency boosting
        aggregator = ResultsAggregator({"href", "url", "image"})
        aggregator.extend(all_results)
        result_objects = aggregator.extract()

        if rank:
            result_objects = self._ranker.rank(result_objects, query_str)

        return result_objects[:max_results]

    def _search(
        self,
        search_type: str,
        query: str | Query,
        *,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        page: int = 1,  # noqa: ARG002
        rank: bool = True,
        engine: str | None = None,
        **kwargs: Any,
    ) -> list[BaseResult]:
        """Internal search dispatcher with automatic fallback.

        Tries each provider in order.  On transient failures (rate limit,
        timeout, HTTP errors) the next provider is attempted.
        """
        query_str = str(query) if isinstance(query, Query) else query
        if not query_str or not query_str.strip():
            msg = "Search query must not be empty."
            raise GoogerException(msg)

        # Check cache
        cache_key = None
        if self._cache:
            cache_key = SearchCache.make_key(
                search_type=search_type,
                query=query_str,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_results=max_results,
                engine=engine or self._engine_preference,
            )
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.info("Returning cached results for query: %r", query_str)
                return cached  # type: ignore[return-value]

        providers = self._resolve_providers(engine)

        # Remove keys handled at this level
        kwargs.pop("rank", None)
        kwargs.pop("engine", None)

        # Multi-engine concurrent search
        if providers == ["multi"]:
            result_objects = self._search_multi(
                search_type,
                query_str,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_results=max_results,
                rank=rank,
                **kwargs,
            )
            if self._cache and cache_key:
                self._cache.set(cache_key, result_objects)
            return result_objects

        # Sequential fallback search
        last_exception: Exception | None = None

        for provider in providers:
            try:
                results = self._search_single_provider(
                    provider,
                    search_type,
                    query_str,
                    region=region,
                    safesearch=safesearch,
                    timelimit=timelimit,
                    max_results=max_results,
                    **kwargs,
                )

                if not results:
                    logger.info(
                        "Provider '%s' returned no results for query: %r",
                        provider,
                        query_str,
                    )
                    continue

                # Aggregate & deduplicate
                aggregator = ResultsAggregator({"href", "url", "image"})
                aggregator.extend(results)
                result_objects = aggregator.extract()

                if rank:
                    result_objects = self._ranker.rank(result_objects, query_str)

                logger.info(
                    "Provider '%s' returned %d results for query: %r",
                    provider,
                    len(result_objects),
                    query_str,
                )
                final = result_objects[:max_results]

                if self._cache and cache_key:
                    self._cache.set(cache_key, final)

                return final

            except (RateLimitException, TimeoutException, HttpException) as exc:
                logger.warning(
                    "Provider '%s' failed for '%s': %s. Trying next provider...",
                    provider,
                    search_type,
                    exc,
                )
                last_exception = exc
                continue

        if last_exception:
            raise last_exception

        msg = f"No results found for query: {query_str!r}"
        raise NoResultsException(msg)

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
        engine: str | None = None,
    ) -> list[TextResult]:
        """Perform a web/text search.

        Args:
            query: Search terms (string or :class:`Query` object).
            region: Locale code (e.g. ``"us-en"``, ``"ko-kr"``).
            safesearch: Safe-search level (``"on"``, ``"moderate"``, ``"off"``).
            timelimit: Time filter (``"h"`` hour, ``"d"`` day, ``"w"`` week,
                ``"m"`` month, ``"y"`` year).
            max_results: Maximum number of results.  Defaults to 10.
            page: Starting page number.  Defaults to 1.
            rank: Apply relevance ranking.  Defaults to ``True``.
            engine: Override the default engine for this call
                (``"auto"``, ``"multi"``, ``"duckduckgo"``, ``"brave"``, ``"google"``).

        Returns:
            List of :class:`TextResult` objects with ``title``, ``href``,
            ``body``, ``provider`` attributes.

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
            engine=engine,
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
        engine: str | None = None,
    ) -> list[ImageResult]:
        """Perform an image search.

        Args:
            query: Search terms.
            region: Locale code.
            safesearch: Safe-search level.
            timelimit: Time filter.
            max_results: Maximum number of results.
            size: Image size filter (``"large"``, ``"medium"``, ``"icon"``).
            color: Color filter (``"color"``, ``"gray"``, ``"mono"``, ``"trans"``).
            image_type: Type filter.
            license_type: License filter.
            engine: Override the default engine for this call.

        Returns:
            List of :class:`ImageResult` objects.

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
            engine=engine,
        )

    def news(
        self,
        query: str | Query,
        *,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        engine: str | None = None,
    ) -> list[NewsResult]:
        """Perform a news search.

        Args:
            query: Search terms.
            region: Locale code.
            safesearch: Safe-search level.
            timelimit: Time filter.
            max_results: Maximum number of results.
            engine: Override the default engine for this call.

        Returns:
            List of :class:`NewsResult` objects.

        """
        return self._search(  # type: ignore[return-value]
            "news",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            engine=engine,
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
        engine: str | None = None,
    ) -> list[VideoResult]:
        """Perform a video search.

        Args:
            query: Search terms.
            region: Locale code.
            safesearch: Safe-search level.
            timelimit: Time filter.
            max_results: Maximum number of results.
            duration: Duration filter (``"short"``, ``"medium"``, ``"long"``).
            engine: Override the default engine for this call.

        Returns:
            List of :class:`VideoResult` objects.

        """
        return self._search(  # type: ignore[return-value]
            "videos",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            duration=duration,
            engine=engine,
        )

    # -- suggestions --------------------------------------------------------

    def suggest(
        self,
        query: str,
        *,
        region: str = DEFAULT_REGION,
    ) -> list[str]:
        """Get autocomplete suggestions for a partial query.

        Uses the DuckDuckGo autocomplete API to return search suggestions.

        Args:
            query: Partial search query.
            region: Locale code for regional suggestions.

        Returns:
            List of suggestion strings.

        Example::

            >>> Googer().suggest("python prog")
            ['python programiz', 'python programming', ...]

        """
        if not query or not query.strip():
            return []

        cache_key = None
        if self._cache:
            cache_key = SearchCache.make_key(type="suggest", query=query, region=region)
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached  # type: ignore[return-value]

        try:
            resp = self._http_client.get(
                DDG_SUGGEST_URL,
                params={"q": query, "type": "list", "kl": region},
            )
            if not resp or not resp.ok:
                return []

            data = json.loads(resp.text)
            # DDG returns [query, [suggestions...]]
            suggestions = data[1] if isinstance(data, list) and len(data) > 1 else []
            if self._cache and cache_key:
                self._cache.set(cache_key, suggestions)
            return suggestions  # type: ignore[return-value]

        except Exception:  # noqa: BLE001
            logger.exception("Suggestions request failed")
            return []

    # -- instant answers ----------------------------------------------------

    def answers(
        self,
        query: str,
    ) -> AnswerResult | None:
        """Get an instant answer for a query.

        Uses the DuckDuckGo Instant Answer API to return structured
        information (abstract, related topics, source URL).

        Args:
            query: Search query for instant answer.

        Returns:
            An :class:`AnswerResult` object, or ``None`` if no answer available.

        Example::

            >>> answer = Googer().answers("python programming language")
            >>> answer.abstract
            'Python is a high-level, general-purpose programming language...'
            >>> answer.url
            'https://en.wikipedia.org/wiki/Python_(programming_language)'

        """
        if not query or not query.strip():
            return None

        cache_key = None
        if self._cache:
            cache_key = SearchCache.make_key(type="answer", query=query)
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached  # type: ignore[return-value]

        try:
            resp = self._http_client.get(
                DDG_ANSWER_URL,
                params={
                    "q": query,
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1",
                },
            )
            if not resp or not resp.ok:
                return None

            data = json.loads(resp.text)
            abstract = data.get("Abstract", "")
            answer_text = data.get("Answer", "")

            if not abstract and not answer_text:
                return None

            # Extract related topics
            related: list[dict[str, str]] = []
            for topic in data.get("RelatedTopics", []):
                if "Text" in topic:
                    related.append({
                        "text": topic.get("Text", ""),
                        "url": topic.get("FirstURL", ""),
                    })

            result = AnswerResult(
                heading=data.get("Heading", ""),
                abstract=abstract,
                url=data.get("AbstractURL", ""),
                source=data.get("AbstractSource", ""),
                answer=answer_text,
                answer_type=data.get("Type", ""),
                image=data.get("Image", ""),
                related=related if related else None,
            )

            if self._cache and cache_key:
                self._cache.set(cache_key, result)

            return result

        except Exception:  # noqa: BLE001
            logger.exception("Answers request failed")
            return None
