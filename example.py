"""googer 사용 예제 스크립트.

실행 전 설치:
    pip install googer[browser]
    patchright install chromium

사용법:
    python example.py
    python example.py --query "machine learning"
    python example.py --query "서울 맛집" --max-results 20
    python example.py --backend http
"""

import argparse
import sys

from googer import Googer


def text_search(query: str, max_results: int = 10, backend: str = "browser") -> None:
    """텍스트 검색 (기본)."""
    print(f"\n{'=' * 60}")
    print(f"  Text Search: {query}")
    print(f"{'=' * 60}")

    with Googer(backend=backend) as g:  # type: ignore[arg-type]
        results = g.search(query, max_results=max_results)

    for i, r in enumerate(results, 1):
        print(f"\n  [{i}] {r.title}")
        print(f"      {r.href}")
        if r.body:
            print(f"      {r.body[:150]}")


def news_search(query: str, max_results: int = 5, backend: str = "browser") -> None:
    """뉴스 검색."""
    print(f"\n{'=' * 60}")
    print(f"  News Search: {query}")
    print(f"{'=' * 60}")

    with Googer(backend=backend) as g:  # type: ignore[arg-type]
        results = g.news(query, max_results=max_results)

    for i, r in enumerate(results, 1):
        print(f"\n  [{i}] {r.title}")
        print(f"      {r.url}")
        if r.source:
            print(f"      source: {r.source}")
        if r.date:
            print(f"      date:   {r.date}")


def video_search(query: str, max_results: int = 5, backend: str = "browser") -> None:
    """비디오 검색."""
    print(f"\n{'=' * 60}")
    print(f"  Video Search: {query}")
    print(f"{'=' * 60}")

    with Googer(backend=backend) as g:  # type: ignore[arg-type]
        results = g.videos(query, max_results=max_results)

    for i, r in enumerate(results, 1):
        print(f"\n  [{i}] {r.title}")
        print(f"      {r.url}")
        if r.duration:
            print(f"      duration: {r.duration}")


def query_builder_search(backend: str = "browser") -> None:
    """Query 빌더 사용 예제."""
    from googer import Query

    print(f"\n{'=' * 60}")
    print("  Query Builder: site:github.com filetype:md")
    print(f"{'=' * 60}")

    q = Query("python tutorial").site("github.com").filetype("md")
    print(f"  Built query: {q}\n")

    with Googer(backend=backend) as g:  # type: ignore[arg-type]
        results = g.search(q, max_results=5)

    for i, r in enumerate(results, 1):
        print(f"  [{i}] {r.title}")
        print(f"      {r.href}")


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description="googer 사용 예제")
    parser.add_argument("--query", "-q", default="python programming", help="검색어")
    parser.add_argument("--max-results", "-n", type=int, default=10, help="최대 결과 수")
    parser.add_argument(
        "--backend", "-b", choices=["browser", "http"], default="browser",
        help="백엔드 (browser=patchright, http=primp)",
    )
    parser.add_argument(
        "--type", "-t", choices=["text", "news", "videos", "query", "all"], default="text",
        help="검색 유형",
    )
    args = parser.parse_args()

    search_type = args.type

    if search_type in ("text", "all"):
        text_search(args.query, args.max_results, args.backend)

    if search_type in ("news", "all"):
        news_search(args.query, max_results=5, backend=args.backend)

    if search_type in ("videos", "all"):
        video_search(args.query, max_results=5, backend=args.backend)

    if search_type in ("query", "all"):
        query_builder_search(args.backend)

    print("\nDone.")


if __name__ == "__main__":
    main()
