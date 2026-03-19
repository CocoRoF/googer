# Googer

**A multi-engine search library for Python supporting 7 search engines.**

DuckDuckGo · Brave · Google · Ecosia · Yahoo · AOL · Naver — unified search through a single API.

[한국어 문서 (Korean)](README_KO.md)

## Installation

```bash
pip install googer
```

## Quick Start

```python
from googer import Googer

# Search (default: auto mode — automatic engine selection with fallback)
results = Googer().search("python programming")
for r in results:
    print(r.title, r.href)
```

## Engine Selection

```python
from googer import Googer

# Use a specific engine
g = Googer(engine="brave")
results = g.search("rust language")

# Multi-engine — query multiple engines concurrently and merge results
g = Googer(engine="multi")
results = g.search("machine learning")

# Override engine per method call
g = Googer(engine="duckduckgo")
results = g.search("AI news", engine="naver")  # uses Naver for this call only
```

### Supported Engines

| Engine | Text | Images | News | Videos |
|--------|:----:|:------:|:----:|:------:|
| `duckduckgo` | ✅ | ✅ | ✅ | ✅ |
| `brave` | ✅ | | ✅ | ✅ |
| `google` | ✅ | ✅ | ✅ | ✅ |
| `ecosia` | ✅ | | | |
| `yahoo` | ✅ | | | |
| `aol` | ✅ | | | |
| `naver` | ✅ | | | |

### Engine Modes

| Mode | Description |
|------|-------------|
| `auto` | Default. Tries engines in fallback order, uses the first that succeeds |
| `multi` | Queries multiple engines concurrently, merges and deduplicates results |
| `duckduckgo`, `brave`, ... | Uses only the specified engine |

## Search Types

```python
from googer import Googer

g = Googer()

# Text search
results = g.search("python", region="ko-kr", max_results=20)

# Image search
images = g.images("cute cats", size="large", color="color")
for img in images:
    print(img.title, img.image)

# News search (last 24 hours)
news = g.news("AI", timelimit="d")
for n in news:
    print(n.title, n.source, n.date)

# Video search (short videos only)
videos = g.videos("python tutorial", duration="short")

# Autocomplete suggestions
suggestions = g.suggest("python")

# Instant answer
answer = g.answers("python release date")
```

## Advanced Queries

```python
from googer import Googer, Query

q = (
    Query("machine learning")
    .exact("neural network")
    .site("arxiv.org")
    .filetype("pdf")
    .exclude("tutorial")
)

results = Googer().search(q, max_results=20)
```

## Proxy & Context Manager

```python
from googer import Googer

# With proxy (also supports GOOGER_PROXY env var)
with Googer(proxy="socks5://127.0.0.1:9150") as g:
    results = g.search("privacy tools")

# Tor Browser shorthand
with Googer(proxy="tb") as g:
    results = g.search("onion sites")
```

## All Options

```python
g = Googer(
    engine="auto",          # auto | multi | duckduckgo | brave | google | ecosia | yahoo | aol | naver
    proxy=None,             # Proxy URL (http/https/socks5)
    timeout=10,             # Request timeout in seconds
    max_retries=3,          # Number of retries
    cache_ttl=300,          # Cache TTL in seconds (0 to disable)
    backend="http",         # http | browser
    headless=True,          # Headless mode when using browser backend
    verify=True,            # SSL certificate verification
)
```

## CLI

```bash
# Text search
googer search -q "python programming" -m 5

# Specify engine
googer search -q "news" --engine naver

# Multi-engine search
googer search -q "AI" --engine multi

# News (past week)
googer news -q "AI" -t w

# Images
googer images -q "landscape" --size large

# Videos
googer videos -q "cooking" --duration short

# Suggestions
googer suggest -q "python"

# Save results
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
| `--engine` | | Engine selection (default: `auto`) |
| `--region` | `-r` | Region code (default: `us-en`) |
| `--safesearch` | `-s` | `on` / `moderate` / `off` |
| `--timelimit` | `-t` | `h` (hour) `d` (day) `w` (week) `m` (month) `y` (year) |
| `--max-results` | `-m` | Maximum number of results (default: `10`) |
| `--backend` | | `http` / `browser` |
| `--proxy` | | Proxy URL |
| `--timeout` | | Timeout in seconds (default: `10`) |
| `--output` | `-o` | Save to `.json` or `.csv` file |
| `--no-color` | | Disable colored output |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGER_PROXY` | Default proxy URL |

## Requirements

- Python 3.10+
- [primp](https://github.com/deedy5/primp) — HTTP client with TLS fingerprint impersonation
- [lxml](https://lxml.de/) — HTML parsing
- [click](https://click.palletsprojects.com/) — CLI framework

## License

Apache License 2.0 — [LICENSE.md](LICENSE.md)
