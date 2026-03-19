"""Brave Search engines for Googer.

Provides text, news, and video search via Brave Search.
Uses lightweight HTML scraping with no JavaScript rendering or API keys.
Brave's image search requires JavaScript and is not supported.
"""

import logging
import time
from random import uniform
from typing import Any, ClassVar

from ..config import (
    BRAVE_NEWS_ELEMENTS_XPATH,
    BRAVE_NEWS_ITEMS_XPATH,
    BRAVE_NEWS_URL,
    BRAVE_RESULTS_PER_PAGE,
    BRAVE_SAFESEARCH_MAP,
    BRAVE_TEXT_ELEMENTS_XPATH,
    BRAVE_TEXT_ITEMS_XPATH,
    BRAVE_TEXT_URL,
    BRAVE_TIMELIMIT_MAP,
    BRAVE_VIDEO_ELEMENTS_XPATH,
    BRAVE_VIDEO_ITEMS_XPATH,
    BRAVE_VIDEOS_URL,
    DEFAULT_MAX_RESULTS,
    DEFAULT_REGION,
    DEFAULT_SAFESEARCH,
)
from ..results import NewsResult, TextResult, VideoResult
from .base import BaseEngine

logger = logging.getLogger(__name__)


def _brave_region(region: str) -> str:
    """Convert region code to Brave country_string format.

    Brave uses a ``country`` query parameter (e.g. ``us``, ``gb``).
    Falls back to the first part of the region code.
    """
    if not region:
        return ""
    parts = region.lower().split("-", 1)
    return parts[0]


def _brave_lang(region: str) -> str:
    """Extract language code from region for Brave's ``lang`` parameter."""
    if not region:
        return "en"
    parts = region.lower().split("-", 1)
    return parts[1] if len(parts) > 1 else parts[0]


# ---------------------------------------------------------------------------
# Text search engine (HTML scraping)
# ---------------------------------------------------------------------------


