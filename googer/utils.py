"""Utility functions for Googer.

Provides text normalization, URL cleaning, date parsing, and other
small helpers shared across the library.
"""

import re
import unicodedata
from datetime import datetime, timezone
from html import unescape
from urllib.parse import parse_qs, unquote, urlparse

_RE_STRIP_TAGS = re.compile(r"<.*?>")
_RE_MULTI_SPACES = re.compile(r"\s+")


def normalize_url(url: str) -> str:
    """Unquote a URL and normalise spaces.

    Args:
        url: Raw URL string (may be percent-encoded).

    Returns:
        Cleaned URL with spaces replaced by ``+``.

    """
    if not url:
        return ""
    return unquote(url).replace(" ", "+")


def normalize_text(raw: str) -> str:
    """Normalize text for display.

    Pipeline: strip HTML tags → unescape entities → NFC normalise →
    remove Unicode control characters → collapse whitespace.

    Args:
        raw: Raw text (may include HTML fragments).

    Returns:
        Clean, human-readable string.

    """
    if not raw:
        return ""

    # 1. Strip HTML tags
    text = _RE_STRIP_TAGS.sub("", raw)

    # 2. Unescape HTML entities
    text = unescape(text)

    # 3. Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)

    # 4. Remove Unicode "C" (control) category characters
    ctrl_map = {ord(ch): None for ch in set(text) if unicodedata.category(ch)[0] == "C"}
    if ctrl_map:
        text = text.translate(ctrl_map)

    # 5. Collapse whitespace
    return _RE_MULTI_SPACES.sub(" ", text).strip()


def normalize_date(value: int | str) -> str:
    """Convert a Unix timestamp to ISO-8601, or pass through a string.

    Args:
        value: Either an integer Unix timestamp or an already-formatted string.

    Returns:
        ISO-8601 formatted date string.

    """
    if isinstance(value, int):
        return datetime.fromtimestamp(value, timezone.utc).isoformat()
    return value


def extract_clean_url(raw_url: str) -> str:
    """Extract the actual destination URL from a Google redirect URL.

    Google wraps outbound links in ``/url?q=<target>&...``.
    This function extracts ``<target>`` and strips Google's
    ``#:~:text=`` highlight fragments.

    Args:
        raw_url: Possibly-wrapped Google redirect URL.

    Returns:
        The unwrapped destination URL, or the original if not wrapped.

    """
    if raw_url.startswith("/url?q="):
        url = raw_url.split("?q=", 1)[1].split("&", 1)[0]
        return _strip_text_fragment(normalize_url(url))
    return _strip_text_fragment(normalize_url(raw_url))


def _strip_text_fragment(url: str) -> str:
    """Remove ``#:~:text=...`` fragments appended by Google."""
    idx = url.find("#:~:text=")
    return url[:idx] if idx != -1 else url


def expand_proxy_alias(proxy: str | None) -> str | None:
    """Expand shorthand proxy aliases.

    Currently supports:

    * ``"tb"`` → ``socks5h://127.0.0.1:9150`` (Tor Browser)

    Args:
        proxy: Proxy string or alias.

    Returns:
        Expanded proxy URL, or the input unchanged.

    """
    if proxy == "tb":
        return "socks5h://127.0.0.1:9150"
    return proxy


def extract_ddg_url(raw_url: str) -> str:
    """Extract the actual destination URL from a DuckDuckGo redirect URL.

    DuckDuckGo wraps outbound links in ``//duckduckgo.com/l/?uddg=<target>&...``.
    This function extracts ``<target>``.

    Args:
        raw_url: Possibly-wrapped DuckDuckGo redirect URL.

    Returns:
        The unwrapped destination URL, or the original if not wrapped.

    """
    if not raw_url:
        return ""
    if "uddg=" in raw_url:
        url = raw_url if raw_url.startswith("http") else f"https:{raw_url}"
        parsed = urlparse(url)
        uddg = parse_qs(parsed.query).get("uddg")
        if uddg:
            return unquote(uddg[0])
    return normalize_url(raw_url)


def extract_yahoo_redirect_url(raw_url: str) -> str:
    """Extract the actual destination URL from a Yahoo/AOL redirect URL.

    Yahoo and AOL wrap outbound links in
    ``r.search.yahoo.com/_ylt=.../RU=<target>/RK=...``.
    This function extracts ``<target>`` and URL-decodes it.

    Handles both percent-encoded and already-decoded forms since
    :class:`TextResult` may normalise the href before post-processing.

    Args:
        raw_url: Possibly-wrapped Yahoo/AOL redirect URL.

    Returns:
        The unwrapped destination URL, or the original if not wrapped.

    """
    if not raw_url:
        return ""
    if "/RU=" in raw_url:
        # Match everything between /RU= and /RK= (greedy but bounded)
        match = re.search(r"/RU=(.*?)/RK=", raw_url)
        if match:
            return unquote(match.group(1))
    return normalize_url(raw_url)


def build_region_params(region: str) -> dict[str, str]:
    """Parse a region code (e.g. ``us-en``) into Google query parameters.

    Args:
        region: A ``<country>-<lang>`` string.

    Returns:
        Dict with ``hl``, ``lr``, and ``cr`` keys.

    """
    parts = region.lower().split("-", 1)
    if len(parts) != 2:  # noqa: PLR2004
        country, lang = "us", "en"
    else:
        country, lang = parts

    return {
        "hl": f"{lang}-{country.upper()}",      # interface language
        "lr": f"lang_{lang}",                    # restrict to language
        "cr": f"country{country.upper()}",       # restrict to country
    }
