"""CLI interface for Googer.

Provides a ``googer`` command-line tool built with Click.
Supports text, image, news, and video search with formatted output
and optional JSON/CSV export.  Supports DuckDuckGo, Brave Search,
and Google with automatic fallback, multi-engine concurrent search,
suggestions, and instant answers.

Usage::

    googer search "python programming" --max-results 5
    googer search "python" --engine multi
    googer news "artificial intelligence" --timelimit d
    googer images "cute cats" --size large
    googer videos "python tutorial" --duration short
    googer suggest "python prog"
    googer answers "python programming language"

"""

import csv
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click

from . import __version__
from .googer import Googer

# ---------------------------------------------------------------------------
# Colour palette for terminal output
# ---------------------------------------------------------------------------
_COLORS: dict[int, str] = {
    0: "white",
    1: "cyan",
    2: "green",
    3: "yellow",
    4: "blue",
    5: "magenta",
    6: "bright_cyan",
    7: "bright_green",
}


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _print_results(results: list[Any], *, no_color: bool = False) -> None:
    """Pretty-print results to the terminal."""
    if not results:
        click.echo("No results found.")
        return

    for i, result in enumerate(results, start=1):
        click.secho(f"\n{i}. {'=' * 72}", fg="white" if no_color else "bright_white", bold=True)
        for j, (key, value) in enumerate(result.items()):
            if value:
                color = "white" if no_color else _COLORS.get(j % len(_COLORS), "white")
                width = 300 if key in ("href", "url", "image", "thumbnail") else 78
                text = click.wrap_text(
                    str(value),
                    width=width,
                    initial_indent="",
                    subsequent_indent=" " * 14,
                    preserve_paragraphs=True,
                )
                click.secho(f"  {key:<12}{text}", fg=color)


def _save_json(filepath: Path, data: list[Any]) -> None:
    """Save results as JSON."""
    serializable = [r.to_dict() if hasattr(r, "to_dict") else r for r in data]
    with filepath.open("w", encoding="utf-8") as f:
        f.write(json.dumps(serializable, ensure_ascii=False, indent=2))
    click.echo(f"Saved to {filepath}")


def _save_csv(filepath: Path, data: list[Any]) -> None:
    """Save results as CSV."""
    if not data:
        return
    serializable = [r.to_dict() if hasattr(r, "to_dict") else r for r in data]
    with filepath.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=serializable[0].keys(), quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(serializable)
    click.echo(f"Saved to {filepath}")


def _save_data(
    results: list[Any],
    query: str,
    command: str,
    output: str | None,
) -> None:
    """Optionally save results to a file."""
    if not output:
        return
    if output.endswith(".json"):
        _save_json(Path(output), results)
    elif output.endswith(".csv"):
        _save_csv(Path(output), results)
    else:
        # Auto-generate filename
        sanitized = query.replace(" ", "_")[:50]
        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        _save_json(Path(f"{command}_{sanitized}_{ts}.json"), results)


# ---------------------------------------------------------------------------
# Common Click options
# ---------------------------------------------------------------------------

_common_options = [
    click.option("-q", "--query", required=True, help="Search query string."),
    click.option("-r", "--region", default="us-en", show_default=True, help="Region code (e.g. us-en, ko-kr)."),
    click.option(
        "-s",
        "--safesearch",
        default="moderate",
        type=click.Choice(["on", "moderate", "off"]),
        show_default=True,
        help="Safe-search level.",
    ),
    click.option(
        "-t",
        "--timelimit",
        type=click.Choice(["h", "d", "w", "m", "y"]),
        help="Time filter (hour, day, week, month, year).",
    ),
    click.option(
        "-m",
        "--max-results",
        default=10,
        type=int,
        show_default=True,
        help="Maximum number of results.",
    ),
    click.option("--proxy", default=None, help="Proxy URL (http/https/socks5 or 'tb' for Tor)."),
    click.option("--timeout", default=10, type=int, show_default=True, help="Request timeout in seconds."),
    click.option(
        "--engine",
        type=click.Choice(["auto", "multi", "duckduckgo", "brave", "google", "ecosia", "yahoo", "aol", "naver"]),
        default="auto",
        show_default=True,
        help="Search engine provider.",
    ),
    click.option(
        "--backend",
        type=click.Choice(["http", "browser"]),
        default="http",
        show_default=True,
        help="HTTP backend (browser needed for Google).",
    ),
    click.option("-o", "--output", default=None, help="Save results to file (.json or .csv)."),
    click.option("--no-color", is_flag=True, help="Disable coloured output."),
]


def _add_common_options(func):  # noqa: ANN001, ANN202
    """Decorator that adds common search options to a Click command."""
    for option in reversed(_common_options):
        func = option(func)
    return func


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


@click.group()
@click.version_option(version=__version__, prog_name="googer")
def cli() -> None:
    """Googer \u2014 A powerful multi-engine search CLI."""


