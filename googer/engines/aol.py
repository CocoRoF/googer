"""AOL search engine for Googer.

Provides text search via AOL Search (Bing-powered).
Uses the same HTML structure as Yahoo Search. Outbound links may go
through Yahoo-style redirect URLs that are extracted during
post-processing.
"""

from typing import Any, ClassVar

from ..config import (
    AOL_TEXT_ELEMENTS_XPATH,
    AOL_TEXT_ITEMS_XPATH,
    AOL_TEXT_URL,
)
from ..results import TextResult
from ..utils import extract_yahoo_redirect_url
from .base import BaseEngine


class AolTextEngine(BaseEngine[TextResult]):
    """AOL text search engine.

    Scrapes AOL Search's server-rendered HTML result page.
    AOL is powered by Bing via the Yahoo platform.  Shares the same
    ``algo-sr`` HTML structure and redirect URL pattern as Yahoo.
    """

    name: ClassVar[str] = "aol-text"
    search_url: ClassVar[str] = AOL_TEXT_URL
    result_type = TextResult  # type: ignore[assignment]
    items_xpath: ClassVar[str] = AOL_TEXT_ITEMS_XPATH
    elements_xpath: ClassVar[dict[str, str]] = dict(AOL_TEXT_ELEMENTS_XPATH)
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
        """Build GET parameters for AOL text search."""
        params: dict[str, str] = {
            "q": query,
            "s_it": "aol-serp",
        }
        if page > 1:
            params["b"] = str((page - 1) * 10 + 1)
        return params

    def post_process(self, results: list[TextResult]) -> list[TextResult]:
        """Unwrap redirect URLs and drop non-HTTP results."""
        cleaned: list[TextResult] = []
        for r in results:
            r.href = extract_yahoo_redirect_url(r.href)
            if r.title and r.href.startswith("http"):
                cleaned.append(r)
        return cleaned
