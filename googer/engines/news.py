"""Google news search engine."""

from typing import Any, ClassVar

from ..config import (
    GOOGLE_NEWS_URL,
    NEWS_ELEMENTS_XPATH,
    NEWS_ITEMS_XPATH,
    TBM_NEWS,
    TIMELIMIT_MAP,
)
from ..results import NewsResult
from ..utils import extract_clean_url
from .base import BaseEngine


class GoogleNewsEngine(BaseEngine[NewsResult]):
    """Google News search engine.

    Uses ``tbm=nws`` to retrieve news results from Google.
    """

    name: ClassVar[str] = "news"
    search_url: ClassVar[str] = GOOGLE_NEWS_URL
    result_type = NewsResult  # type: ignore[assignment]
    items_xpath: ClassVar[str] = NEWS_ITEMS_XPATH
    elements_xpath: ClassVar[dict[str, str]] = dict(NEWS_ELEMENTS_XPATH)

    def build_params(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build GET parameters for a news search.

        Args:
            query: Search terms.
            region: Locale code.
            safesearch: Safe-search level.
            timelimit: Time filter.
            page: 1-based page number.

        Returns:
            Google News query parameters.

        """
        params = self._build_base_params(query, region, safesearch, page)
        params["tbm"] = TBM_NEWS
        if timelimit and timelimit in TIMELIMIT_MAP:
            params["tbs"] = f"qdr:{TIMELIMIT_MAP[timelimit]}"
        return params

    def post_process(self, results: list[NewsResult]) -> list[NewsResult]:
        """Clean URLs and filter valid results."""
        cleaned: list[NewsResult] = []
        for r in results:
            r.url = extract_clean_url(r.url)
            if r.title:
                cleaned.append(r)
        return cleaned
