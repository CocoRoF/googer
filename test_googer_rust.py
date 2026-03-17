"""googer-rust 통합 테스트

Rust 기반 googer 패키지의 모든 Python API를 검증합니다.
"""

import sys
import traceback

PASSED = 0
FAILED = 0


def run(name, fn):
    global PASSED, FAILED
    try:
        fn()
        PASSED += 1
        print(f"  ✅ {name}")
    except Exception as e:
        FAILED += 1
        print(f"  ❌ {name}")
        traceback.print_exc()
        print()


# ──────────────────────────────────────────────
# 1. Import 테스트
# ──────────────────────────────────────────────
print("\n[1] Import 테스트")


def test_import_core():
    from googer import _core
    assert hasattr(_core, "Googer")

run("_core 모듈 import", test_import_core)


def test_import_all_public_names():
    from googer import (
        Googer, Query,
        TextResult, ImageResult, NewsResult, VideoResult,
        GoogerException, HttpException, TimeoutException,
        RateLimitException, ParseException, QueryBuildException,
        NoResultsException,
    )
    assert Googer is not None

run("모든 public 이름 import", test_import_all_public_names)


# ──────────────────────────────────────────────
# 2. Googer 인스턴스 테스트
# ──────────────────────────────────────────────
print("\n[2] Googer 인스턴스 테스트")


def test_googer_default():
    from googer import Googer
    g = Googer()
    assert g is not None

run("기본 생성", test_googer_default)


def test_googer_with_options():
    from googer import Googer
    g = Googer(timeout=30, verify=True, max_retries=5)
    assert g is not None

run("옵션 지정 생성", test_googer_with_options)


def test_googer_context_manager():
    from googer import Googer
    with Googer() as g:
        assert g is not None

run("context manager (with문)", test_googer_context_manager)


def test_googer_empty_query():
    from googer import Googer, GoogerException
    g = Googer()
    try:
        g.search("")
        assert False, "빈 쿼리에서 예외가 발생해야 함"
    except GoogerException:
        pass  # 정상

run("빈 쿼리 예외 처리", test_googer_empty_query)


# ──────────────────────────────────────────────
# 3. Query Builder 테스트
# ──────────────────────────────────────────────
print("\n[3] Query Builder 테스트")


def test_query_basic():
    from googer import Query
    q = Query("python")
    result = q.build()
    assert result == "python", f"expected 'python', got {result!r}"

run("기본 쿼리", test_query_basic)


def test_query_exact():
    from googer import Query
    q = Query("search").exact("exact phrase")
    result = q.build()
    assert '"exact phrase"' in result

run("exact() 큰따옴표 감싸기", test_query_exact)


def test_query_or_term():
    from googer import Query
    q = Query("base").or_term("alpha").or_term("beta")
    result = q.build()
    assert "OR" in result
    assert "alpha" in result
    assert "beta" in result

run("or_term() OR 연산", test_query_or_term)


def test_query_exclude():
    from googer import Query
    q = Query("rust").exclude("java")
    result = q.build()
    assert "-java" in result

run("exclude() 제외 연산", test_query_exclude)


def test_query_site():
    from googer import Query
    q = Query("news").site("bbc.com")
    result = q.build()
    assert "site:bbc.com" in result

run("site() 도메인 제한", test_query_site)


def test_query_filetype():
    from googer import Query
    q = Query("report").filetype("pdf")
    result = q.build()
    assert "filetype:pdf" in result

run("filetype() 파일 유형", test_query_filetype)


def test_query_intitle():
    from googer import Query
    result = Query("test").intitle("important").build()
    assert "intitle:important" in result

run("intitle()", test_query_intitle)


def test_query_inurl():
    from googer import Query
    result = Query("test").inurl("docs").build()
    assert "inurl:docs" in result

run("inurl()", test_query_inurl)


def test_query_intext():
    from googer import Query
    result = Query("test").intext("keyword").build()
    assert "intext:keyword" in result

run("intext()", test_query_intext)


def test_query_related():
    from googer import Query
    result = Query("test").related("example.com").build()
    assert "related:example.com" in result

run("related()", test_query_related)


def test_query_cache():
    from googer import Query
    result = Query("test").cache("example.com/page").build()
    assert "cache:example.com/page" in result

run("cache()", test_query_cache)


def test_query_date_range():
    from googer import Query
    result = Query("test").date_range("2025-01-01", "2025-12-31").build()
    assert "after:2025-01-01" in result
    assert "before:2025-12-31" in result

