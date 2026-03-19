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
# Engine defaults
# ---------------------------------------------------------------------------
DEFAULT_ENGINE: Final[str] = "auto"
ENGINE_FALLBACK_ORDER: Final[tuple[str, ...]] = (
    "duckduckgo", "brave", "ecosia", "yahoo", "aol", "google", "naver",
)

# ---------------------------------------------------------------------------
# Cache defaults
# ---------------------------------------------------------------------------
DEFAULT_CACHE_TTL: Final[int] = 300  # 5 minutes
DEFAULT_CACHE_ENABLED: Final[bool] = True

# ---------------------------------------------------------------------------
# Google URLs
# ---------------------------------------------------------------------------
GOOGLE_TEXT_URL: Final[str] = "https://www.google.com/search"
GOOGLE_IMAGES_URL: Final[str] = "https://www.google.com/search"
GOOGLE_NEWS_URL: Final[str] = "https://www.google.com/search"
GOOGLE_VIDEOS_URL: Final[str] = "https://www.google.com/search"

# ---------------------------------------------------------------------------
# DuckDuckGo URLs
# ---------------------------------------------------------------------------
DDG_TEXT_URL: Final[str] = "https://html.duckduckgo.com/html/"
DDG_IMAGES_URL: Final[str] = "https://duckduckgo.com/i.js"
DDG_NEWS_URL: Final[str] = "https://duckduckgo.com/news.js"
DDG_VIDEOS_URL: Final[str] = "https://duckduckgo.com/v.js"
DDG_VQD_URL: Final[str] = "https://duckduckgo.com/"
DDG_SUGGEST_URL: Final[str] = "https://ac.duckduckgo.com/ac/"
DDG_ANSWER_URL: Final[str] = "https://api.duckduckgo.com/"

# ---------------------------------------------------------------------------
# Brave URLs
# ---------------------------------------------------------------------------
BRAVE_TEXT_URL: Final[str] = "https://search.brave.com/search"
BRAVE_NEWS_URL: Final[str] = "https://search.brave.com/news"
BRAVE_VIDEOS_URL: Final[str] = "https://search.brave.com/videos"

# ---------------------------------------------------------------------------
# Ecosia URLs
# ---------------------------------------------------------------------------
ECOSIA_TEXT_URL: Final[str] = "https://www.ecosia.org/search"

# ---------------------------------------------------------------------------
# Yahoo URLs
# ---------------------------------------------------------------------------
YAHOO_TEXT_URL: Final[str] = "https://search.yahoo.com/search"

# ---------------------------------------------------------------------------
# AOL URLs
# ---------------------------------------------------------------------------
AOL_TEXT_URL: Final[str] = "https://search.aol.com/aol/search"

# ---------------------------------------------------------------------------
# Naver URLs
# ---------------------------------------------------------------------------
NAVER_TEXT_URL: Final[str] = "https://search.naver.com/search.naver"

