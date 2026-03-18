"""Google text/web search engine."""

from typing import Any, ClassVar

from ..config import (
    GOOGLE_TEXT_URL,
    TEXT_ELEMENTS_XPATH,
    TEXT_ITEMS_XPATH,
    TIMELIMIT_MAP,
)
from ..results import TextResult
from ..utils import extract_clean_url
from .base import BaseEngine


class GoogleTextEngine(BaseEngine[TextResult]):
    """Google web/text search engine.

    Parses the browser-rendered Google SERP using ``tF2Cxc`` divs
    which contain individual search results with titles, links,
    and snippets.
    """

    name: ClassVar[str] = "text"
    search_url: ClassVar[str] = GOOGLE_TEXT_URL
    result_type = TextResult  # type: ignore[assignment]
    items_xpath: ClassVar[str] = TEXT_ITEMS_XPATH
    elements_xpath: ClassVar[dict[str, str]] = dict(TEXT_ELEMENTS_XPATH)

    def build_params(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build GET parameters for a text search.

        Args:
            query: Search terms.
            region: Locale code.
            safesearch: Safe-search level.
            timelimit: Optional time filter (``h``, ``d``, ``w``, ``m``, ``y``).
            page: 1-based page number.

        Returns:
            Google query parameters dict.

        """
        params = self._build_base_params(query, region, safesearch, page)
        if timelimit and timelimit in TIMELIMIT_MAP:
            params["tbs"] = f"qdr:{TIMELIMIT_MAP[timelimit]}"
        return params

    def post_process(self, results: list[TextResult]) -> list[TextResult]:
        """Clean up Google redirect URLs and drop non-HTTP results."""
        cleaned: list[TextResult] = []
        for r in results:
            r.href = extract_clean_url(r.href)
            if r.title and r.href.startswith("http"):
                cleaned.append(r)
        return cleaned
