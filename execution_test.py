"""Googer execution test — perform real Google searches and inspect results.

This is not a pytest suite; it is meant to be run directly to visually
verify live search results.

Usage:
    python execution_test.py
"""

from googer import Googer, Query


def divider(title: str) -> None:
    """Print a section divider."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def test_basic_search() -> None:
    """Basic web search test."""
    divider("1. Basic Web Search: '2025 Korea Series champion'")

    g = Googer()
    results = g.search("2025 KBO Korean Series champion", region="us-en", max_results=5)

    print(f"{len(results)} results\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r.get('title', 'N/A')}")
        print(f"    URL:  {r.get('href', 'N/A')}")
        print(f"    Body: {r.get('body', 'N/A')[:120]}")
        print()


def test_query_builder_search() -> None:
    """Advanced search using the Query builder."""
    divider("2. Query Builder: 'machine learning' + exact('neural network') + site:arxiv.org")

    q = Query("machine learning").exact("neural network").site("arxiv.org")
    print(f"Built query: {q}\n")

    g = Googer()
    results = g.search(q, region="us-en", max_results=5)

    print(f"{len(results)} results\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r.get('title', 'N/A')}")
        print(f"    URL:  {r.get('href', 'N/A')}")
        print(f"    Body: {r.get('body', 'N/A')[:120]}")
        print()


def test_news_search() -> None:
    """News search test."""
    divider("3. News Search: 'artificial intelligence 2025'")

    g = Googer()
    results = g.news("artificial intelligence 2025", region="us-en", max_results=5)

    print(f"{len(results)} results\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r.get('title', 'N/A')}")
        print(f"    URL:    {r.get('href', r.get('url', 'N/A'))}")
        print(f"    Source: {r.get('source', 'N/A')}")
        print(f"    Date:   {r.get('date', 'N/A')}")
        print(f"    Body:   {r.get('body', 'N/A')[:120]}")
        print()


def test_context_manager() -> None:
    """Context manager usage test."""
    divider("4. Context Manager: 'Python 3.13 new features'")

    with Googer() as g:
        results = g.search("Python 3.13 new features", max_results=3)

    print(f"{len(results)} results\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r.get('title', 'N/A')}")
        print(f"    URL:  {r.get('href', 'N/A')}")
        print(f"    Body: {r.get('body', 'N/A')[:120]}")
        print()


def main() -> None:
    """Run all execution tests."""
    print("=" * 70)
    print("  Googer Execution Test (Live Google Search)")
    print("=" * 70)

    tests = [
        ("Basic Web Search", test_basic_search),
        ("Query Builder Search", test_query_builder_search),
        ("News Search", test_news_search),
        ("Context Manager", test_context_manager),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            print(f"  >>> PASS: {name}")
            passed += 1
        except Exception as e:
            print(f"  >>> FAIL: {name}")
            print(f"      Error: {type(e).__name__}: {e}")
            failed += 1

    divider("Test Summary")
    print(f"  PASS: {passed}")
    print(f"  FAIL: {failed}")
    print(f"  TOTAL: {passed + failed}")
    print()


if __name__ == "__main__":
    main()
