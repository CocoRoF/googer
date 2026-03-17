# Googer

**A powerful, type-safe Google Search library for Python.**

Googer provides an elegant Python interface for querying Google Search and receiving structured, typed results. Built with robustness in mind — featuring automatic retries, rate-limit detection, TLS fingerprint impersonation, and a fluent query builder.

## Features

- **Web Search** — Full-text Google web search with pagination
- **Image Search** — Google Images with size, color, type, and license filters
- **News Search** — Google News with time filtering
- **Video Search** — Google Videos with duration filtering
- **Advanced Query Builder** — Fluent API for complex Google operators (`site:`, `filetype:`, `intitle:`, exact phrases, exclusions, date ranges, etc.)
- **Anti-Detection** — Rotating User-Agents (GSA/Chrome), TLS fingerprint impersonation via `primp`
- **Automatic Retries** — Exponential back-off with configurable retry count
- **Rate-Limit Detection** — Detects CAPTCHA/rate-limit pages and raises clear exceptions
- **Proxy Support** — HTTP, HTTPS, SOCKS5 (with Tor Browser shorthand `"tb"`)
- **CLI Tool** — `googer` command-line interface for all search types
- **Type-Safe** — Full type annotations, `py.typed` marker, mypy-strict compatible

## Installation

```bash
pip install googer
```

## Quick Start

### Python API

```python
from googer import Googer

# Simple search
results = Googer().search("python programming")
for r in results:
    print(r.title, r.href)
```

### Advanced Query Builder

```python
from googer import Googer, Query

# Build a complex query with operators
q = (
    Query("machine learning")
    .exact("neural network")
    .site("arxiv.org")
    .filetype("pdf")
    .exclude("tutorial")
)

results = Googer().search(q, max_results=20)
```

### Search Categories

```python
from googer import Googer

g = Googer()

# Web search
web = g.search("python", region="ko-kr", max_results=10)

# Image search with filters
images = g.images("cute cats", size="large", color="color")
for img in images:
    print(img.title, img.image)

# News search — last 24 hours
news = g.news("artificial intelligence", timelimit="d")
for n in news:
    print(n.title, n.source, n.date)

# Video search — short videos only
videos = g.videos("python tutorial", duration="short")
for v in videos:
    print(v.title, v.url, v.duration)
```

### Context Manager & Proxy

```python
from googer import Googer

# With proxy (also supports GOOGER_PROXY env var)
with Googer(proxy="socks5://127.0.0.1:9150") as g:
    results = g.search("privacy tools")

# Tor Browser shorthand
with Googer(proxy="tb") as g:
    results = g.search("onion sites")
```

## CLI

```bash
# Web search
googer search -q "python programming" -m 5

# News — past week
googer news -q "AI" -t w

# Images — large, creative commons
googer images -q "landscape" --size large --license creative_commons

# Videos — short duration
googer videos -q "cooking" --duration short

# Save to file
googer search -q "python" -o results.json
googer search -q "python" -o results.csv

# With proxy
googer search -q "python" --proxy socks5://127.0.0.1:9150

# Version
googer version
```

### CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--query` | `-q` | Search query (required) |
| `--region` | `-r` | Region code (default: `us-en`) |
| `--safesearch` | `-s` | `on`, `moderate`, `off` (default: `moderate`) |
| `--timelimit` | `-t` | `h` (hour), `d` (day), `w` (week), `m` (month), `y` (year) |
| `--max-results` | `-m` | Maximum results (default: `10`) |
| `--proxy` | | Proxy URL |
| `--timeout` | | Timeout in seconds (default: `10`) |
| `--output` | `-o` | Save to `.json` or `.csv` file |
| `--no-color` | | Disable colored output |

## Configuration

| Environment Variable | Description |
|-------------------|----|
| `GOOGER_PROXY` | Default proxy URL |

## Architecture

```
googer/
├── __init__.py          # Public API: Googer, Query
├── googer.py            # Main Googer class (orchestrator)
├── config.py            # Constants, URLs, XPath selectors
├── exceptions.py        # Exception hierarchy
├── http_client.py       # HTTP client with retries & anti-detection
├── parser.py            # XPath-based HTML parser
├── query_builder.py     # Fluent query builder (Query)
├── results.py           # Typed result dataclasses
├── user_agents.py       # User-Agent rotation
├── ranker.py            # Relevance ranking
├── utils.py             # Text/URL normalization helpers
├── cli.py               # Click-based CLI
└── engines/
    ├── base.py          # Abstract base engine
    ├── text.py          # Web/text search
    ├── images.py        # Image search
    ├── news.py          # News search
    └── videos.py        # Video search
```

## Requirements

- Python 3.10+
- [primp](https://github.com/deedy5/primp) — HTTP client with TLS impersonation
- [lxml](https://lxml.de/) — Fast HTML/XML parsing
- [click](https://click.palletsprojects.com/) — CLI framework

## License

Apache License 2.0. See [LICENSE.md](LICENSE.md) for details.
