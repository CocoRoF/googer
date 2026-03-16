"""Googer 실행 테스트 — 실제 Google 검색을 수행하고 결과를 확인한다.

pytest가 아닌, 직접 실행하여 결과를 눈으로 확인하는 용도.
사용법:
    python execution_test.py
"""

from googer import Googer, Query


def divider(title: str) -> None:
    """구분선 출력."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def test_basic_search() -> None:
    """기본 웹 검색 테스트."""
    divider("1. 기본 웹 검색: '2025 한국 시리즈 우승팀은?'")

    g = Googer()
    results = g.search("2025 한국 시리즈 우승팀은?", region="kr-ko", max_results=5)

    print(f"총 {len(results)}개 결과\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r.get('title', 'N/A')}")
        print(f"    URL:  {r.get('href', 'N/A')}")
        print(f"    내용: {r.get('body', 'N/A')[:120]}")
        print()


def test_query_builder_search() -> None:
    """Query 빌더를 사용한 고급 검색."""
    divider("2. Query 빌더: '한국시리즈' + exact('2025') + site:naver.com")

    q = Query("한국시리즈").exact("2025").site("naver.com")
    print(f"빌드된 쿼리: {q}\n")

    g = Googer()
    results = g.search(q, region="kr-ko", max_results=5)

    print(f"총 {len(results)}개 결과\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r.get('title', 'N/A')}")
        print(f"    URL:  {r.get('href', 'N/A')}")
        print(f"    내용: {r.get('body', 'N/A')[:120]}")
        print()


def test_news_search() -> None:
    """뉴스 검색 테스트."""
    divider("3. 뉴스 검색: '한국시리즈 2025'")

    g = Googer()
    results = g.news("한국시리즈 2025", region="kr-ko", max_results=5)

    print(f"총 {len(results)}개 결과\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r.get('title', 'N/A')}")
        print(f"    URL:  {r.get('href', r.get('url', 'N/A'))}")
        print(f"    출처: {r.get('source', 'N/A')}")
        print(f"    날짜: {r.get('date', 'N/A')}")
        print(f"    내용: {r.get('body', 'N/A')[:120]}")
        print()


def test_context_manager() -> None:
    """Context Manager 사용 테스트."""
    divider("4. Context Manager: 'Python 3.13 new features'")

    with Googer() as g:
        results = g.search("Python 3.13 new features", max_results=3)

    print(f"총 {len(results)}개 결과\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r.get('title', 'N/A')}")
        print(f"    URL:  {r.get('href', 'N/A')}")
        print(f"    내용: {r.get('body', 'N/A')[:120]}")
        print()


def main() -> None:
    """전체 실행 테스트."""
    print("=" * 70)
    print("  Googer 실행 테스트 (실제 Google 검색)")
    print("=" * 70)

    tests = [
        ("기본 웹 검색", test_basic_search),
        ("Query 빌더 검색", test_query_builder_search),
        ("뉴스 검색", test_news_search),
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

    divider("실행 결과 요약")
    print(f"  PASS: {passed}")
    print(f"  FAIL: {failed}")
    print(f"  TOTAL: {passed + failed}")
    print()


if __name__ == "__main__":
    main()
