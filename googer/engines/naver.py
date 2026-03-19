"""Naver search engine for Googer.

Provides text search via Naver (Korea's dominant search engine).
Naver uses heavily obfuscated CSS class names that change frequently,
so this engine uses structural patterns (external link order within
``fds-web-doc-root`` containers) rather than class-based XPaths for
element extraction.
"""

import logging
from typing import Any, ClassVar

from lxml import html as lxml_html

from ..config import NAVER_TEXT_ITEMS_XPATH, NAVER_TEXT_URL
from ..results import TextResult
from .base import BaseEngine

logger = logging.getLogger(__name__)


class NaverTextEngine(BaseEngine[TextResult]):
    """Naver text search engine with custom HTML parsing.

    Naver's SERP wraps each web result in a ``fds-web-doc-root`` div.
    Inside each div, the relevant ``<a>`` tags follow a consistent
    order regardless of CSS class names:

    1. **Breadcrumb** link — site name + URL path (first external ``<a>``)
    2. *Keep* bookmarks — ``#`` or ``keep.naver.com`` links (skipped)
    3. **Title** link — the actual result title (second external ``<a>``)
    4. **Description / sub-links** — remaining external ``<a>`` tags

    This engine overrides ``search()`` to perform custom extraction
    instead of relying on the generic XPath-based parser.
    """

    name: ClassVar[str] = "naver-text"
    search_url: ClassVar[str] = NAVER_TEXT_URL
    result_type = TextResult  # type: ignore[assignment]
    # Empty XPaths → self._parser is None; custom parsing below.
    items_xpath: ClassVar[str] = ""
    elements_xpath: ClassVar[dict[str, str]] = {}
    extra_headers: ClassVar[dict[str, str]] = {
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
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
        """Build GET parameters for Naver web search."""
        params: dict[str, str] = {
            "query": query,
            "where": "web",
        }
        if page > 1:
            params["start"] = str((page - 1) * 10 + 1)
        return params

    # -- custom search override ---------------------------------------------

    def search(
        self,
        query: str,
        region: str = "ko-kr",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        **kwargs: Any,
    ) -> list[TextResult]:
        """Execute a Naver web search with custom HTML parsing."""
        params = self.build_params(
            query=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
            **kwargs,
        )
        try:
            resp = self._http.client.get(self.search_url, params=params)
        except Exception:  # noqa: BLE001
            logger.exception("Naver request failed")
            return []

        if resp.status_code != 200:  # noqa: PLR2004
            logger.warning("Naver returned status %s", resp.status_code)
            return []

        return self._parse_naver(resp.text)

    # -- internal parsing ---------------------------------------------------

    @staticmethod
    def _parse_naver(html_text: str) -> list[TextResult]:
        """Extract results from Naver SERP HTML.

        Identifies external links (non-Naver, non-bookmark) inside each
        ``fds-web-doc-root`` item and maps them to title / URL / body
        by position.
        """
        tree = lxml_html.fromstring(html_text)
        items = tree.xpath(NAVER_TEXT_ITEMS_XPATH)
        results: list[TextResult] = []

        for item in items:
            # Collect <a> tags pointing to external (non-Naver) URLs
            external_links = [
                a
                for a in item.xpath(".//a")
                if a.get("href", "").startswith("http")
                and "naver.com" not in a.get("href", "")
                and a.get("href", "") != "#"
            ]
            if not external_links:
                continue

            url = external_links[0].get("href", "")

            # Second external link = title (first is breadcrumb)
            if len(external_links) >= 2:  # noqa: PLR2004
                title = external_links[1].text_content().strip()
            else:
                title = external_links[0].text_content().strip()

            # Description: longest text among remaining links
            desc_texts = [
                a.text_content().strip()
                for a in external_links[2:]
                if a.text_content().strip()
            ]
            body = max(desc_texts, key=len) if desc_texts else ""

            if title and url:
                results.append(TextResult(title=title, href=url, body=body))

        logger.debug("Naver: parsed %d results from %d items", len(results), len(items))
        return results