class BraveTextEngine(BaseEngine[TextResult]):
    """Brave Search text engine.

    Scrapes Brave Search's server-rendered HTML result page.
    No API key or JavaScript rendering required.
    """

    name: ClassVar[str] = "brave-text"
    search_url: ClassVar[str] = BRAVE_TEXT_URL
    result_type = TextResult  # type: ignore[assignment]
    items_xpath: ClassVar[str] = BRAVE_TEXT_ITEMS_XPATH
    elements_xpath: ClassVar[dict[str, str]] = dict(BRAVE_TEXT_ELEMENTS_XPATH)

    def build_params(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build GET parameters for Brave text search."""
        params: dict[str, str] = {
            "q": query,
            "source": "web",
        }
        country = _brave_region(region)
        if country:
            params["country"] = country
        lang = _brave_lang(region)
        if lang:
            params["lang"] = lang
        safe = BRAVE_SAFESEARCH_MAP.get(safesearch.lower(), "moderate")
        params["safesearch"] = safe
        if timelimit and timelimit in BRAVE_TIMELIMIT_MAP:
            params["tf"] = BRAVE_TIMELIMIT_MAP[timelimit]
        if page > 1:
            params["offset"] = str(page - 1)
        return params

    def search_pages(
        self,
        query: str,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        **kwargs: Any,
    ) -> list[TextResult]:
        """Search with offset-based pagination."""
        all_results: list[TextResult] = []
        pages_needed = max((max_results + BRAVE_RESULTS_PER_PAGE - 1) // BRAVE_RESULTS_PER_PAGE, 1)

        for page in range(1, pages_needed + 1):
            if page > 1:
                delay = uniform(1.5, 3.0)
                logger.debug("Brave text: sleeping %.2fs between pages", delay)
                time.sleep(delay)

            batch = self.search(
                query=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                page=page,
                **kwargs,
            )
            if not batch:
                break
            all_results.extend(batch)
            if len(all_results) >= max_results:
                break

        return all_results[:max_results]

    def post_process(self, results: list[TextResult]) -> list[TextResult]:
        """Filter out results without titles or valid URLs."""
        return [r for r in results if r.title and r.href and r.href.startswith("http")]


# ---------------------------------------------------------------------------
# News search engine (HTML scraping)
# ---------------------------------------------------------------------------


class BraveNewsEngine(BaseEngine[NewsResult]):
    """Brave Search news engine.

    Scrapes Brave News search result page.
    """

    name: ClassVar[str] = "brave-news"
    search_url: ClassVar[str] = BRAVE_NEWS_URL
    result_type = NewsResult  # type: ignore[assignment]
    items_xpath: ClassVar[str] = BRAVE_NEWS_ITEMS_XPATH
    elements_xpath: ClassVar[dict[str, str]] = dict(BRAVE_NEWS_ELEMENTS_XPATH)

    def build_params(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build GET parameters for Brave news search."""
        params: dict[str, str] = {
            "q": query,
            "source": "news",
        }
        country = _brave_region(region)
        if country:
            params["country"] = country
        safe = BRAVE_SAFESEARCH_MAP.get(safesearch.lower(), "moderate")
        params["safesearch"] = safe
        if timelimit and timelimit in BRAVE_TIMELIMIT_MAP:
            params["tf"] = BRAVE_TIMELIMIT_MAP[timelimit]
        if page > 1:
            params["offset"] = str(page - 1)
        return params

    def search_pages(
        self,
        query: str,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        **kwargs: Any,
    ) -> list[NewsResult]:
        """Search with offset-based pagination."""
        all_results: list[NewsResult] = []
        pages_needed = max((max_results + BRAVE_RESULTS_PER_PAGE - 1) // BRAVE_RESULTS_PER_PAGE, 1)

        for page in range(1, pages_needed + 1):
            if page > 1:
                delay = uniform(1.5, 3.0)
                logger.debug("Brave news: sleeping %.2fs between pages", delay)
                time.sleep(delay)

            batch = self.search(
                query=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                page=page,
                **kwargs,
            )
            if not batch:
                break
            all_results.extend(batch)
            if len(all_results) >= max_results:
                break

        return all_results[:max_results]

    def post_process(self, results: list[NewsResult]) -> list[NewsResult]:
        """Filter out results without titles."""
        return [r for r in results if r.title and r.url and r.url.startswith("http")]


# ---------------------------------------------------------------------------
# Video search engine (HTML scraping)
# ---------------------------------------------------------------------------


class BraveVideosEngine(BaseEngine[VideoResult]):
    """Brave Search video engine.

    Scrapes Brave Video search result page.
    """

    name: ClassVar[str] = "brave-videos"
    search_url: ClassVar[str] = BRAVE_VIDEOS_URL
    result_type = VideoResult  # type: ignore[assignment]
    items_xpath: ClassVar[str] = BRAVE_VIDEO_ITEMS_XPATH
    elements_xpath: ClassVar[dict[str, str]] = dict(BRAVE_VIDEO_ELEMENTS_XPATH)

    def build_params(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build GET parameters for Brave video search."""
        params: dict[str, str] = {
            "q": query,
            "source": "videos",
        }
        country = _brave_region(region)
        if country:
            params["country"] = country
        safe = BRAVE_SAFESEARCH_MAP.get(safesearch.lower(), "moderate")
        params["safesearch"] = safe
        if timelimit and timelimit in BRAVE_TIMELIMIT_MAP:
            params["tf"] = BRAVE_TIMELIMIT_MAP[timelimit]
        if page > 1:
            params["offset"] = str(page - 1)
        return params

    def search_pages(
        self,
        query: str,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        **kwargs: Any,
    ) -> list[VideoResult]:
        """Search with offset-based pagination."""
        all_results: list[VideoResult] = []
        pages_needed = max((max_results + BRAVE_RESULTS_PER_PAGE - 1) // BRAVE_RESULTS_PER_PAGE, 1)

        for page in range(1, pages_needed + 1):
            if page > 1:
                delay = uniform(1.5, 3.0)
                logger.debug("Brave videos: sleeping %.2fs between pages", delay)
                time.sleep(delay)

            batch = self.search(
                query=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                page=page,
                **kwargs,
            )
            if not batch:
                break
            all_results.extend(batch)
            if len(all_results) >= max_results:
                break

        return all_results[:max_results]

    def post_process(self, results: list[VideoResult]) -> list[VideoResult]:
        """Filter out results without titles."""
        return [r for r in results if r.title and r.url and r.url.startswith("http")]
