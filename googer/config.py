"""Configuration constants for Googer.

Centralises all magic values, default settings, and URL templates
so that the rest of the library stays clean and declarative.
"""

from typing import Final

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
VERSION: Final[str] = __import__("importlib.metadata", fromlist=["version"]).version("googer")

# ---------------------------------------------------------------------------
# HTTP defaults
# ---------------------------------------------------------------------------
DEFAULT_TIMEOUT: Final[int] = 10
DEFAULT_MAX_RETRIES: Final[int] = 3
RETRY_BACKOFF_FACTOR: Final[float] = 0.5
DEFAULT_IMPERSONATE: Final[str] = "random"
DEFAULT_IMPERSONATE_OS: Final[str] = "random"

# ---------------------------------------------------------------------------
# Google URLs
# ---------------------------------------------------------------------------
GOOGLE_TEXT_URL: Final[str] = "https://www.google.com/search"
GOOGLE_IMAGES_URL: Final[str] = "https://www.google.com/search"
GOOGLE_NEWS_URL: Final[str] = "https://www.google.com/search"
GOOGLE_VIDEOS_URL: Final[str] = "https://www.google.com/search"

# ---------------------------------------------------------------------------
# Search defaults
# ---------------------------------------------------------------------------
DEFAULT_REGION: Final[str] = "us-en"
DEFAULT_SAFESEARCH: Final[str] = "moderate"
DEFAULT_MAX_RESULTS: Final[int] = 10
RESULTS_PER_PAGE: Final[int] = 10

# ---------------------------------------------------------------------------
# Safe-search mapping  (Google's &filter= parameter)
# ---------------------------------------------------------------------------
SAFESEARCH_MAP: Final[dict[str, str]] = {
    "on": "2",
    "moderate": "1",
    "off": "0",
}

# ---------------------------------------------------------------------------
# Time-limit shortcuts  (Google's &tbs=qdr: parameter)
# ---------------------------------------------------------------------------
TIMELIMIT_MAP: Final[dict[str, str]] = {
    "h": "h",       # past hour
    "d": "d",       # past day
    "w": "w",       # past week
    "m": "m",       # past month
    "y": "y",       # past year
}

# ---------------------------------------------------------------------------
# Image search parameters
# ---------------------------------------------------------------------------
IMAGE_SIZE_MAP: Final[dict[str, str]] = {
    "large": "isz:l",
    "medium": "isz:m",
    "icon": "isz:i",
}

IMAGE_COLOR_MAP: Final[dict[str, str]] = {
    "color": "ic:color",
    "gray": "ic:gray",
    "mono": "ic:mono",
    "trans": "ic:trans",
}

IMAGE_TYPE_MAP: Final[dict[str, str]] = {
    "face": "itp:face",
    "photo": "itp:photo",
    "clipart": "itp:clipart",
    "lineart": "itp:lineart",
    "animated": "itp:animated",
}

IMAGE_LICENSE_MAP: Final[dict[str, str]] = {
    "creative_commons": "il:cl",
    "commercial": "il:ol",
}

# ---------------------------------------------------------------------------
# Video search parameters
# ---------------------------------------------------------------------------
VIDEO_DURATION_MAP: Final[dict[str, str]] = {
    "short": "dur:s",     # < 4 minutes
    "medium": "dur:m",    # 4-20 minutes
    "long": "dur:l",      # > 20 minutes
}

# ---------------------------------------------------------------------------
# News search parameter: tbm value
# ---------------------------------------------------------------------------
TBM_NEWS: Final[str] = "nws"
TBM_IMAGES: Final[str] = "isch"
TBM_VIDEOS: Final[str] = "vid"

# ---------------------------------------------------------------------------
# XPath selectors — Text search
# ---------------------------------------------------------------------------
TEXT_ITEMS_XPATH: Final[str] = "//div[@data-snc]"
TEXT_ELEMENTS_XPATH: Final[dict[str, str]] = {
    "title": ".//div[@role='link']//text()",
    "href": ".//a/@href",
    "body": "./div[@data-sncf]//text()",
}

# ---------------------------------------------------------------------------
# XPath selectors — News search
# ---------------------------------------------------------------------------
NEWS_ITEMS_XPATH: Final[str] = "//a[contains(@class,'WlydOe')]"
NEWS_ELEMENTS_XPATH: Final[dict[str, str]] = {
    "title": ".//div[@role='heading']//text()",
    "url": "./@href",
    "body": ".//div[@role='heading']//text()",
    "source": ".//div[contains(@class,'MgUUmf')]//span//text()",
    "date": ".//div[contains(@class,'OSrXXb')]//span//text()",
}

# ---------------------------------------------------------------------------
# XPath selectors — Video search
# ---------------------------------------------------------------------------
VIDEO_ITEMS_XPATH: Final[str] = "//div[@class='MjjYud']"
VIDEO_ELEMENTS_XPATH: Final[dict[str, str]] = {
    "title": ".//h3//text()",
    "url": ".//a/@href",
    "body": ".//div[@class='ITZIwc']//text()",
    "duration": ".//div[@class='J1mWY']//text()",
    "source": ".//span[@class='CA5RN']//span//text()",
    "date": ".//span[@class='rQMQod']//text()",
}

# ---------------------------------------------------------------------------
# Rate-limit detection patterns
# ---------------------------------------------------------------------------
RATE_LIMIT_INDICATORS: Final[tuple[str, ...]] = (
    "detected unusual traffic",
    "captcha",
    "/sorry/",
    "recaptcha",
)
