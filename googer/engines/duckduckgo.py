"""DuckDuckGo search engines for Googer.

Provides text, image, news, and video search via DuckDuckGo.
Text search uses the lightweight HTML form endpoint; media
searches use DuckDuckGo's JSON API with VQD token authentication.
"""

import json
import logging
import re
import time
from random import uniform
from typing import Any, ClassVar
from urllib.parse import parse_qs, unquote, urlparse

from lxml import html as lxml_html

from ..config import (
    DDG_IMAGES_URL,
    DDG_NEWS_URL,
    DDG_SAFESEARCH_MAP,
    DDG_TEXT_ELEMENTS_XPATH,
    DDG_TEXT_ITEMS_XPATH,
    DDG_TEXT_URL,
    DDG_TIMELIMIT_MAP,
    DDG_VIDEOS_URL,
    DDG_VQD_URL,
    DEFAULT_MAX_RESULTS,
    DEFAULT_REGION,
    DEFAULT_SAFESEARCH,
)
from ..exceptions import GoogerException
from ..results import ImageResult, NewsResult, TextResult, VideoResult
from .base import BaseEngine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VQD_PATTERNS = (
    re.compile(r'vqd="([^"]+)"'),
    re.compile(r"vqd='([^']+)'"),
    re.compile(r"vqd=([\d]+-[\d]+-[^&\"']+)"),
)


def _extract_ddg_url(raw_url: str) -> str:
    """Extract actual URL from DuckDuckGo redirect wrapper."""
    if not raw_url:
        return ""
    if "uddg=" in raw_url:
        url = raw_url if raw_url.startswith("http") else f"https:{raw_url}"
        parsed = urlparse(url)
        uddg = parse_qs(parsed.query).get("uddg")
        if uddg:
            return unquote(uddg[0])
    return unquote(raw_url) if raw_url else ""


def _get_vqd(http_client: Any, query: str) -> str:
    """Obtain a VQD token required for DuckDuckGo API searches."""
    # Use x-vqd-accept header to request VQD token in response
    http_client.update_headers({"x-vqd-accept": "1"})
    resp = http_client.get(DDG_VQD_URL, params={"q": query})
    if not resp or not resp.ok:
        msg = "Failed to reach DuckDuckGo for search token"
        raise GoogerException(msg)

    # Try response headers first (preferred method)
    vqd = resp.headers.get("x-vqd-4", "")
    if vqd:
        return vqd

    # Fallback: extract from HTML body
    for pattern in _VQD_PATTERNS:
        match = pattern.search(resp.text)
        if match:
            return match.group(1)

    msg = "Could not extract VQD token from DuckDuckGo response"
    raise GoogerException(msg)


def _ddg_region(region: str) -> str:
    """Convert region code to DuckDuckGo kl format."""
    if not region or region == "us-en":
        return "wt-wt"
    return region


# ---------------------------------------------------------------------------
# Text search engine (HTML form)
# ---------------------------------------------------------------------------


