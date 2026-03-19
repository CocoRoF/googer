"""Yahoo search engine for Googer.

Provides text search via Yahoo Search (Bing-powered).
Uses lightweight HTML scraping with no JavaScript rendering or API keys.
Yahoo wraps outbound URLs in redirect links that are extracted
during post-processing.
"""

from typing import Any, ClassVar

from ..config import (
    YAHOO_TEXT_ELEMENTS_XPATH,
    YAHOO_TEXT_ITEMS_XPATH,
    YAHOO_TEXT_URL,
)
from ..results import TextResult
from ..utils import extract_yahoo_redirect_url
from .base import BaseEngine


class YahooTextEngine(BaseEngine[TextResult]):
    """Yahoo text search engine.

    Scrapes Yahoo Search's server-rendered HTML result page.
    Yahoo is powered by Bing.  Outbound links go through a redirect
    (``r.search.yahoo.com``) which is unwrapped in :meth:`post_process`.
    """

    name: ClassVar[str] = "yahoo-text"
    search_url: ClassVar[str] = YAHOO_TEXT_URL
    result_type = TextResult  # type: ignore[assignment]
    items_xpath: ClassVar[str] = YAHOO_TEXT_ITEMS_XPATH
    elements_xpath: ClassVar[dict[str, str]] = dict(YAHOO_TEXT_ELEMENTS_XPATH)
    extra_headers: ClassVar[dict[str, str]] = {
        "Accept-Language": "en-US,en;q=0.9",
    }

    def build_params(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build GET parameters for Yahoo text search."""
        params: dict[str, str] = {
            "p": query,
            "ei": "UTF-8",
        }
        if page > 1:
            params["b"] = str((page - 1) * 10 + 1)
        return params

    def post_process(self, results: list[TextResult]) -> list[TextResult]:
        """Unwrap Yahoo redirect URLs and drop non-HTTP results."""
        cleaned: list[TextResult] = []
        for r in results:
            r.href = extract_yahoo_redirect_url(r.href)
            if r.title and r.href.startswith("http"):
                cleaned.append(r)
        return cleaned
