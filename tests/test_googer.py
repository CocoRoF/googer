"""googer-rust unit tests.

Validates all Python API exposed by the Rust native extension.
"""

import pytest

from googer import (
    Googer,
    GoogerException,
    HttpException,
    ImageResult,
    NewsResult,
    NoResultsException,
    ParseException,
    Query,
    QueryBuildException,
    RateLimitException,
    TextResult,
    TimeoutException,
    VideoResult,
)


# ── Import ──────────────────────────────────────────────────────────────────


class TestImports:
    """Verify all public names are importable."""

    def test_core_module(self):
        from googer import _core

        assert hasattr(_core, "Googer")

    def test_all_names(self):
        assert Googer is not None
        assert Query is not None
        assert TextResult is not None
        assert ImageResult is not None
        assert NewsResult is not None
        assert VideoResult is not None


# ── Googer Instance ────────────────────────────────────────────────────────


class TestGooger:
    """Test Googer class instantiation and configuration."""

    def test_default_creation(self):
        g = Googer()
        assert g is not None

    def test_with_options(self):
        g = Googer(timeout=30, verify=True, max_retries=5)
        assert g is not None

    def test_context_manager(self):
        with Googer() as g:
            assert g is not None

    def test_empty_query_raises(self):
        g = Googer()
        with pytest.raises(GoogerException):
            g.search("")

    def test_whitespace_query_raises(self):
        g = Googer()
        with pytest.raises(GoogerException):
            g.search("   ")


# ── Query Builder ──────────────────────────────────────────────────────────


class TestQueryBuilder:
    """Test the fluent query builder API."""

    def test_basic(self):
        assert Query("python").build() == "python"

    def test_exact(self):
        result = Query("search").exact("exact phrase").build()
        assert '"exact phrase"' in result

    def test_or_term(self):
        result = Query("base").or_term("alpha").or_term("beta").build()
        assert "OR" in result
        assert "alpha" in result
        assert "beta" in result

    def test_exclude(self):
        result = Query("rust").exclude("java").build()
        assert "-java" in result

    def test_site(self):
        result = Query("news").site("bbc.com").build()
        assert "site:bbc.com" in result

    def test_filetype(self):
        result = Query("report").filetype("pdf").build()
        assert "filetype:pdf" in result

    def test_intitle(self):
        assert "intitle:important" in Query("q").intitle("important").build()

    def test_inurl(self):
        assert "inurl:docs" in Query("q").inurl("docs").build()

    def test_intext(self):
        assert "intext:keyword" in Query("q").intext("keyword").build()

    def test_related(self):
        assert "related:example.com" in Query("q").related("example.com").build()

    def test_cache(self):
        assert "cache:example.com/page" in Query("q").cache("example.com/page").build()

    def test_date_range(self):
        result = Query("q").date_range("2025-01-01", "2025-12-31").build()
        assert "after:2025-01-01" in result
        assert "before:2025-12-31" in result

    def test_raw(self):
        result = Query("q").raw("custom:fragment").build()
        assert "custom:fragment" in result

    def test_chaining(self):
        result = (
            Query("ml")
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

    def test_empty_raises(self):
        with pytest.raises(QueryBuildException):
            Query("").build()

    def test_str(self):
        assert str(Query("hello")) == "hello"

    def test_repr(self):
        r = repr(Query("hello"))
        assert "Query" in r and "hello" in r

    def test_bool_truthy(self):
        assert bool(Query("something")) is True

    def test_bool_falsy(self):
        assert bool(Query("")) is False


# ── TextResult ─────────────────────────────────────────────────────────────


class TestTextResult:
    """Test TextResult dict-like interface."""

    @pytest.fixture()
    def result(self):
        return TextResult(title="Title", href="https://example.com", body="Body text")

    def test_getters(self, result):
        assert result.title == "Title"
        assert result.href == "https://example.com"
        assert result.body == "Body text"

    def test_to_dict(self, result):
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["title"] == "Title"
        assert d["href"] == "https://example.com"
        assert d["body"] == "Body text"

    def test_keys(self, result):
        assert result.keys() == ["title", "href", "body"]

    def test_values(self, result):
        assert result.values() == ["Title", "https://example.com", "Body text"]

    def test_items(self, result):
        assert result.items() == [
            ("title", "Title"),
            ("href", "https://example.com"),
            ("body", "Body text"),
        ]

    def test_get_existing(self, result):
        assert result.get("title") == "Title"

    def test_get_missing(self, result):
        assert result.get("missing") is None

    def test_get_default(self, result):
        assert result.get("missing", "fallback") == "fallback"

    def test_getitem(self, result):
        assert result["title"] == "Title"

    def test_getitem_invalid(self, result):
        with pytest.raises(KeyError):
            _ = result["invalid"]

    def test_contains(self, result):
        assert "title" in result
        assert "href" in result
        assert "nonexistent" not in result

    def test_len(self, result):
        assert len(result) == 3

    def test_repr(self, result):
        s = repr(result)
        assert "TextResult" in s
        assert "Title" in s

    def test_default_empty(self):
        r = TextResult()
        assert r.title == ""
        assert r.href == ""
        assert r.body == ""


# ── ImageResult ────────────────────────────────────────────────────────────


class TestImageResult:
    """Test ImageResult."""

    def test_creation(self):
        r = ImageResult(title="Img", image="http://img.png", url="http://page.com")
        assert r.title == "Img"
        assert r.image == "http://img.png"
        assert r.url == "http://page.com"

    def test_len(self):
        assert len(ImageResult()) == 7

    def test_to_dict(self):
        r = ImageResult(title="T", image="I")
        d = r.to_dict()
        assert d["title"] == "T"
        assert d["image"] == "I"


# ── NewsResult ─────────────────────────────────────────────────────────────


class TestNewsResult:
    """Test NewsResult."""

    def test_creation(self):
        r = NewsResult(title="News", url="http://news.com", source="CNN")
        assert r.title == "News"
        assert r.source == "CNN"

    def test_len(self):
        assert len(NewsResult()) == 6

    def test_contains(self):
        r = NewsResult()
        assert "title" in r
        assert "source" in r

    def test_to_dict(self):
        r = NewsResult(title="T", source="S")
        d = r.to_dict()
        assert d["source"] == "S"


# ── VideoResult ────────────────────────────────────────────────────────────


class TestVideoResult:
    """Test VideoResult."""

    def test_creation(self):
        r = VideoResult(title="Vid", url="http://vid.com", duration="5:30")
        assert r.title == "Vid"
        assert r.duration == "5:30"

    def test_len(self):
        assert len(VideoResult()) == 7

    def test_to_dict(self):
        r = VideoResult(title="V", duration="1:00")
        d = r.to_dict()
        assert d["duration"] == "1:00"


# ── Exceptions ─────────────────────────────────────────────────────────────


class TestExceptions:
    """Test the exception hierarchy."""

    def test_base_is_exception(self):
        assert issubclass(GoogerException, Exception)

    @pytest.mark.parametrize(
        "exc_class",
        [
            HttpException,
            TimeoutException,
            RateLimitException,
            ParseException,
            QueryBuildException,
            NoResultsException,
        ],
    )
    def test_subclass_of_base(self, exc_class):
        assert issubclass(exc_class, GoogerException)

    def test_catch_child_as_parent(self):
        with pytest.raises(GoogerException):
            raise NoResultsException("test")

    def test_exception_message(self):
        try:
            raise NoResultsException("no results here")
        except GoogerException as e:
            assert "no results here" in str(e)