def safe_entry_point() -> None:
    """Run the CLI with top-level exception handling."""
    logging.basicConfig(level=logging.WARNING)
    try:
        cli()
    except Exception as exc:  # noqa: BLE001
        click.secho(f"Error: {type(exc).__name__}: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@cli.command()
@_add_common_options
def search(
    query: str,
    region: str,
    safesearch: str,
    timelimit: str | None,
    max_results: int,
    proxy: str | None,
    timeout: int,
    engine: str,
    backend: str,
    output: str | None,
    no_color: bool,
) -> None:
    """Perform a web/text search."""
    g = Googer(proxy=proxy, timeout=timeout, engine=engine, backend=backend)
    results = g.search(
        query,
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        max_results=max_results,
    )
    _print_results(results, no_color=no_color)
    _save_data(results, query, "search", output)


@cli.command()
@_add_common_options
@click.option("--size", type=click.Choice(["large", "medium", "icon"]), help="Image size filter.")
@click.option("--color", type=click.Choice(["color", "gray", "mono", "trans"]), help="Color filter.")
@click.option(
    "--image-type",
    type=click.Choice(["face", "photo", "clipart", "lineart", "animated"]),
    help="Image type filter.",
)
@click.option(
    "--license",
    "license_type",
    type=click.Choice(["creative_commons", "commercial"]),
    help="License filter.",
)
def images(
    query: str,
    region: str,
    safesearch: str,
    timelimit: str | None,
    max_results: int,
    proxy: str | None,
    timeout: int,
    engine: str,
    backend: str,
    output: str | None,
    no_color: bool,
    size: str | None,
    color: str | None,
    image_type: str | None,
    license_type: str | None,
) -> None:
    """Perform an image search."""
    g = Googer(proxy=proxy, timeout=timeout, engine=engine, backend=backend)
    results = g.images(
        query,
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        max_results=max_results,
        size=size,
        color=color,
        image_type=image_type,
        license_type=license_type,
    )
    _print_results(results, no_color=no_color)
    _save_data(results, query, "images", output)


@cli.command()
@_add_common_options
def news(
    query: str,
    region: str,
    safesearch: str,
    timelimit: str | None,
    max_results: int,
    proxy: str | None,
    timeout: int,
    engine: str,
    backend: str,
    output: str | None,
    no_color: bool,
) -> None:
    """Perform a news search."""
    g = Googer(proxy=proxy, timeout=timeout, engine=engine, backend=backend)
    results = g.news(
        query,
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        max_results=max_results,
    )
    _print_results(results, no_color=no_color)
    _save_data(results, query, "news", output)


@cli.command()
@_add_common_options
@click.option(
    "--duration",
    type=click.Choice(["short", "medium", "long"]),
    help="Video duration filter.",
)
def videos(
    query: str,
    region: str,
    safesearch: str,
    timelimit: str | None,
    max_results: int,
    proxy: str | None,
    timeout: int,
    engine: str,
    backend: str,
    output: str | None,
    no_color: bool,
    duration: str | None,
) -> None:
    """Perform a video search."""
    g = Googer(proxy=proxy, timeout=timeout, engine=engine, backend=backend)
    results = g.videos(
        query,
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        max_results=max_results,
        duration=duration,
    )
    _print_results(results, no_color=no_color)
    _save_data(results, query, "videos", output)


@cli.command()
def version() -> None:
    """Print the Googer version."""
    click.echo(__version__)


@cli.command()
@click.option("-q", "--query", required=True, help="Partial search query.")
@click.option("-r", "--region", default="us-en", show_default=True, help="Region code.")
@click.option("--no-color", is_flag=True, help="Disable coloured output.")
def suggest(query: str, region: str, no_color: bool) -> None:
    """Get autocomplete suggestions for a query."""
    g = Googer()
    suggestions = g.suggest(query, region=region)
    if not suggestions:
        click.echo("No suggestions found.")
        return
    for i, s in enumerate(suggestions, start=1):
        color = "white" if no_color else "cyan"
        click.secho(f"  {i}. {s}", fg=color)


@cli.command()
@click.option("-q", "--query", required=True, help="Search query for instant answer.")
@click.option("--no-color", is_flag=True, help="Disable coloured output.")
def answers(query: str, no_color: bool) -> None:
    """Get an instant answer for a query."""
    g = Googer()
    answer = g.answers(query)
    if answer is None:
        click.echo("No instant answer found.")
        return
    if answer.heading:
        click.secho(f"\n  {answer.heading}", fg="white" if no_color else "bright_white", bold=True)
    if answer.abstract:
        text = click.wrap_text(answer.abstract, width=78, initial_indent="  ", subsequent_indent="  ")
        click.secho(text, fg="white" if no_color else "cyan")
    if answer.url:
        click.secho(f"  Source: {answer.url}", fg="white" if no_color else "green")
    if answer.answer:
        click.secho(f"  Answer: {answer.answer}", fg="white" if no_color else "yellow")
    if answer.related:
        click.secho("\n  Related:", fg="white" if no_color else "bright_white", bold=True)
        for topic in answer.related[:5]:
            click.secho(f"    - {topic.get('text', '')[:100]}", fg="white" if no_color else "magenta")
