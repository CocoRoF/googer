"""Brave Search engines for Googer.

Provides text, image, news, and video search via Brave Search.
Uses lightweight HTML scraping with no JavaScript rendering or API keys.
"""

import base64
import logging
import re
import time
from random import uniform
from typing import Any, ClassVar

from lxml import html as lxml_html

from ..config import (
    BRAVE_IMAGES_URL,
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
from ..results import ImageResult, NewsResult, TextResult, VideoResult
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


def _decode_brave_image_url(proxy_url: str) -> str:
    """Decode the original image URL from Brave's proxy URL.

    Brave proxies images through ``imgs.search.brave.com`` and encodes
    the original URL as base64 segments after ``/g:ce/``.
    """
    if "/g:ce/" not in proxy_url:
        return proxy_url
    b64_part = proxy_url.split("/g:ce/")[1]
    b64_clean = "".join(b64_part.split("/"))
    padding = 4 - len(b64_clean) % 4
    if padding != 4:
        b64_clean += "=" * padding
    try:
        return base64.b64decode(b64_clean).decode("utf-8")
    except Exception:  # noqa: BLE001
        return proxy_url


# ---------------------------------------------------------------------------
# Image search engine (HTML scraping)
# ---------------------------------------------------------------------------


class BraveImagesEngine(BaseEngine[ImageResult]):
    """Brave Search image engine.

    Scrapes Brave Image search's server-rendered HTML page.
    Extracts thumbnail, original image URL (base64 decoded), title, and source.
    """

    name: ClassVar[str] = "brave-images"
    search_url: ClassVar[str] = BRAVE_IMAGES_URL
    result_type = ImageResult  # type: ignore[assignment]

    def build_params(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build GET parameters for Brave image search."""
        params: dict[str, str] = {
            "q": query,
            "source": "images",
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
    ) -> list[ImageResult]:
        """Fetch image results by scraping Brave's image search HTML."""
        params = self.build_params(
            query=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=1,
        )
        try:
            resp = self._http.get(self.search_url, params=params)
        except Exception:
            logger.exception("Brave images request failed")
            return []

        if not resp or not resp.ok:
            return []

        try:
            tree = lxml_html.fromstring(resp.text)
        except Exception:  # noqa: BLE001
            logger.warning("Brave images: failed to parse HTML")
            return []

        buttons = tree.xpath('//button[contains(@class, "image-result")]')
        if not buttons:
            logger.debug("Brave images: no image-result buttons found")
            return []

        all_results: list[ImageResult] = []
        for btn in buttons:
            imgs = btn.xpath('.//div[contains(@class, "image-wrapper")]//img')
            if not imgs:
                continue

            thumbnail = imgs[0].get("src", "")
            alt_title = imgs[0].get("alt", "")

            # Decode original image URL from Brave proxy
            image_url = _decode_brave_image_url(thumbnail)

            # Title from metadata span (more complete) or img alt
            title_spans = btn.xpath('.//span[contains(@class, "image-metadata-title")]')
            title = title_spans[0].text_content().strip() if title_spans else alt_title

            # Source domain
            source_spans = btn.xpath('.//span[contains(@class, "image-metadata-source")]')
            source = source_spans[0].text_content().strip() if source_spans else ""

            # Dimensions from button style
            style = btn.get("style", "")
            w_match = re.search(r"--width:\s*(\d+)", style)
            h_match = re.search(r"--height:\s*(\d+)", style)
            width = w_match.group(1) if w_match else ""
            height = h_match.group(1) if h_match else ""

            # Build source page URL from domain
            url = f"https://{source}" if source and not source.startswith("http") else source

            all_results.append(ImageResult(
                title=title,
                image=image_url,
                thumbnail=thumbnail,
                url=url,
                height=height,
                width=width,
                source=source,
            ))

            if len(all_results) >= max_results:
                break

        return all_results[:max_results]

    def post_process(self, results: list[ImageResult]) -> list[ImageResult]:
        """Filter out results without images."""
        return [r for r in results if r.image and r.title]


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
