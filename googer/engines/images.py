"""Google image search engine."""

import logging
from typing import Any, ClassVar

from ..config import (
    GOOGLE_IMAGES_URL,
    IMAGE_COLOR_MAP,
    IMAGE_LICENSE_MAP,
    IMAGE_SIZE_MAP,
    IMAGE_TYPE_MAP,
    TBM_IMAGES,
    TIMELIMIT_MAP,
)
from ..results import ImageResult
from ..utils import extract_clean_url
from .base import BaseEngine

logger = logging.getLogger(__name__)


class GoogleImagesEngine(BaseEngine[ImageResult]):
    """Google image search engine.

    Uses ``tbm=isch`` to retrieve image results from Google.
    """

    name: ClassVar[str] = "images"
    search_url: ClassVar[str] = GOOGLE_IMAGES_URL
    result_type = ImageResult  # type: ignore[assignment]

    # Image search returns a different HTML structure
    items_xpath: ClassVar[str] = "//div[@class='isv-r PNCib MSM1fd BUooTd']"
    elements_xpath: ClassVar[dict[str, str]] = {
        "title": ".//h3//text()",
        "url": ".//a/@href",
        "thumbnail": ".//img/@src",
    }

    def build_params(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        *,
        size: str | None = None,
        color: str | None = None,
        image_type: str | None = None,
        license_type: str | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build GET parameters for an image search.

        Args:
            query: Search terms.
            region: Locale code.
            safesearch: Safe-search level.
            timelimit: Time filter.
            page: 1-based page number.
            size: Image size (``large``, ``medium``, ``icon``).
            color: Color filter (``color``, ``gray``, ``mono``, ``trans``).
            image_type: Type filter (``face``, ``photo``, ``clipart``, ``lineart``, ``animated``).
            license_type: License (``creative_commons``, ``commercial``).

        Returns:
            Google image query parameters.

        """
        params = self._build_base_params(query, region, safesearch, page)
        params["tbm"] = TBM_IMAGES

        # Build tbs parameter with filters
        tbs_parts: list[str] = []
        if timelimit and timelimit in TIMELIMIT_MAP:
            tbs_parts.append(f"qdr:{TIMELIMIT_MAP[timelimit]}")
        if size and size in IMAGE_SIZE_MAP:
            tbs_parts.append(IMAGE_SIZE_MAP[size])
        if color and color in IMAGE_COLOR_MAP:
            tbs_parts.append(IMAGE_COLOR_MAP[color])
        if image_type and image_type in IMAGE_TYPE_MAP:
            tbs_parts.append(IMAGE_TYPE_MAP[image_type])
        if license_type and license_type in IMAGE_LICENSE_MAP:
            tbs_parts.append(IMAGE_LICENSE_MAP[license_type])
        if tbs_parts:
            params["tbs"] = ",".join(tbs_parts)

        return params

    def post_process(self, results: list[ImageResult]) -> list[ImageResult]:
        """Clean URLs and filter out empty entries."""
        cleaned: list[ImageResult] = []
        for r in results:
            r.url = extract_clean_url(r.url)
            if r.title or r.thumbnail:
                cleaned.append(r)
        if not cleaned:
            logger.warning(
                "Google Images returned 0 parseable results. Google now requires "
                "JavaScript rendering \u2014 use backend='browser' or a different engine."
            )
        return cleaned
