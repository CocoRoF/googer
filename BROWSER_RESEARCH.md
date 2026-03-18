# Browser / JS Rendering Research for Google Search Scraping (2025-2026)

> **Date:** March 18, 2026
> **Context:** googer library currently uses `primp` (HTTP-only with TLS impersonation). Google now serves 100% JS-rendered pages, returning empty `<noscript>` shells to HTTP-only clients.

---

## Table of Contents
1. [The Problem](#the-problem)
2. [Package Comparison Table](#package-comparison-table)
3. [Detailed Package Analysis](#detailed-package-analysis)
4. [How Other Libraries Handle This](#how-other-libraries-handle-this)
5. [Non-Browser Approaches](#non-browser-approaches)
6. [Code Examples](#code-examples)
7. [Recommendation](#recommendation)

---

## The Problem

Google Search has progressively moved to JavaScript-rendered results. When using HTTP-only clients like `primp`, `requests`, or `httpx`, Google returns:
- Empty `<noscript>` pages with no search results
- Pages that require JS execution to render actual result links
- CAPTCHA/bot-detection pages (403s, "unusual traffic" interstitials)

The `googlesearch-python` library (Nv7-GitHub) worked around this temporarily by switching to a Lynx user-agent (release v1.3.0, Jan 2025), which makes Google serve a simplified HTML page. However, this is fragile and Google could block it at any time .

**We need a reliable JS rendering solution that:**
- Is lightweight enough to bundle as an optional dependency in a library
- Can bypass Google's bot detection
- Works in both headless and headful modes

---

## Package Comparison Table

| Feature | **nodriver** | **zendriver** | **patchright** | **camoufox** | **playwright** | **rebrowser-playwright** | **DrissionPage** |
|---|---|---|---|---|---|---|---|
| **PyPI Package Size** | ~150 KB (pure Python) | ~200 KB (pure Python) | ~400 KB (Python wrapper) | ~2 MB (Python wrapper) | ~400 KB (Python wrapper) | ~400 KB (Python wrapper) | ~1.5 MB (pure Python) |
| **Browser Binary Needed** | Uses system Chrome/Chromium (already installed) | Uses system Chrome/Chromium | **Must download Chromium** (~150 MB via `patchright install chromium`) | **Must download Camoufox browser** (~200 MB via `camoufox fetch`) | **Must download browser** (~150 MB via `playwright install chromium`) | **Must download browser** (~150 MB) | Uses system Chrome/Edge |
| **Anti-Detection** | ✅ Excellent (built-in, no webdriver leak) | ✅ Excellent (same as nodriver) | ✅ Excellent (Runtime.enable patched, passes Cloudflare/Datadome/etc.) | ✅ Best-in-class (Firefox-based fingerprint rotation, BrowserForge) | ❌ Easily detected | ✅ Good (rebrowser-patches applied) | ✅ Good (no webdriver, CDP-based) |
| **API Style** | Async only | Async only | Sync + Async | Sync + Async (via Playwright) | Sync + Async | Sync + Async | Sync only |
| **Min Python** | 3.9 | 3.10 | 3.9 | 3.8 | 3.9 | 3.9 | 3.6 |
| **Latest Release** | Nov 9, 2025 (v0.48.1) | Mar 12, 2026 (v0.15.3) | Mar 7, 2026 (v1.58.2) | Jan 29, 2025 (v0.4.11) | Jan 31, 2026 (v1.58.0) | May 9, 2025 (v1.52.0) | Mar 21, 2025 (v4.1.0.17) |
| **Actively Maintained** | ⚠️ Slow (restricted contributions) | ✅ Yes (community fork of nodriver) | ✅ Yes (auto-deployed) | ✅ Yes | ✅ Yes (Microsoft) | ⚠️ Lags behind playwright | ✅ Yes (CN community) |
| **Stars** | ~13K (ultrafunkamsterdam) | ~1.5K | ~1.2K | ~5K | ~12K | ~500 | ~11.6K |
| **License** | AGPL-3.0 ⚠️ | AGPL-3.0 ⚠️ | Apache-2.0 ✅ | MIT ✅ | Apache-2.0 ✅ | Apache-2.0 ✅ | Custom (non-commercial) ⚠️ |
| **Library-Friendly** | ✅ Good | ✅ Good | ✅ Excellent | ✅ Good | ✅ Excellent | ✅ Good | ⚠️ Moderate (CN docs only) |
| **Protocol** | CDP (Chrome DevTools Protocol) | CDP | CDP (via Playwright driver) | CDP (via Playwright, Firefox) | CDP/custom WebSocket | CDP (patched) | CDP (self-implemented) |
| **Dependencies** | websockets only | websockets, mss | greenlet, pyee | playwright, browserforge, many more | greenlet, pyee | greenlet, pyee | requests, lxml, websocket-client |

---

## Detailed Package Analysis

### 1. nodriver (v0.48.1)
**Author:** UltrafunkAmsterdam (creator of undetected-chromedriver)

**Pros:**
- 🪶 **Lightest weight** — pure Python, ~150 KB, only needs `websockets`
- 🛡️ No selenium/webdriver — communicates via CDP directly
- 🖥️ Uses **system-installed Chrome** — no separate download needed
- 🔒 Built-in anti-detection (no webdriver leak, clean automation flags)
- 🧹 Fresh profile per run, auto-cleanup
- Known to work with Chrome, Edge, Brave

**Cons:**
- ⚠️ **AGPL-3.0 license** — viral copyleft, problematic for Apache-2.0 library
- Async-only API (requires asyncio wrapper for sync usage)
- Maintenance slowing down — PR merges restricted
- Alpha status (`Development Status :: 3 - Alpha`)

**Weight:** ~150 KB + system Chrome (already present on most machines)

---

### 2. zendriver (v0.15.3) — **RECOMMENDED for async**
**Author:** Stephan Lensky (community fork of nodriver)

**Pros:**
- 🪶 Same lightweight architecture as nodriver
- ✅ **Actively maintained** — open PRs, bug fixes merged, ruff/mypy, codecov
- 🛡️ Same anti-detection as nodriver
- 🖥️ Uses system Chrome — no download needed
- 🐳 First-class Docker support (zendriver-docker project)
- Modern tooling (ruff, mypy, static analysis)

**Cons:**
- ⚠️ **AGPL-3.0 license** — same copyleft issue
- Async-only
- Newer project, smaller community
- Python 3.10+ required (vs googer's 3.10+ — this matches!)

**Weight:** ~200 KB + system Chrome

---

### 3. patchright (v1.58.2) — **RECOMMENDED for sync + anti-detection**
**Author:** Vinyzu / Kaliiiiiiiiii

**Pros:**
- ✅ **Apache-2.0 license** — compatible with googer!
- 🔄 **Drop-in replacement** for Playwright (same API, same imports minus name)
- 🛡️ **Best stealth for Chromium** — patches Runtime.enable, Console.enable, command flags
- Passes Cloudflare, Kasada, Akamai, Datadome, Fingerprint.com, etc.
- Sync AND Async API
- Can use system Chrome (`channel="chrome"`) — avoids ~150MB download
- Auto-deployed when upstream Playwright updates

**Cons:**
- Requires browser binary download if system Chrome not used
- Slightly heavier than nodriver (Playwright driver binary ~5 MB)
- Only patches Chromium (not Firefox/WebKit)
- Console functionality disabled (needed for stealth)

**Weight:** ~400 KB Python + ~5 MB driver binary + system Chrome OR ~150 MB downloaded Chromium

**Best practice for anti-detection:**
```python
# Use system Chrome, not downloaded Chromium
patchright install chrome  # or just use channel="chrome" if Chrome is installed
```

---

### 4. camoufox (v0.4.11)
**Author:** daijro

**Pros:**
- 🛡️ **Best-in-class fingerprint rotation** (OS, fonts, WebGL, navigator, etc.)
- Uses BrowserForge for statistically realistic device characteristics
- GeoIP-based locale/timezone matching (proxy detection avoidance)
- Humanized cursor movement
- Firefox-based (different detection surface than Chrome)
- MIT license ✅

**Cons:**
- 🏋️ **Heaviest option** — requires downloading custom Camoufox browser (~200+ MB)
- Many dependencies (playwright, browserforge, and more)
- Firefox-based means different CSS/rendering behavior
- Overkill for simple search scraping

**Weight:** ~2 MB Python + ~200 MB Camoufox browser download

---

### 5. playwright (v1.58.0)
**Author:** Microsoft

**Pros:**
- 🏢 Industry standard, excellent docs, professional support
- Sync + Async API
- Multi-browser (Chromium, Firefox, WebKit)
- Apache-2.0 ✅

**Cons:**
- ❌ **Easily detected by Google** — exposes automation markers
- Requires browser download (~150 MB)
- Not stealth by default — needs manual tweaking

**Weight:** ~400 KB Python + ~150 MB browser download

---

### 6. rebrowser-playwright (v1.52.0)
**Author:** rebrowser.net

**Pros:**
- Drop-in replacement for Playwright with anti-detection patches
- Apache-2.0 ✅

**Cons:**
- ⚠️ Lags behind official Playwright (currently v1.52 vs official v1.58)
- Less mature than patchright
- Same download requirements as Playwright

---

### 7. DrissionPage (v4.1.0.17/4.1.1.2)
**Author:** g1879

**Pros:**
- 🪶 Lightweight, self-implemented CDP client
- Uses system Chrome/Edge
- Can combine browser control + HTTP requests
- No webdriver dependency
- 11.6K GitHub stars

**Cons:**
- ⚠️ **Custom license** — prohibits commercial use without authorization
- Documentation primarily in Chinese
- Sync-only
- Less familiar API for Western developers

---

## How Other Libraries Handle This

### DDGS (duckduckgo_search, now renamed to `ddgs`) — deedy5
- **Approach:** Uses `primp` HTTP client (same as googer!) with TLS impersonation
- **Search engines supported:** google, bing, brave, duckduckgo, mojeek, yandex, yahoo, wikipedia — it's a **metasearch engine**, not a single-source scraper
- **Key insight:** For Google backend, they likely send requests to Google and parse the response HTML — same approach googer uses. The JS-rendering problem would affect them too.
- **Workaround:** Uses multiple backend engines, so if Google fails, falls back to others.

### googlesearch-python (Nv7-GitHub)
- **Approach:** Uses `requests` + `BeautifulSoup` with **Lynx user-agent** trick
- **Latest release** (v1.3.0, Jan 2025): "Use Lynx useragent to fix empty results"
- When Google sees a Lynx user-agent, it serves simplified text-only HTML
- **Fragile:** Google can break this at any time

### SerpAPI / Oxylabs / HasData (commercial)
- Use rotating proxy networks + custom rendering infrastructure
- Not a library — paid API services
- Cost: $50-500+/month for meaningful usage

### nagooglesearch
- Uses `requests` with custom headers — same vulnerability to JS rendering issue

---

## Non-Browser Approaches

### 1. Lynx User-Agent Trick (lightest, but fragile)
```python
headers = {"User-Agent": "Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/0.8.12"}
# Google serves simplified text-only HTML for text-mode browsers
```
- **Pro:** Zero extra dependencies, extremely fast
- **Con:** Google could block this ANY time. Not reliable long-term.

### 2. Google's `&udm=14` Parameter (Web filter)
```
https://www.google.com/search?q=test&udm=14
```
- Returns Google "Web" results with a simpler page structure
- Still may require JS rendering in 2026

### 3. Google Custom Search API (official)
```python
# 100 queries/day free, then $5/1000 queries
import requests
resp = requests.get("https://www.googleapis.com/customsearch/v1", params={
    "key": API_KEY, "cx": CSE_ID, "q": "search query"
})
```
- **Pro:** Official, reliable, no bot detection
- **Con:** Rate-limited (100/day free), costs money, limited to 10K/day paid

### 4. Extracting Data from Google's JS Payload
Google embeds search result data in script tags as serialized protocol buffer / JSON structures. These can potentially be extracted without rendering JS:
```python
# Look for patterns like: AF_initDataCallback({key: 'ds:1', data: [...]})
# or nested arrays in <script> tags
```
- **Pro:** No browser needed, fast
- **Con:** Extremely fragile, format changes without notice, complex parsing

---

## Code Examples

### Example 1: zendriver (Lightweight, Async)
```python
import asyncio
import zendriver as zd

async def google_search(query: str) -> str:
    browser = await zd.start(headless=True)
    try:
        page = await browser.get(f"https://www.google.com/search?q={query}&hl=en")
        # Wait for results to render
        await page.select("div#search", timeout=10)
        html = await page.get_content()
        return html
    finally:
        await browser.stop()

html = asyncio.run(google_search("python programming"))
```

### Example 2: patchright (Sync, Anti-Detection)
```python
from patchright.sync_api import sync_playwright

def google_search(query: str) -> str:
    with sync_playwright() as p:
        # Use system Chrome for best stealth
        browser = p.chromium.launch(
            channel="chrome",   # uses system Chrome
            headless=True,
        )
        page = browser.new_page()
        page.goto(f"https://www.google.com/search?q={query}&hl=en")
        page.wait_for_selector("div#search", timeout=10000)
        html = page.content()
        browser.close()
        return html

html = google_search("python programming")
```

### Example 3: patchright (Async, Anti-Detection)
```python
import asyncio
from patchright.async_api import async_playwright

async def google_search(query: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",
            headless=True,
        )
        page = await browser.new_page()
        await page.goto(f"https://www.google.com/search?q={query}&hl=en")
        await page.wait_for_selector("div#search", timeout=10000)
        html = await page.content()
        await browser.close()
        return html

html = asyncio.run(google_search("python programming"))
```

### Example 4: nodriver (Async, Zero-Download)
```python
import nodriver as uc

async def google_search(query: str) -> str:
    browser = await uc.start(headless=True)
    page = await browser.get(f"https://www.google.com/search?q={query}&hl=en")
    await page.select("div#search", timeout=10)
    html = await page.get_content()
    browser.stop()
    return html

uc.loop().run_until_complete(google_search("python programming"))
```

### Example 5: camoufox (Sync, Maximum Stealth)
```python
from camoufox.sync_api import Camoufox

def google_search(query: str) -> str:
    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        page.goto(f"https://www.google.com/search?q={query}&hl=en")
        page.wait_for_selector("div#search", timeout=10000)
        html = page.content()
        return html

html = google_search("python programming")
```

### Example 6: Integration Pattern for googer (Optional Browser Backend)
```python
# googer/browser_client.py — optional browser-based client
"""Browser-based HTTP client for JS-rendered pages.

Requires: pip install googer[browser]
Which installs: patchright

Usage is transparent — falls back from primp to browser automatically.
"""

class BrowserClient:
    """Headless browser client using patchright for JS rendering."""

    def __init__(self, headless=True, channel="chrome"):
        self._headless = headless
        self._channel = channel
        self._playwright = None
        self._browser = None

    def __enter__(self):
        from patchright.sync_api import sync_playwright
        self._pw_context = sync_playwright()
        self._playwright = self._pw_context.__enter__()
        self._browser = self._playwright.chromium.launch(
            channel=self._channel,
            headless=self._headless,
        )
        return self

    def __exit__(self, *args):
        if self._browser:
            self._browser.close()
        if self._pw_context:
            self._pw_context.__exit__(*args)

    def get_rendered_html(self, url: str, wait_selector: str = "div#search", timeout: int = 10000) -> str:
        page = self._browser.new_page()
        try:
            page.goto(url, timeout=timeout)
            page.wait_for_selector(wait_selector, timeout=timeout)
            return page.content()
        finally:
            page.close()
```

---

## Recommendation

### Primary Recommendation: **patchright** (as optional dependency)

| Criterion | Why patchright wins |
|---|---|
| **License** | Apache-2.0 — fully compatible with googer's Apache-2.0 |
| **Anti-detection** | Best stealth for Chromium; patches Runtime.enable, automation flags |
| **API** | Both sync and async; drop-in Playwright API (well-documented) |
| **System Chrome** | Can use `channel="chrome"` to avoid ~150 MB browser download |
| **Maintenance** | Auto-deployed on Playwright updates; actively maintained |
| **Ecosystem** | Playwright is industry-standard; huge community, excellent docs |
| **Library integration** | Perfect for optional dependency pattern (`pip install googer[browser]`) |

### Integration Strategy for googer

```toml
# pyproject.toml
[project.optional-dependencies]
browser = ["patchright>=1.58.0"]
```

```
pip install googer           # HTTP-only (primp) — lightweight, works when Google serves HTML
pip install googer[browser]  # Adds patchright for JS rendering when needed
```

**Fallback chain:**
1. Try `primp` (HTTP-only, fast, lightweight) — works for users with proxies / when Google serves HTML
2. If empty results detected → fall back to `patchright` browser rendering (if installed)
3. If `patchright` not installed → raise clear error suggesting `pip install googer[browser]`

### Why NOT the others?

| Package | Reason to avoid |
|---|---|
| **nodriver/zendriver** | AGPL-3.0 is incompatible with Apache-2.0 library distribution |
| **camoufox** | Too heavy (~200 MB browser download); overkill for search scraping |
| **playwright** | Easily detected by Google; no stealth patches |
| **rebrowser-playwright** | Lags behind official Playwright versions significantly |
| **DrissionPage** | Custom non-commercial license; CN-only docs; sync-only |

### Second Choice: **zendriver** (if AGPL is acceptable)

If the project were AGPL-compatible, zendriver would be the lightest option:
- Pure Python (~200 KB)
- Uses system Chrome (0 bytes extra download)
- Same anti-detection as nodriver
- Actively maintained
- Modern Python tooling

But AGPL-3.0 would require googer to also be AGPL-licensed, which contradicts the current Apache-2.0 license.

---

## Summary: Weight Comparison

| Solution | Python Pkg | Browser Download | Total Footprint | Anti-Detection | License OK? |
|---|---|---|---|---|---|
| primp (current) | ~2 MB | None | ~2 MB | ⚠️ TLS only | ✅ |
| Lynx UA trick | 0 | None | 0 | ❌ Fragile | ✅ |
| zendriver | ~200 KB | None (system Chrome) | ~200 KB | ✅ Excellent | ❌ AGPL |
| nodriver | ~150 KB | None (system Chrome) | ~150 KB | ✅ Excellent | ❌ AGPL |
| **patchright** | **~400 KB** | **None if using system Chrome** | **~5 MB (driver)** | **✅ Excellent** | **✅ Apache-2.0** |
| patchright + download | ~400 KB | ~150 MB Chromium | ~155 MB | ✅ Excellent | ✅ Apache-2.0 |
| camoufox | ~2 MB | ~200 MB Camoufox | ~202 MB | ✅ Best | ✅ MIT |
| playwright | ~400 KB | ~150 MB Chromium | ~155 MB | ❌ Detected | ✅ Apache-2.0 |

**Winner: patchright with `channel="chrome"` (system Chrome) — ~5 MB total, excellent stealth, Apache-2.0 license.**
