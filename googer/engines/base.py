"""Abstract base class for Google search engines.

Every concrete engine (text, images, news, videos) inherits from
:class:`BaseEngine` and must implement :meth:`build_params` and
may override any of the hook methods.
"""

import logging
import time
from abc import ABC, abstractmethod
from random import uniform
from typing import Any, ClassVar, Generic, TypeVar

from ..config import (
    DEFAULT_MAX_RESULTS,
    DEFAULT_REGION,
    DEFAULT_SAFESEARCH,
    RESULTS_PER_PAGE,
    SAFESEARCH_MAP,
)
from ..exceptions import RateLimitException, TimeoutException
from ..http_client import HttpClient, Response
from ..parser import GoogleParser
from ..results import BaseResult
from ..utils import build_region_params

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseResult)

# Type alias for any client that provides .get()/.post()/.update_headers()
# (HttpClient or BrowserClient — duck-typed).
_Client = Any


class BaseEngine(ABC, Generic[T]):
    """Abstract base for a Google search engine variant.

    Class attributes that subclasses **must** set:

    * ``name``          — unique identifier (e.g. ``"text"``).
    * ``search_url``    — the Google endpoint URL.
    * ``result_type``   — the concrete :class:`BaseResult` subclass.
    * ``items_xpath``   — XPath for selecting item nodes.
    * ``elements_xpath``— Mapping of field name → relative XPath per item.

    Class attributes that subclasses **may** override:

    * ``search_method`` — ``"GET"`` (default) or ``"POST"``.
    * ``extra_headers`` — Extra HTTP headers merged into each request.

    The *http_client* parameter accepts either an :class:`HttpClient`
    or a :class:`~googer.browser_client.BrowserClient` (duck-typed).

    """

    name: ClassVar[str]
    search_url: ClassVar[str]
    result_type: ClassVar[type[BaseResult]]
    items_xpath: ClassVar[str] = ""
    elements_xpath: ClassVar[dict[str, str]] = {}
    search_method: ClassVar[str] = "GET"
    extra_headers: ClassVar[dict[str, str]] = {}

    def __init__(self, http_client: _Client) -> None:
        self._http = http_client
        if self.extra_headers:
            self._http.update_headers(self.extra_headers)
        if self.items_xpath and self.elements_xpath:
            self._parser: GoogleParser | None = GoogleParser(
                items_xpath=self.items_xpath,
                elements_xpath=self.elements_xpath,
            )
        else:
            self._parser = None

    # -- abstract -----------------------------------------------------------

    @abstractmethod
    def build_params(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Return query parameters / form data for this engine.

        Args:
            query: Search query string.
            region: Region code (e.g. ``"us-en"``).
            safesearch: One of ``"on"``, ``"moderate"``, ``"off"``.
            timelimit: Time filter (``"h"``, ``"d"``, ``"w"``, ``"m"``, ``"y"`` or ``None``).
            page: 1-based page number.
            **kwargs: Engine-specific extras.

        Returns:
            Dict of query-string parameters (GET) or form fields (POST).

        """
        raise NotImplementedError

    # -- overridable hooks --------------------------------------------------

    def post_process(self, results: list[T]) -> list[T]:
        """Post-process extracted results before returning.

        Override in subclasses for engine-specific cleanup (e.g. URL unwrapping).
        """
        return results

    # -- core search --------------------------------------------------------

    def search(
        self,
        query: str,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        page: int = 1,
        **kwargs: Any,
    ) -> list[T]:
        """Execute a single-page search and return parsed results.

        Args:
            query: Search terms.
            region: Locale code.
            safesearch: Safe-search level.
            timelimit: Optional time filter.
            page: Page number (1-based).
            **kwargs: Engine-specific extras.

        Returns:
            A list of typed result objects.

        """
        params = self.build_params(
            query=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
            **kwargs,
        )

        resp = self._make_request(params)
        if not resp or not resp.ok:
            logger.warning(
                "Engine %s: HTTP %s for url=%s (body=%d bytes)",
                self.name,
                resp.status_code if resp else "None",
                self.search_url,
                len(resp.text) if resp else 0,
            )
            return []

        if self._parser is None:
            logger.warning("Engine %s: no parser configured", self.name)
            return []

        results = self._parser.parse(resp.text, self.result_type)  # type: ignore[arg-type]
        logger.debug(
            "Engine %s: parsed %d raw results from %d bytes",
            self.name,
            len(results),
            len(resp.text),
        )
        return self.post_process(results)

    # -- multi-page search --------------------------------------------------

    def search_pages(
        self,
        query: str,
        region: str = DEFAULT_REGION,
        safesearch: str = DEFAULT_SAFESEARCH,
        timelimit: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        **kwargs: Any,
    ) -> list[T]:
        """Search across multiple pages until *max_results* are collected.

        Args:
            query: Search terms.
            region: Locale code.
            safesearch: Safe-search level.
            timelimit: Optional time filter.
            max_results: Target number of results.
            **kwargs: Engine-specific extras.

        Returns:
            Combined results from all fetched pages.

        """
        all_results: list[T] = []
        pages_needed = (max_results + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE

        for page in range(1, pages_needed + 1):
            # Randomised delay between pages to avoid rate limiting
            if page > 1:
                delay = uniform(1.5, 3.5)
                logger.debug("Sleeping %.2fs between pages", delay)
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

    # -- internal -----------------------------------------------------------

    def _make_request(self, params: dict[str, Any]) -> Response | None:
        """Send the actual HTTP request."""
        try:
            if self.search_method == "GET":
                return self._http.get(self.search_url, params=params)
            return self._http.post(self.search_url, data=params)
        except (RateLimitException, TimeoutException):
            raise
        except Exception:
            logger.exception("Request failed for engine %s", self.name)
            return None

    # -- helpers for subclasses ---------------------------------------------

    @staticmethod
    def _build_base_params(
        query: str,
        region: str,
        safesearch: str,
        page: int,
    ) -> dict[str, str]:
        """Build the minimal parameter set shared by all engines.

        Args:
            query: Search terms.
            region: Locale code.
            safesearch: Safe-search level.
            page: 1-based page number.

        Returns:
            Dict ready to be extended by subclass-specific params.

        """
        params: dict[str, str] = {"q": query}
        params["filter"] = SAFESEARCH_MAP.get(safesearch.lower(), "1")
        params["start"] = str((page - 1) * RESULTS_PER_PAGE)
        params.update(build_region_params(region))
        return params
