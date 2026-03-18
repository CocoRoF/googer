"""User-Agent management for Googer.

Provides rotating User-Agent strings that mimic real Google Search App
(GSA) on iOS devices.  The mapping is derived from observed UA strings
in the wild and keeps the library stealthy against bot-detection.
"""

from random import SystemRandom

_rng = SystemRandom()

# iOS version → list of observed GSA (Google Search App) versions
_IOS_GSA_MAP: dict[str, list[str]] = {
    "17_4": ["315.0.630091404", "317.0.634488990"],
    "17_6_1": ["411.0.879111500"],
    "18_1_1": ["411.0.879111500"],
    "18_2": ["173.0.391310503"],
    "18_6_2": [
        "397.0.836500703",
        "399.2.845414227",
        "410.0.875971614",
        "411.0.879111500",
    ],
    "18_7_2": ["411.0.879111500"],
    "18_7_5": ["411.0.879111500"],
    "18_7_6": ["411.0.879111500"],
    "26_1_0": ["411.0.879111500"],
    "26_2_0": [
        "396.0.833910942",
        "409.0.872648028",
        "411.0.879111500",
    ],
    "26_2_1": ["409.0.872648028", "411.0.879111500"],
    "26_3_0": [
        "406.0.862495628",
        "410.0.875971614",
        "411.0.879111500",
    ],
    "26_3_1": [
        "370.0.762543316",
        "404.0.856692123",
        "408.0.868297084",
        "410.0.875971614",
        "411.0.879111500",
    ],
    "26_4_0": ["411.0.879111500"],
}

# Pre-built Chrome desktop UA pool for fallback / alternative strategies
_CHROME_DESKTOP_UAS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_4) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_4) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]


def get_gsa_user_agent() -> str:
    """Return a random GSA (Google Search App) User-Agent for iOS."""
    ios_ver = _rng.choice(list(_IOS_GSA_MAP.keys()))
    gsa_ver = _rng.choice(_IOS_GSA_MAP[ios_ver])
    return (
        f"Mozilla/5.0 (iPhone; CPU iPhone OS {ios_ver} like Mac OS X) "
        f"AppleWebKit/605.1.15 (KHTML, like Gecko) "
        f"GSA/{gsa_ver} Mobile/15E148 Safari/604.1"
    )


def get_chrome_user_agent() -> str:
    """Return a random Chrome desktop User-Agent."""
    return _rng.choice(_CHROME_DESKTOP_UAS)


def get_random_user_agent() -> str:
    """Return a random User-Agent, weighted towards GSA strings."""
    if _rng.random() < 0.7:
        return get_gsa_user_agent()
    return get_chrome_user_agent()
