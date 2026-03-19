"""Googer example script.

Install before running:
    pip install googer

To use the Google browser backend:
    pip install googer[browser]
    patchright install chromium

Usage:
    python example.py
    python example.py --query "machine learning"
    python example.py --query "python tutorial" --max-results 20
    python example.py --engine google --backend browser
"""

import argparse
import sys

from googer import Googer


def text_search(query: str, max_results: int = 10, engine: str = "auto", backend: str = "http") -> None:
    """Text search (default)."""
    print(f"\n{'=' * 60}")
    print(f"  Text Search [{engine}]: {query}")
    print(f"{'=' * 60}")

    with Googer(engine=engine, backend=backend) as g:  # type: ignore[arg-type]
        results = g.search(query, max_results=max_results)

    for i, r in enumerate(results, 1):
        print(f"\n  [{i}] {r.title}")
        print(f"      {r.href}")
        if r.body:
            print(f"      {r.body[:150]}")


def news_search(query: str, max_results: int = 5, engine: str = "auto", backend: str = "http") -> None:
    """News search."""
    print(f"\n{'=' * 60}")
    print(f"  News Search [{engine}]: {query}")
    print(f"{'=' * 60}")

    with Googer(engine=engine, backend=backend) as g:  # type: ignore[arg-type]
        results = g.news(query, max_results=max_results)

    for i, r in enumerate(results, 1):
        print(f"\n  [{i}] {r.title}")
        print(f"      {r.url}")
        if r.source:
            print(f"      source: {r.source}")
        if r.date:
            print(f"      date:   {r.date}")


def video_search(query: str, max_results: int = 5, engine: str = "auto", backend: str = "http") -> None:
    """Video search."""
    print(f"\n{'=' * 60}")
    print(f"  Video Search [{engine}]: {query}")
    print(f"{'=' * 60}")

    with Googer(engine=engine, backend=backend) as g:  # type: ignore[arg-type]
        results = g.videos(query, max_results=max_results)

    for i, r in enumerate(results, 1):
        print(f"\n  [{i}] {r.title}")
        print(f"      {r.url}")
        if r.duration:
            print(f"      duration: {r.duration}")


def query_builder_search(engine: str = "auto", backend: str = "http") -> None:
    """Query builder example."""
    from googer import Query

    print(f"\n{'=' * 60}")
    print("  Query Builder: site:github.com filetype:md")
    print(f"{'=' * 60}")

    q = Query("python tutorial").site("github.com").filetype("md")
    print(f"  Built query: {q}\n")

    with Googer(engine=engine, backend=backend) as g:  # type: ignore[arg-type]
        results = g.search(q, max_results=5)

    for i, r in enumerate(results, 1):
        print(f"  [{i}] {r.title}")
        print(f"      {r.href}")


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description="googer example")
    parser.add_argument("--query", "-q", default="python programming", help="Search query")
    parser.add_argument("--max-results", "-n", type=int, default=10, help="Max results")
    parser.add_argument(
        "--engine", "-e", choices=["auto", "duckduckgo", "google"], default="auto",
        help="Search engine (auto, duckduckgo, google)",
    )
    parser.add_argument(
        "--backend", "-b", choices=["browser", "http"], default="http",
        help="Backend (browser=patchright, http=primp)",
    )
    parser.add_argument(
        "--type", "-t", choices=["text", "news", "videos", "query", "all"], default="text",
        help="Search type",
    )
    args = parser.parse_args()

    search_type = args.type

    if search_type in ("text", "all"):
        text_search(args.query, args.max_results, args.engine, args.backend)

    if search_type in ("news", "all"):
        news_search(args.query, max_results=5, engine=args.engine, backend=args.backend)

    if search_type in ("videos", "all"):
        video_search(args.query, max_results=5, engine=args.engine, backend=args.backend)

    if search_type in ("query", "all"):
        query_builder_search(args.engine, args.backend)

    print("\nDone.")


if __name__ == "__main__":
    main()