# ---------------------------------------------------------------------------
# Search defaults
# ---------------------------------------------------------------------------
DEFAULT_REGION: Final[str] = "us-en"
DEFAULT_SAFESEARCH: Final[str] = "moderate"
DEFAULT_MAX_RESULTS: Final[int] = 10
RESULTS_PER_PAGE: Final[int] = 10
BRAVE_RESULTS_PER_PAGE: Final[int] = 20

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
# XPath selectors — Text search (browser-rendered HTML)
# ---------------------------------------------------------------------------
TEXT_ITEMS_XPATH: Final[str] = "//div[contains(@class, 'tF2Cxc')]"
TEXT_ELEMENTS_XPATH: Final[dict[str, str]] = {
    "title": ".//h3//text()",
    "href": ".//h3/ancestor::a/@href",
    "body": ".//div[contains(@class, 'VwiC3b')]//text()",
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

# ---------------------------------------------------------------------------
# DuckDuckGo safesearch mapping (kp parameter)
# ---------------------------------------------------------------------------
DDG_SAFESEARCH_MAP: Final[dict[str, str]] = {
    "on": "1",
    "moderate": "-1",
    "off": "-2",
}

# ---------------------------------------------------------------------------
# DuckDuckGo time-limit mapping (df parameter)
# ---------------------------------------------------------------------------
DDG_TIMELIMIT_MAP: Final[dict[str, str]] = {
    "d": "d",       # past day
    "w": "w",       # past week
    "m": "m",       # past month
    "y": "y",       # past year
}

# ---------------------------------------------------------------------------
# XPath selectors — DuckDuckGo text search (HTML form results)
# ---------------------------------------------------------------------------
DDG_TEXT_ITEMS_XPATH: Final[str] = "//div[contains(@class, 'result__body')]"
DDG_TEXT_ELEMENTS_XPATH: Final[dict[str, str]] = {
    "title": ".//a[contains(@class, 'result__a')]//text()",
    "href": ".//a[contains(@class, 'result__a')]/@href",
    "body": ".//a[contains(@class, 'result__snippet')]//text()",
}

# ---------------------------------------------------------------------------
# Brave safesearch mapping
# ---------------------------------------------------------------------------
BRAVE_SAFESEARCH_MAP: Final[dict[str, str]] = {
    "on": "strict",
    "moderate": "moderate",
    "off": "off",
}

# ---------------------------------------------------------------------------
# Brave time-limit mapping (tf parameter)
# ---------------------------------------------------------------------------
BRAVE_TIMELIMIT_MAP: Final[dict[str, str]] = {
    "d": "pd",       # past day
    "w": "pw",       # past week
    "m": "pm",       # past month
    "y": "py",       # past year
}

# ---------------------------------------------------------------------------
# XPath selectors — Brave text search
# ---------------------------------------------------------------------------
BRAVE_TEXT_ITEMS_XPATH: Final[str] = "//div[@data-type='web']"
BRAVE_TEXT_ELEMENTS_XPATH: Final[dict[str, str]] = {
    "title": ".//a[contains(@class,'l1')]//div[contains(@class,'title')]//text()",
    "href": ".//a[contains(@class,'l1')]/@href",
    "body": ".//div[contains(@class,'generic-snippet')]//div[contains(@class,'content')]//text()",
}

# ---------------------------------------------------------------------------
# XPath selectors — Brave news search
# ---------------------------------------------------------------------------
BRAVE_NEWS_ITEMS_XPATH: Final[str] = "//div[@data-type='news']"
BRAVE_NEWS_ELEMENTS_XPATH: Final[dict[str, str]] = {
    "title": ".//div[contains(@class,'title')]/@title",
    "url": ".//a[contains(@class,'l1')]/@href",
    "body": ".//div[contains(@class,'description')]//text()",
    "source": ".//span[contains(@class,'desktop-small-semibold')]//text()",
    "date": ".//span[contains(@class,'age-header')]//span[last()]//text()",
}

# ---------------------------------------------------------------------------
# XPath selectors — Brave video search
# ---------------------------------------------------------------------------
BRAVE_VIDEO_ITEMS_XPATH: Final[str] = "//div[@data-type='videos']"
BRAVE_VIDEO_ELEMENTS_XPATH: Final[dict[str, str]] = {
    "title": ".//div[contains(@class,'title')]/@title",
    "url": ".//a[contains(@class,'l1')]/@href",
    "body": ".//div[contains(@class,'description')]//text()",
    "duration": ".//div[contains(@class,'duration')]//text()",
    "source": ".//span[contains(@class,'desktop-small-semibold')]//text()",
    "date": ".//div[contains(@class,'metadata')]//text()",
}

# ---------------------------------------------------------------------------
# XPath selectors — Ecosia text search
# ---------------------------------------------------------------------------
ECOSIA_TEXT_ITEMS_XPATH: Final[str] = "//div[contains(@class,'mainline__result')]"
ECOSIA_TEXT_ELEMENTS_XPATH: Final[dict[str, str]] = {
    "title": ".//h2//text()",
    "href": ".//a[contains(@class,'result__link')]/@href",
    "body": ".//p[contains(@class,'web-result__description')]//text()",
}

# ---------------------------------------------------------------------------
# XPath selectors — Yahoo text search
# ---------------------------------------------------------------------------
YAHOO_TEXT_ITEMS_XPATH: Final[str] = "//div[contains(@class,'algo-sr')]"
YAHOO_TEXT_ELEMENTS_XPATH: Final[dict[str, str]] = {
    "title": ".//h3[1]//text()",
    "href": ".//a[1]/@href",
    "body": ".//p//text()",
}

# ---------------------------------------------------------------------------
# XPath selectors — AOL text search  (same structure as Yahoo)
# ---------------------------------------------------------------------------
AOL_TEXT_ITEMS_XPATH: Final[str] = "//div[contains(@class,'algo-sr')]"
AOL_TEXT_ELEMENTS_XPATH: Final[dict[str, str]] = {
    "title": ".//h3[1]//text()",
    "href": ".//a[1]/@href",
    "body": ".//p//text()",
}

# ---------------------------------------------------------------------------
# XPath selectors — Naver text search  (items only; element extraction is custom)
# ---------------------------------------------------------------------------
NAVER_TEXT_ITEMS_XPATH: Final[str] = "//div[contains(@class,'fds-web-doc-root')]"
