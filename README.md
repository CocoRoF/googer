# Googer (Rust-Powered)

A powerful, type-safe Google Search library for Python — with a **Rust** core for maximum performance.

## Features

- **Rust Core**: HTTP requests, HTML parsing, and text normalization all run in native Rust code via PyO3
- **Type-Safe**: Full type stubs (`.pyi`) for IDE autocompletion and static analysis
- **Multiple Search Types**: Web, Images, News, and Videos
- **Advanced Query Builder**: Fluent, chainable API for complex Google search queries
- **Rate-Limit Detection**: Automatic retry with User-Agent rotation
- **Proxy Support**: HTTP, HTTPS, SOCKS5 (including Tor Browser shortcut)
- **CLI**: Full-featured command-line interface via Click

## Installation

```bash
pip install googer
```

### Build from source

Requires Rust toolchain and maturin:

```bash
pip install maturin
maturin develop --release
```

## Quick Start

### Python API

```python
from googer import Googer

results = Googer().search("python programming")
for r in results:
    print(r.title, r.href)
```

### Advanced Query Builder

```python
from googer import Googer, Query

q = Query("machine learning").site("arxiv.org").filetype("pdf")
results = Googer().search(str(q), max_results=20)
```

### Search Categories

```python
g = Googer()

# Web search
text_results = g.search("python programming")

# Image search
image_results = g.images("cute cats", size="large")

# News search
news_results = g.news("artificial intelligence", timelimit="d")

# Video search
video_results = g.videos("python tutorial", duration="short")
```

### Context Manager & Proxy

```python
with Googer(proxy="socks5h://127.0.0.1:9150", timeout=15) as g:
    results = g.search("privacy tools")
```

## CLI Usage

```bash
googer search -q "python programming" --max-results 5
googer news -q "artificial intelligence" --timelimit d
googer images -q "cute cats" --size large
googer videos -q "python tutorial" --duration short
```

## Architecture

```
googer (Python package)
├── __init__.py          # Public API, lazy imports from _core
├── _core.pyi            # Type stubs for the Rust module
├── cli.py               # Click-based CLI (Python)
└── _core                # Native Rust extension (PyO3)
    ├── Googer           # Main search facade
    ├── Query            # Fluent query builder
    ├── TextResult       # Web search result type
    ├── ImageResult      # Image search result type
    ├── NewsResult       # News search result type
    ├── VideoResult      # Video search result type
    └── Exceptions       # GoogerException hierarchy
```

### Rust Modules

| Module | Description |
|--------|-------------|
| `config` | Constants & configuration maps |
| `exceptions` | Error types (Rust + Python) |
| `user_agents` | Rotating GSA/Chrome User-Agent strings |
| `utils` | URL/text normalization, proxy expansion |
| `results` | Result structs with PyO3 wrappers |
| `query_builder` | Fluent query builder |
| `http_client` | reqwest-based HTTP client with retries |
| `parser` | CSS-selector-based HTML parser (scraper) |
| `ranker` | Simple relevance ranker |
| `engines/` | Text, Image, News, Video search engines |

## Requirements

- Python ≥ 3.10
- Rust toolchain (for building from source)
- click ≥ 8.1.8 (for CLI)

## License

Apache-2.0
