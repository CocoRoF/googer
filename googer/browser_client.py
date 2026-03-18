"""Browser client for Googer.

Uses `patchright <https://github.com/patchright/patchright>`_ (a patched
Playwright) to render JavaScript-heavy Google search pages in a real
Chromium browser, bypassing bot detection.

Install the browser extra::

    pip install googer[browser]
    patchright install chromium

"""

import logging
import time
from typing import Any
from urllib.parse import urlencode

from .exceptions import GoogerException, RateLimitException
from .http_client import Response

logger = logging.getLogger(__name__)


class BrowserClient:
    """Browser-based client using patchright for JS rendering.

    Launches a real Chromium browser to render Google search pages,
    bypassing JavaScript-only rendering that blocks HTTP-only clients.

    The browser instance is reused across requests for efficiency and
    automatically cleaned up when :meth:`close` is called or the
    context manager exits.

    Args:
        proxy: Proxy URL (``http://``, ``https://``, ``socks5://``).
        timeout: Page load timeout in seconds.  Defaults to 30.
        headless: Run browser without a visible window.
            Defaults to ``True``.  Set to ``False`` for headed mode
            (useful for debugging or manual CAPTCHA solving).
        captcha_wait: When ``True`` (default) and running in **headed** mode,
            pause and wait for the user to solve a CAPTCHA manually
            in the browser window instead of raising immediately.
            Ignored in headless mode.
        captcha_timeout: Maximum seconds to wait for CAPTCHA solve.
            Defaults to 120.  Only effective in headed mode with
            *captcha_wait* enabled.

    Example::

        >>> from googer.browser_client import BrowserClient
        >>> client = BrowserClient()
        >>> resp = client.get("https://www.google.com/search", params={"q": "test"})
        >>> client.close()

    """

    def __init__(
        self,
        proxy: str | None = None,
        timeout: int | None = 30,
        *,
        headless: bool = True,
        captcha_wait: bool = True,
        captcha_timeout: int = 120,
    ) -> None:
        self._proxy = proxy
        self._timeout = (timeout or 30) * 1000  # milliseconds
        self._headless = headless
        self._captcha_wait = captcha_wait
        self._captcha_timeout = captcha_timeout

        # Lazily initialised browser components
        self._pw: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._page: Any = None

    # -- lazy browser lifecycle --------------------------------------------

    def _ensure_browser(self) -> None:
        """Launch the browser on first use."""
        if self._browser is not None:
            return

        try:
            from patchright.sync_api import sync_playwright  # noqa: PLC0415
        except ImportError:
            msg = (
                "patchright is required for browser backend. "
                "Install with:  pip install googer[browser]  &&  patchright install chromium"
            )
            raise GoogerException(msg) from None

        self._pw = sync_playwright().start()

        launch_args: list[str] = [
            "--disable-blink-features=AutomationControlled",
        ]

        launch_kwargs: dict[str, Any] = {
            "headless": self._headless,
            "channel": "chrome",
            "args": launch_args,
        }
        if self._proxy:
            launch_kwargs["proxy"] = {"server": self._proxy}

        self._browser = self._pw.chromium.launch(**launch_kwargs)
        self._context = self._browser.new_context(
            locale="en-US",
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )

        # Skip the EU cookie consent dialog
        self._context.add_cookies(
            [
                {
                    "name": "CONSENT",
                    "value": "YES+cb.20240101-00-p0.en+FX+111",
                    "domain": ".google.com",
                    "path": "/",
                },
            ]
        )

        self._page = self._context.new_page()
        logger.debug("Browser launched (headless=%s)", self._headless)

    # -- HttpClient-compatible interface -----------------------------------

    def get(self, url: str, **kwargs: Any) -> Response:  # noqa: ANN401
        """Navigate to *url* and return the rendered HTML.

        Accepts a ``params`` dict that is URL-encoded and appended
        to the URL, matching the :class:`HttpClient.get` signature.

        Args:
            url: Target URL.
            **kwargs: Supports ``params`` dict for query parameters.

        Returns:
            A :class:`Response` containing the fully rendered page HTML.

        Raises:
            RateLimitException: If a CAPTCHA or rate-limit page is detected.
            GoogerException: On any other browser error.

        """
        self._ensure_browser()

        params = kwargs.get("params")
        if params:
            url = f"{url}?{urlencode(params)}"

        try:
            self._page.goto(url, timeout=self._timeout)

            # If Google redirects to a CAPTCHA page, handle it
            if self._is_rate_limited():
                if self._captcha_wait and not self._headless:
                    self._wait_for_captcha_solve()
                else:
                    logger.warning("Rate limit / CAPTCHA detected in browser response")
                    raise RateLimitException(
                        "Google CAPTCHA detected. Try again later or use a different IP."
                    )

            # Wait for search results to render
            try:
                self._page.wait_for_selector("h3", timeout=15000)
            except Exception:  # noqa: BLE001
                # Might be empty results or non-text search page.
                # Fall back to waiting for the search container.
                try:
                    self._page.wait_for_selector("#search, #rso", timeout=5000)
                except Exception:  # noqa: BLE001
                    pass  # Use whatever has rendered so far

            # Brief pause for any final JS rendering
            time.sleep(0.5)

            html = self._page.content()

            # Final CAPTCHA check after rendering
            if self._is_rate_limited():
                logger.warning("Rate limit / CAPTCHA detected in browser response")
                raise RateLimitException(
                    "Google CAPTCHA detected. Try again later or use a different IP."
                )

            return Response(
                status_code=200,
                content=html.encode("utf-8"),
                text=html,
            )

        except RateLimitException:
            raise
        except Exception as exc:
            logger.exception("Browser navigation failed")
            msg = f"Browser request failed: {exc}"
            raise GoogerException(msg) from exc

    def post(self, url: str, **kwargs: Any) -> Response:  # noqa: ANN401
        """POST is unsupported in browser mode; delegates to GET."""
        return self.get(url, **kwargs)

    def update_headers(self, headers: dict[str, str]) -> None:
        """Set extra HTTP headers on the browser context."""
        if self._context is not None:
            self._context.set_extra_http_headers(headers)

    def rotate_user_agent(self) -> None:
        """No-op — the browser manages its own User-Agent."""

    # -- CAPTCHA handling ---------------------------------------------------

    def _wait_for_captcha_solve(self) -> None:
        """Wait for the user to solve a CAPTCHA in the visible browser.

        In headed mode, the browser window is visible and the user
        can interact with it to solve the CAPTCHA.  This method polls
        until the page navigates away from the ``/sorry/`` URL.

        Raises:
            RateLimitException: If the user does not solve the CAPTCHA within
                the configured timeout.

        """
        logger.warning(
            "CAPTCHA detected — please solve it in the browser window "
            "(timeout: %ds)",
            self._captcha_timeout,
        )

        deadline = time.monotonic() + self._captcha_timeout
        while time.monotonic() < deadline:
            if not self._is_rate_limited():
                logger.info("CAPTCHA solved! Resuming search.")
                return
            time.sleep(1)

        raise RateLimitException(
            f"CAPTCHA not solved within {self._captcha_timeout}s. "
            "Try again later or use a different IP."
        )

    # -- rate-limit detection ------------------------------------------------

    _CAPTCHA_SIGNALS = (
        "detected unusual traffic",
        "/sorry/",
    )

    def _is_rate_limited(self) -> bool:
        """Check visible page content for CAPTCHA / rate-limit signals.

        We inspect the page title and URL rather than the raw HTML
        because Google embeds ``"recaptcha"`` strings in script bundles
        on normal result pages.
        """
        try:
            url = self._page.url.lower()
            title = self._page.title().lower()
            visible = f"{url} {title}"
            return any(sig in visible for sig in self._CAPTCHA_SIGNALS)
        except Exception:  # noqa: BLE001
            return False

    # -- cleanup -----------------------------------------------------------

    def close(self) -> None:
        """Release all browser resources."""
        for attr in ("_page", "_context", "_browser"):
            obj = getattr(self, attr, None)
            if obj is not None:
                try:
                    obj.close()
                except Exception:  # noqa: BLE001
                    pass
                setattr(self, attr, None)

        if self._pw is not None:
            try:
                self._pw.stop()
            except Exception:  # noqa: BLE001
                pass
            self._pw = None

        logger.debug("Browser closed")

    def __del__(self) -> None:
        """Best-effort cleanup on garbage collection."""
        self.close()
