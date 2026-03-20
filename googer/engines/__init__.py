"""Engine registry for Googer.

Exposes an ``ENGINES`` dict mapping provider name → search-type → engine class.
"""

from .aol import AolTextEngine
from .brave import BraveImagesEngine, BraveNewsEngine, BraveTextEngine, BraveVideosEngine
from .duckduckgo import (
    DuckDuckGoImagesEngine,
    DuckDuckGoNewsEngine,
    DuckDuckGoTextEngine,
    DuckDuckGoVideosEngine,
)
from .ecosia import EcosiaTextEngine
from .images import GoogleImagesEngine
from .naver import NaverTextEngine
from .news import GoogleNewsEngine
from .text import GoogleTextEngine
from .videos import GoogleVideosEngine
from .yahoo import YahooTextEngine

ENGINES: dict[str, dict[str, type]] = {
    "google": {
        "text": GoogleTextEngine,
        "images": GoogleImagesEngine,
        "news": GoogleNewsEngine,
        "videos": GoogleVideosEngine,
    },
    "duckduckgo": {
        "text": DuckDuckGoTextEngine,
        "images": DuckDuckGoImagesEngine,
        "news": DuckDuckGoNewsEngine,
        "videos": DuckDuckGoVideosEngine,
    },
    "brave": {
        "text": BraveTextEngine,
        "images": BraveImagesEngine,
        "news": BraveNewsEngine,
        "videos": BraveVideosEngine,
    },
    "ecosia": {
        "text": EcosiaTextEngine,
    },
    "yahoo": {
        "text": YahooTextEngine,
    },
    "aol": {
        "text": AolTextEngine,
    },
    "naver": {
        "text": NaverTextEngine,
    },
}

__all__ = [
    "ENGINES",
    "AolTextEngine",
    "BraveImagesEngine",
    "BraveNewsEngine",
    "BraveTextEngine",
    "BraveVideosEngine",
    "DuckDuckGoImagesEngine",
    "DuckDuckGoNewsEngine",
    "DuckDuckGoTextEngine",
    "DuckDuckGoVideosEngine",
    "EcosiaTextEngine",
    "GoogleImagesEngine",
    "GoogleNewsEngine",
    "GoogleTextEngine",
    "GoogleVideosEngine",
    "NaverTextEngine",
    "YahooTextEngine",
]
