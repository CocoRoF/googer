"""HTTP client for Googer.

Wraps the ``primp`` library to provide a high-level HTTP client with:
* TLS fingerprint impersonation (anti-bot evasion)
* Automatic retries with exponential back-off
* Rate-limit / CAPTCHA detection
* Proxy support (HTTP / HTTPS / SOCKS5)
"""

import logging
import time
from typing import Any

import primp

from .config import (
    DEFAULT_IMPERSONATE,
    DEFAULT_IMPERSONATE_OS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    RATE_LIMIT_INDICATORS,
    RETRY_BACKOFF_FACTOR,
)
from .exceptions import HttpException, RateLimitException, TimeoutException
from .user_agents import get_gsa_user_agent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lightweight response wrapper
# ---------------------------------------------------------------------------


class Response:
    """Minimal HTTP response container.

    Attributes:
        status_code: HTTP status code.
        content: Raw bytes of the response body.
        text: Decoded text of the response body.

    """

    __slots__ = ("content", "status_code", "text")

    def __init__(self, status_code: int, content: bytes, text: str) -> None:
        self.status_code = status_code
        self.content = content
        self.text = text

    @property
    def ok(self) -> bool:
        """``True`` when the status code is in the 2xx range."""
        return 200 <= self.status_code < 300


# ---------------------------------------------------------------------------
# Main HTTP client
# ---------------------------------------------------------------------------


class HttpClient:
    """HTTP client with impersonation, retries, and rate-limit detection.

    Args:
        proxy: Proxy URL (``http://``, ``https://``, ``socks5://``).
        timeout: Request timeout in seconds.
        verify: SSL verification — ``True``, ``False``, or path to a PEM file.
        max_retries: Maximum number of retry attempts on transient failures.

    """

    def __init__(
        self,
        proxy: str | None = None,
        timeout: int | None = DEFAULT_TIMEOUT,
        *,
        verify: bool | str = True,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self._max_retries = max_retries
        self._timeout = timeout

        self.client = primp.Client(
            proxy=proxy,
            timeout=timeout,
            impersonate=DEFAULT_IMPERSONATE,
            impersonate_os=DEFAULT_IMPERSONATE_OS,
            verify=verify if isinstance(verify, bool) else True,
            ca_cert_file=verify if isinstance(verify, str) else None,
        )

        # Set a GSA User-Agent header by default
        self.client.headers_update({"User-Agent": get_gsa_user_agent()})

    # -- header management --------------------------------------------------

    def update_headers(self, headers: dict[str, str]) -> None:
        """Merge *headers* into the underlying session headers."""
        self.client.headers_update(headers)

    def rotate_user_agent(self) -> None:
        """Replace the current User-Agent with a freshly generated one."""
        self.client.headers_update({"User-Agent": get_gsa_user_agent()})

    # -- core request -------------------------------------------------------

    def request(self, method: str, url: str, **kwargs: Any) -> Response:  # noqa: ANN401
        """Execute an HTTP request with retries and rate-limit detection.

        Args:
            method: HTTP method (``GET`` or ``POST``).
            url: Target URL.
            **kwargs: Extra keyword arguments forwarded to ``primp.Client.request``.

        Returns:
            A :class:`Response` instance.

        Raises:
            RateLimitException: If Google returns a CAPTCHA / rate-limit page.
            TimeoutException: If the request times out after all retries.
            HttpException: For any other transport-level error.

        """
        last_exc: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                resp = self.client.request(method=method, url=url, **kwargs)
                wrapped = Response(
                    status_code=resp.status_code,
                    content=resp.content,
                    text=resp.text,
                )

                # Rate-limit / CAPTCHA detection
                if self._is_rate_limited(wrapped):
                    logger.warning("Rate limit detected (attempt %d/%d)", attempt, self._max_retries)
                    if attempt < self._max_retries:
                        self.rotate_user_agent()
                        self._backoff(attempt)
                        continue
                    raise RateLimitException(
                        "Google rate limit detected. Try again later or use a proxy."
                    )

                return wrapped

            except primp.TimeoutError as exc:
                last_exc = exc
                logger.debug("Timeout (attempt %d/%d): %r", attempt, self._max_retries, exc)
                if attempt < self._max_retries:
                    self._backoff(attempt)
                    continue
                raise TimeoutException(str(exc)) from exc

            except RateLimitException:
                raise

            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.debug("HTTP error (attempt %d/%d): %r", attempt, self._max_retries, exc)
                if attempt < self._max_retries:
                    self._backoff(attempt)
                    continue

        msg = f"Request failed after {self._max_retries} retries: {last_exc!r}"
        raise HttpException(msg) from last_exc

    def get(self, url: str, **kwargs: Any) -> Response:  # noqa: ANN401
        """Send a GET request."""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response:  # noqa: ANN401
        """Send a POST request."""
        return self.request("POST", url, **kwargs)

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _is_rate_limited(response: Response) -> bool:
        """Check whether a response looks like a Google rate-limit page."""
        if response.status_code == 429:  # noqa: PLR2004
            return True
        text_lower = response.text.lower()
        return any(indicator in text_lower for indicator in RATE_LIMIT_INDICATORS)

    @staticmethod
    def _backoff(attempt: int) -> None:
        """Sleep with exponential back-off."""
        delay = RETRY_BACKOFF_FACTOR * (2 ** (attempt - 1))
        logger.debug("Backing off %.2fs", delay)
        time.sleep(delay)