class DuckDuckGoTextEngine(BaseEngine[TextResult]):
    """DuckDuckGo text search via HTML form.

    Posts to ``html.duckduckgo.com/html/`` and parses the lightweight
    HTML response.  No JavaScript rendering or API keys required.
    """

    name: ClassVar[str] = "ddg-text"
    search_url: ClassVar[str] = DDG_TEXT_URL
    search_method: ClassVar[str] = "POST"
    result_type = TextResult  # type: ignore[assignment]
    items_xpath: ClassVar[str] = DDG_TEXT_ITEMS_XPATH
    elements_xpath: ClassVar[dict[str, str]] = dict(DDG_TEXT_ELEMENTS_XPATH)
    extra_headers: ClassVar[dict[str, str]] = {
        "Referer": "https://html.duckduckgo.com/",
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
        """Build POST form data for DuckDuckGo text search."""
        params: dict[str, str] = {
            "q": query,
            "kl": _ddg_region(region),
            "kp": DDG_SAFESEARCH_MAP.get(safesearch.lower(), "-1"),
        }
        if timelimit and timelimit in DDG_TIMELIMIT_MAP:
            params["df"] = DDG_TIMELIMIT_MAP[timelimit]
        return params

    def search_pages(
        self,
        query: str,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        **kwargs: Any,  # noqa: ARG002
    ) -> list[TextResult]:
        """Search with form-based pagination.

        DDG's HTML interface uses hidden form fields for pagination
        rather than offset parameters, so we extract the "Next" form
        data from each response.
        """
        all_results: list[TextResult] = []
        payload = self.build_params(query, region, safesearch, timelimit)
        max_pages = max((max_results + 20) // 20, 1)

        for page_num in range(max_pages):
            if page_num > 0:
                delay = uniform(1.0, 2.5)
                logger.debug("DDG text: sleeping %.2fs between pages", delay)
                time.sleep(delay)

            try:
                resp = self._http.post(self.search_url, data=payload)
            except Exception:  # noqa: BLE001
                logger.exception("DDG text request failed on page %d", page_num + 1)
                break

            if not resp or not resp.ok:
                logger.warning("DDG text: bad response status %s", resp.status_code if resp else "None")
                break

            if self._parser is None:
                break

            results = self._parser.parse(resp.text, self.result_type)  # type: ignore[arg-type]
            results = self.post_process(results)
            if not results:
                break

            all_results.extend(results)
            if len(all_results) >= max_results:
                break

            # Extract next page form data
            next_payload = self._extract_next_form(resp.text)
            if not next_payload:
                break
            payload = next_payload

        return all_results[:max_results]

    def post_process(self, results: list[TextResult]) -> list[TextResult]:
        """Clean DDG redirect URLs and drop non-HTTP results."""
        cleaned: list[TextResult] = []
        for r in results:
            r.href = _extract_ddg_url(r.href)
            if r.title and r.href and r.href.startswith("http"):
                cleaned.append(r)
        return cleaned

    @staticmethod
    def _extract_next_form(html_text: str) -> dict[str, str] | None:
        """Extract hidden form fields from the 'Next' page button."""
        try:
            tree = lxml_html.fromstring(html_text)
            forms = tree.xpath("//form[.//input[@value='Next']]")
            if not forms:
                return None
            inputs = forms[0].xpath(".//input[@type='hidden']")
            form_data = {
                inp.get("name"): inp.get("value", "")
                for inp in inputs
                if inp.get("name")
            }
            return form_data if form_data else None
        except Exception:  # noqa: BLE001
            return None


# ---------------------------------------------------------------------------
# Image search engine (JSON API)
# ---------------------------------------------------------------------------


class DuckDuckGoImagesEngine(BaseEngine[ImageResult]):
    """DuckDuckGo image search via JSON API.

    Obtains a VQD token from the main DuckDuckGo page, then queries
    the ``/i.js`` endpoint for paginated JSON image results.
    """

    name: ClassVar[str] = "ddg-images"
    search_url: ClassVar[str] = DDG_IMAGES_URL
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
        """Not used directly — search_pages handles params."""
        return {}

    def search_pages(
        self,
        query: str,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        **kwargs: Any,
    ) -> list[ImageResult]:
        """Fetch image results from DDG JSON API with pagination."""
        vqd = _get_vqd(self._http, query)
        kp_val = DDG_SAFESEARCH_MAP.get(safesearch.lower(), "-1")

        # Set required headers for DDG API authentication
        self._http.update_headers({
            "Referer": "https://duckduckgo.com/",
            "x-vqd-4": vqd,
        })

        params: dict[str, str] = {
            "q": query,
            "o": "json",
            "l": _ddg_region(region),
            "p": kp_val,
            "f": ",,,,,",
            "s": "0",
        }

        if timelimit and timelimit in DDG_TIMELIMIT_MAP:
            params["df"] = DDG_TIMELIMIT_MAP[timelimit]

        all_results: list[ImageResult] = []
        url = self.search_url

        for _ in range(max((max_results + 50) // 50, 1)):
            try:
                resp = self._http.get(url, params=params)
            except Exception:  # noqa: BLE001
                logger.exception("DDG images request failed")
                break

            if not resp or not resp.ok:
                break

            try:
                data = json.loads(resp.text)
            except json.JSONDecodeError:
                logger.warning("DDG images: invalid JSON response")
                break

            items = data.get("results", [])
            if not items:
                break

            for item in items:
                result = ImageResult(
                    title=item.get("title", ""),
                    image=item.get("image", ""),
                    thumbnail=item.get("thumbnail", ""),
                    url=item.get("url", ""),
                    height=str(item.get("height", "")),
                    width=str(item.get("width", "")),
                    source=item.get("source", ""),
                )
                all_results.append(result)

            if len(all_results) >= max_results:
                break

            next_path = data.get("next")
            if not next_path:
                break

            url = f"https://duckduckgo.com{next_path}"
            params = {}  # next URL is self-contained
            time.sleep(uniform(0.5, 1.5))

        return all_results[:max_results]


# ---------------------------------------------------------------------------
# News search engine (JSON API)
# ---------------------------------------------------------------------------


class DuckDuckGoNewsEngine(BaseEngine[NewsResult]):
    """DuckDuckGo news search via JSON API."""

    name: ClassVar[str] = "ddg-news"
    search_url: ClassVar[str] = DDG_NEWS_URL
    result_type = NewsResult  # type: ignore[assignment]

    def build_params(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Not used directly — search_pages handles params."""
        return {}

    def search_pages(
        self,
        query: str,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        **kwargs: Any,  # noqa: ARG002
    ) -> list[NewsResult]:
        """Fetch news results from DDG JSON API with pagination."""
        vqd = _get_vqd(self._http, query)

        # Set required headers for DDG API authentication
        self._http.update_headers({
            "Referer": "https://duckduckgo.com/",
            "x-vqd-4": vqd,
        })

        params: dict[str, str] = {
            "q": query,
            "o": "json",
            "l": _ddg_region(region),
            "s": "0",
        }

        if timelimit and timelimit in DDG_TIMELIMIT_MAP:
            params["df"] = DDG_TIMELIMIT_MAP[timelimit]

        all_results: list[NewsResult] = []
        offset = 0

        for _ in range(max((max_results + 25) // 25, 1)):
            params["s"] = str(offset)

            try:
                resp = self._http.get(self.search_url, params=params)
            except Exception:  # noqa: BLE001
                logger.exception("DDG news request failed")
                break

            if not resp or not resp.ok:
                break

            try:
                data = json.loads(resp.text)
            except json.JSONDecodeError:
                logger.warning("DDG news: invalid JSON response")
                break

            items = data.get("results", [])
            if not items:
                break

            for item in items:
                result = NewsResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    body=item.get("excerpt", item.get("body", "")),
                    source=item.get("source", ""),
                    date=item.get("date", ""),
                    image=item.get("image", ""),
                )
                all_results.append(result)

            if len(all_results) >= max_results:
                break

            offset += len(items)
            time.sleep(uniform(0.5, 1.5))

        return all_results[:max_results]


# ---------------------------------------------------------------------------
# Video search engine (JSON API)
# ---------------------------------------------------------------------------


class DuckDuckGoVideosEngine(BaseEngine[VideoResult]):
    """DuckDuckGo video search via JSON API."""

    name: ClassVar[str] = "ddg-videos"
    search_url: ClassVar[str] = DDG_VIDEOS_URL
    result_type = VideoResult  # type: ignore[assignment]

    def build_params(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Not used directly — search_pages handles params."""
        return {}

    def search_pages(
        self,
        query: str,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        **kwargs: Any,
    ) -> list[VideoResult]:
        """Fetch video results from DDG JSON API with pagination."""
        vqd = _get_vqd(self._http, query)

        # Set required headers for DDG API authentication
        self._http.update_headers({
            "Referer": "https://duckduckgo.com/",
            "x-vqd-4": vqd,
        })

        params: dict[str, str] = {
            "q": query,
            "o": "json",
            "l": _ddg_region(region),
            "s": "0",
        }

        duration = kwargs.get("duration")
        if duration:
            params["duration"] = duration

        if timelimit and timelimit in DDG_TIMELIMIT_MAP:
            params["df"] = DDG_TIMELIMIT_MAP[timelimit]

        all_results: list[VideoResult] = []
        offset = 0

        for _ in range(max((max_results + 25) // 25, 1)):
            params["s"] = str(offset)

            try:
                resp = self._http.get(self.search_url, params=params)
            except Exception:  # noqa: BLE001
                logger.exception("DDG videos request failed")
                break

            if not resp or not resp.ok:
                break

            try:
                data = json.loads(resp.text)
            except json.JSONDecodeError:
                logger.warning("DDG videos: invalid JSON response")
                break

            items = data.get("results", [])
            if not items:
                break

            for item in items:
                images = item.get("images", {})
                thumbnail = ""
                if isinstance(images, dict):
                    thumbnail = images.get("large", images.get("medium", images.get("small", "")))

                result = VideoResult(
                    title=item.get("title", ""),
                    url=item.get("content", ""),
                    body=item.get("description", ""),
                    duration=item.get("duration", ""),
                    source=item.get("publisher", ""),
                    date=item.get("published", ""),
                    thumbnail=thumbnail,
                )
                all_results.append(result)

            if len(all_results) >= max_results:
                break

            offset += len(items)
            time.sleep(uniform(0.5, 1.5))

        return all_results[:max_results]