run("date_range() 날짜 범위", test_query_date_range)


def test_query_raw():
    from googer import Query
    result = Query("test").raw("custom:fragment").build()
    assert "custom:fragment" in result

run("raw() 임의 조각", test_query_raw)


def test_query_chaining():
    from googer import Query
    result = (
        Query("machine learning")
        .exact("deep learning")
        .site("arxiv.org")
        .filetype("pdf")
        .exclude("survey")
        .build()
    )
    assert '"deep learning"' in result
    assert "site:arxiv.org" in result
    assert "filetype:pdf" in result
    assert "-survey" in result

run("메서드 체이닝 복합 쿼리", test_query_chaining)


def test_query_empty_error():
    from googer import Query, QueryBuildException
    try:
        Query("").build()
        assert False, "빈 쿼리에서 예외가 발생해야 함"
    except QueryBuildException:
        pass

run("빈 Query 예외", test_query_empty_error)


def test_query_str():
    from googer import Query
    q = Query("hello")
    assert str(q) == "hello"

run("__str__() 변환", test_query_str)


def test_query_repr():
    from googer import Query
    q = Query("hello")
    r = repr(q)
    assert "Query" in r and "hello" in r

run("__repr__() 표현", test_query_repr)


def test_query_bool():
    from googer import Query
    assert bool(Query("something")) is True
    assert bool(Query("")) is False

run("__bool__() 진위값", test_query_bool)


# ──────────────────────────────────────────────
# 4. TextResult 테스트
# ──────────────────────────────────────────────
print("\n[4] TextResult 테스트")


def test_text_result_creation():
    from googer import TextResult
    r = TextResult(title="Title", href="https://example.com", body="Body text")
    assert r.title == "Title"
    assert r.href == "https://example.com"
    assert r.body == "Body text"

run("생성 및 getter", test_text_result_creation)


def test_text_result_to_dict():
    from googer import TextResult
    r = TextResult(title="T", href="H", body="B")
    d = r.to_dict()
    assert isinstance(d, dict)
    assert d["title"] == "T"
    assert d["href"] == "H"
    assert d["body"] == "B"

run("to_dict()", test_text_result_to_dict)


def test_text_result_keys_values_items():
    from googer import TextResult
    r = TextResult(title="A", href="B", body="C")
    assert r.keys() == ["title", "href", "body"]
    assert r.values() == ["A", "B", "C"]
    assert r.items() == [("title", "A"), ("href", "B"), ("body", "C")]

run("keys/values/items", test_text_result_keys_values_items)


def test_text_result_get():
    from googer import TextResult
    r = TextResult(title="T", href="H", body="B")
    assert r.get("title") == "T"
    assert r.get("missing") is None
    assert r.get("missing", "default") == "default"

run("get() 메서드", test_text_result_get)


def test_text_result_getitem():
    from googer import TextResult
    r = TextResult(title="T", href="H", body="B")
    assert r["title"] == "T"
    try:
        _ = r["invalid"]
        assert False
    except KeyError:
        pass

run("__getitem__[] 접근", test_text_result_getitem)


def test_text_result_contains():
    from googer import TextResult
    r = TextResult()
    assert "title" in r
    assert "href" in r
    assert "nonexistent" not in r

run("__contains__ (in 연산자)", test_text_result_contains)


def test_text_result_len():
    from googer import TextResult
    assert len(TextResult()) == 3

run("__len__", test_text_result_len)


def test_text_result_repr():
    from googer import TextResult
    r = TextResult(title="Title", href="URL", body="Body")
    s = repr(r)
    assert "TextResult" in s and "Title" in s

run("__repr__", test_text_result_repr)


# ──────────────────────────────────────────────
# 5. ImageResult 테스트
# ──────────────────────────────────────────────
print("\n[5] ImageResult 테스트")


def test_image_result():
    from googer import ImageResult
    r = ImageResult(title="Img", image="http://img.png", url="http://page.com")
    assert r.title == "Img"
    assert r.image == "http://img.png"
    assert r.url == "http://page.com"
    assert len(r) == 7
    d = r.to_dict()
    assert "title" in d
    assert "image" in d

run("ImageResult 생성·getter·to_dict", test_image_result)


# ──────────────────────────────────────────────
# 6. NewsResult 테스트
# ──────────────────────────────────────────────
print("\n[6] NewsResult 테스트")


