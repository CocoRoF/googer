"""Engine registry for Googer.

Exposes a ``ENGINES`` dict mapping engine name to engine class.
"""

from .images import GoogleImagesEngine
from .news import GoogleNewsEngine
from .text import GoogleTextEngine
from .videos import GoogleVideosEngine

ENGINES: dict[str, type] = {
    "text": GoogleTextEngine,
    "images": GoogleImagesEngine,
    "news": GoogleNewsEngine,
    "videos": GoogleVideosEngine,
}

__all__ = [
    "ENGINES",
    "GoogleImagesEngine",
    "GoogleNewsEngine",
    "GoogleTextEngine",
    "GoogleVideosEngine",
]
