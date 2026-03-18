"""Ecosia search engine for Googer.

Provides text search via Ecosia (Bing-powered, privacy-focused).
Uses lightweight HTML scraping with no JavaScript rendering or API keys.
"""

from typing import Any, ClassVar

from ..config import (
    ECOSIA_TEXT_ELEMENTS_XPATH,
    ECOSIA_TEXT_ITEMS_XPATH,
    ECOSIA_TEXT_URL,
)
from ..results import TextResult
from .base import BaseEngine


def _ecosia_lang(region: str) -> str:
    """Extract language code from region for Ecosia."""
    if not region:
        return "en"
    parts = region.lower().split("-", 1)
    return parts[1] if len(parts) > 1 else parts[0]


class EcosiaTextEngine(BaseEngine[TextResult]):
    """Ecosia text search engine.

    Scrapes Ecosia's server-rendered HTML result page.
    Ecosia is powered by Bing and returns clean, direct URLs.
    """

    name: ClassVar[str] = "ecosia-text"
    search_url: ClassVar[str] = ECOSIA_TEXT_URL
    result_type = TextResult  # type: ignore[assignment]
    items_xpath: ClassVar[str] = ECOSIA_TEXT_ITEMS_XPATH
    elements_xpath: ClassVar[dict[str, str]] = dict(ECOSIA_TEXT_ELEMENTS_XPATH)

    def build_params(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build GET parameters for Ecosia text search."""
        params: dict[str, str] = {"q": query}
        lang = _ecosia_lang(region)
        if lang:
            params["language"] = lang
        if page > 1:
            params["p"] = str(page - 1)
        return params

    def post_process(self, results: list[TextResult]) -> list[TextResult]:
        """Drop results without title or valid URL."""
        return [r for r in results if r.title and r.href.startswith("http")]