def test_news_result():
    from googer import NewsResult
    r = NewsResult(title="News", url="http://news.com", body="content",
                   source="CNN", date="2025-01-01", image="http://img.jpg")
    assert r.title == "News"
    assert r.source == "CNN"
    assert len(r) == 6
    assert "title" in r
    d = r.to_dict()
    assert d["source"] == "CNN"

run("NewsResult 생성·getter·to_dict", test_news_result)


# ──────────────────────────────────────────────
# 7. VideoResult 테스트
# ──────────────────────────────────────────────
print("\n[7] VideoResult 테스트")


def test_video_result():
    from googer import VideoResult
    r = VideoResult(title="Video", url="http://vid.com", body="desc",
                    duration="5:30", source="YouTube", date="2025-06-01",
                    thumbnail="http://thumb.jpg")
    assert r.title == "Video"
    assert r.duration == "5:30"
    assert len(r) == 7
    d = r.to_dict()
    assert d["duration"] == "5:30"

run("VideoResult 생성·getter·to_dict", test_video_result)


# ──────────────────────────────────────────────
# 8. Exception 계층 테스트
# ──────────────────────────────────────────────
print("\n[8] Exception 계층 테스트")


def test_exception_hierarchy():
    from googer import (
        GoogerException, HttpException, TimeoutException,
        RateLimitException, ParseException, QueryBuildException,
        NoResultsException,
    )
    for exc in [HttpException, TimeoutException, RateLimitException,
                ParseException, QueryBuildException, NoResultsException]:
        assert issubclass(exc, GoogerException), f"{exc.__name__}은 GoogerException의 하위 클래스여야 함"

run("모든 예외가 GoogerException 하위 클래스", test_exception_hierarchy)


def test_exception_is_base_exception():
    from googer import GoogerException
    assert issubclass(GoogerException, Exception)

run("GoogerException은 Exception 하위 클래스", test_exception_is_base_exception)


def test_exception_catch():
    from googer import GoogerException, NoResultsException
    try:
        raise NoResultsException("테스트")
    except GoogerException as e:
        assert "테스트" in str(e)

run("GoogerException으로 하위 예외 catch", test_exception_catch)


# ──────────────────────────────────────────────
# 9. 라이브 검색 테스트 (네트워크 필요)
# ──────────────────────────────────────────────
print("\n[9] 라이브 검색 테스트 (네트워크)")


def test_live_search():
    from googer import Googer, GoogerException
    g = Googer(timeout=15)
    try:
        results = g.search("python programming", max_results=3)
        assert len(results) > 0, "결과가 1개 이상이어야 함"
        r = results[0]
        assert r.title, "제목이 비어있지 않아야 함"
        assert r.href.startswith("http"), "URL이 http로 시작해야 함"
        print(f"       → {len(results)}개 결과, 첫 번째: {r.title[:50]}")
    except GoogerException as e:
        print(f"       → 네트워크 오류 (SKIP): {e}")

run("text 검색", test_live_search)


def test_live_news():
    from googer import Googer, GoogerException
    g = Googer(timeout=15)
    try:
        results = g.news("technology", max_results=3)
        assert len(results) > 0
        print(f"       → {len(results)}개 뉴스 결과")
    except GoogerException as e:
        print(f"       → 네트워크 오류 (SKIP): {e}")

run("news 검색", test_live_news)


def test_live_images():
    from googer import Googer, GoogerException
    g = Googer(timeout=15)
    try:
        results = g.images("sunset", max_results=3)
        assert len(results) > 0
        print(f"       → {len(results)}개 이미지 결과")
    except GoogerException as e:
        print(f"       → 네트워크 오류 (SKIP): {e}")

run("images 검색", test_live_images)


def test_live_videos():
    from googer import Googer, GoogerException
    g = Googer(timeout=15)
    try:
        results = g.videos("python tutorial", max_results=3)
        assert len(results) > 0
        print(f"       → {len(results)}개 비디오 결과")
    except GoogerException as e:
        print(f"       → 네트워크 오류 (SKIP): {e}")

run("videos 검색", test_live_videos)


# ──────────────────────────────────────────────
# 결과 요약
# ──────────────────────────────────────────────
print("\n" + "=" * 50)
total = PASSED + FAILED
print(f"  총 {total}개 테스트  |  ✅ {PASSED} 통과  |  ❌ {FAILED} 실패")
print("=" * 50)

sys.exit(1 if FAILED else 0)
