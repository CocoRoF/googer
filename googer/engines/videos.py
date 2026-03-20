"""Google video search engine."""

import logging
from typing import Any, ClassVar

from ..config import (
    GOOGLE_VIDEOS_URL,
    TBM_VIDEOS,
    TIMELIMIT_MAP,
    VIDEO_DURATION_MAP,
    VIDEO_ELEMENTS_XPATH,
    VIDEO_ITEMS_XPATH,
)
from ..results import VideoResult
from ..utils import extract_clean_url
from .base import BaseEngine

logger = logging.getLogger(__name__)


class GoogleVideosEngine(BaseEngine[VideoResult]):
    """Google Video search engine.

    Uses ``tbm=vid`` to retrieve video results from Google.
    """

    name: ClassVar[str] = "videos"
    search_url: ClassVar[str] = GOOGLE_VIDEOS_URL
    result_type = VideoResult  # type: ignore[assignment]
    items_xpath: ClassVar[str] = VIDEO_ITEMS_XPATH
    elements_xpath: ClassVar[dict[str, str]] = dict(VIDEO_ELEMENTS_XPATH)

    def build_params(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        *,
        duration: str | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build GET parameters for a video search.

        Args:
            query: Search terms.
            region: Locale code.
            safesearch: Safe-search level.
            timelimit: Time filter.
            page: 1-based page number.
            duration: Duration filter (``short``, ``medium``, ``long``).

        Returns:
            Google Video query parameters.

        """
        params = self._build_base_params(query, region, safesearch, page)
        params["tbm"] = TBM_VIDEOS

        tbs_parts: list[str] = []
        if timelimit and timelimit in TIMELIMIT_MAP:
            tbs_parts.append(f"qdr:{TIMELIMIT_MAP[timelimit]}")
        if duration and duration in VIDEO_DURATION_MAP:
            tbs_parts.append(VIDEO_DURATION_MAP[duration])
        if tbs_parts:
            params["tbs"] = ",".join(tbs_parts)

        return params

    def post_process(self, results: list[VideoResult]) -> list[VideoResult]:
        """Clean URLs and filter valid results."""
        cleaned: list[VideoResult] = []
        for r in results:
            r.url = extract_clean_url(r.url)
            if r.title:
                cleaned.append(r)
        if not cleaned:
            logger.warning(
                "Google Videos returned 0 parseable results. Google now requires "
                "JavaScript rendering \u2014 use backend='browser' or a different engine."
            )
        return cleaned
