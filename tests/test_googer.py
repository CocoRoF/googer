"""Tests for the Googer library — unit tests (no network)."""

import pytest

from googer import Googer, Query
from googer.config import SAFESEARCH_MAP, TIMELIMIT_MAP, VERSION
from googer.exceptions import GoogerException
from googer.ranker import Ranker
from googer.results import ResultsAggregator, TextResult
from googer.utils import (
    build_region_params,
    expand_proxy_alias,
    extract_clean_url,
    normalize_text,
    normalize_url,
)


# ---------------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------------


class TestNormalizeUrl:
    """URL normalization."""

    def test_empty(self) -> None:
        assert normalize_url("") == ""

    def test_unquote(self) -> None:
        assert normalize_url("https://example.com/hello%20world") == "https://example.com/hello+world"

    def test_passthrough(self) -> None:
        url = "https://example.com/path"
        assert normalize_url(url) == url


class TestNormalizeText:
    """Text normalization."""

    def test_empty(self) -> None:
        assert normalize_text("") == ""

    def test_strip_html(self) -> None:
        assert normalize_text("<b>bold</b> text") == "bold text"

    def test_unescape(self) -> None:
        assert normalize_text("&amp; &lt;") == "& <"

    def test_collapse_whitespace(self) -> None:
        assert normalize_text("  hello   world  ") == "hello world"


class TestExtractCleanUrl:
    """Google redirect URL cleaning."""

    def test_google_redirect(self) -> None:
        url = "/url?q=https://example.com&sa=U"
        assert extract_clean_url(url) == "https://example.com"

    def test_passthrough(self) -> None:
        url = "https://example.com"
        assert extract_clean_url(url) == url


class TestBuildRegionParams:
    """Region parameter building."""

    def test_us_en(self) -> None:
        params = build_region_params("us-en")
        assert params["hl"] == "en-US"
        assert params["lr"] == "lang_en"
        assert params["cr"] == "countryUS"

    def test_ko_kr(self) -> None:
        params = build_region_params("kr-ko")
        assert params["hl"] == "ko-KR"
        assert params["lr"] == "lang_ko"
        assert params["cr"] == "countryKR"

    def test_invalid_format(self) -> None:
        params = build_region_params("invalid")
        assert params["hl"] == "en-US"


class TestExpandProxy:
    """Proxy alias expansion."""

    def test_tb_alias(self) -> None:
        assert expand_proxy_alias("tb") == "socks5h://127.0.0.1:9150"

    def test_none(self) -> None:
        assert expand_proxy_alias(None) is None

    def test_passthrough(self) -> None:
        assert expand_proxy_alias("http://proxy:8080") == "http://proxy:8080"


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


class TestTextResult:
    """TextResult dataclass."""

    def test_default_values(self) -> None:
        r = TextResult()
        assert r.title == ""
        assert r.href == ""
        assert r.body == ""

    def test_normalization(self) -> None:
        r = TextResult()
        r.title = "<b>Hello</b>"
        assert r.title == "Hello"

    def test_to_dict(self) -> None:
        r = TextResult(title="Test", href="https://example.com", body="Body")
        d = r.to_dict()
        assert d["title"] == "Test"
        assert d["href"] == "https://example.com"

    def test_getitem(self) -> None:
        r = TextResult(title="Test", href="https://example.com", body="Body")
        assert r["title"] == "Test"
        assert r["href"] == "https://example.com"

    def test_get_with_default(self) -> None:
        r = TextResult(title="Test")
        assert r.get("title") == "Test"
        assert r.get("nonexistent", "default") == "default"

    def test_contains(self) -> None:
        r = TextResult(title="Test")
        assert "title" in r
        assert "nonexistent" not in r

    def test_keys_values_items(self) -> None:
        r = TextResult(title="Test", href="https://example.com", body="Body")
        assert "title" in r.keys()
        assert "href" in r.keys()
        assert "Test" in r.values()
        items = dict(r.items())
        assert items["title"] == "Test"

    def test_iter_and_dict_conversion(self) -> None:
        r = TextResult(title="Test", href="https://example.com", body="Body")
        d = dict(r)
        assert d["title"] == "Test"
        assert d["href"] == "https://example.com"

    def test_len(self) -> None:
        r = TextResult(title="Test", href="https://example.com", body="Body")
        assert len(r) == 3

    def test_attribute_access(self) -> None:
        r = TextResult(title="Test", href="https://example.com", body="Body")
        assert r.title == "Test"
        assert r.href == "https://example.com"
        assert r.body == "Body"


class TestResultsAggregator:
    """Deduplication aggregator."""

    def test_dedup(self) -> None:
        agg = ResultsAggregator({"href"})
        r1 = TextResult(title="A", href="https://a.com", body="Body A")
        r2 = TextResult(title="A copy", href="https://a.com", body="Longer body A")
        agg.append(r1)
        agg.append(r2)
        assert len(agg) == 1

    def test_frequency_order(self) -> None:
        agg = ResultsAggregator({"href"})
        r1 = TextResult(title="A", href="https://a.com", body="A")
        r2 = TextResult(title="B", href="https://b.com", body="B")
        agg.append(r2)
        agg.append(r1)
        agg.append(r1)  # A appears twice
        dicts = agg.extract_dicts()
        assert dicts[0]["href"] == "https://a.com"

    def test_extract_returns_objects(self) -> None:
        agg = ResultsAggregator({"href"})
        r1 = TextResult(title="A", href="https://a.com", body="A")
        r2 = TextResult(title="B", href="https://b.com", body="B")
        agg.append(r1)
        agg.append(r2)
        results = agg.extract()
        assert isinstance(results[0], TextResult)
        assert results[0].title == "A"

    def test_empty_cache_fields_raises(self) -> None:
        with pytest.raises(ValueError):
            ResultsAggregator(set())


# ---------------------------------------------------------------------------
# Ranker
# ---------------------------------------------------------------------------


class TestRanker:
    """Relevance ranker."""

    def test_wikipedia_boost(self) -> None:
        ranker = Ranker()
        docs = [
            TextResult(title="Regular", href="https://example.com", body="python info"),
            TextResult(title="Python Wiki", href="https://en.wikipedia.org/wiki/Python", body="python"),
        ]
        ranked = ranker.rank(docs, "python")
        assert "wikipedia" in ranked[0].href

    def test_both_match_before_title_only(self) -> None:
        ranker = Ranker()
        docs = [
            TextResult(title="Python", href="https://a.com", body="no match here"),
            TextResult(title="Python tutorial", href="https://b.com", body="learn python"),
        ]
        ranked = ranker.rank(docs, "python")
        assert ranked[0].href == "https://b.com"

    def test_rank_with_dicts_backward_compat(self) -> None:
        ranker = Ranker()
        docs = [
            {"title": "Regular", "href": "https://example.com", "body": "python info"},
            {"title": "Python Wiki", "href": "https://en.wikipedia.org/wiki/Python", "body": "python"},
        ]
        ranked = ranker.rank(docs, "python")
        assert "wikipedia" in ranked[0]["href"]


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class TestConfig:
    """Configuration values."""

    def test_version(self) -> None:
        assert VERSION  # non-empty string

    def test_safesearch_map(self) -> None:
        assert SAFESEARCH_MAP["on"] == "2"
        assert SAFESEARCH_MAP["moderate"] == "1"
        assert SAFESEARCH_MAP["off"] == "0"

    def test_timelimit_map(self) -> None:
        assert "d" in TIMELIMIT_MAP
        assert "w" in TIMELIMIT_MAP
        assert "m" in TIMELIMIT_MAP
        assert "y" in TIMELIMIT_MAP


# ---------------------------------------------------------------------------
# Googer class — construction only (no network)
# ---------------------------------------------------------------------------


class TestGoogerInit:
    """Googer initialization."""

    def test_default_init(self) -> None:
        g = Googer()
        assert g is not None

    def test_context_manager(self) -> None:
        with Googer() as g:
            assert g is not None

    def test_empty_query_raises(self) -> None:
        with pytest.raises(GoogerException):
            Googer().search("")

    def test_query_object(self) -> None:
        q = Query("test")
        assert str(q) == "test"


# ---------------------------------------------------------------------------
# Query integration
# ---------------------------------------------------------------------------


class TestQueryIntegration:
    """Query builder integration with Googer."""

    def test_query_str_conversion(self) -> None:
        q = Query("python").site("github.com").filetype("py")
        assert "python" in str(q)
        assert "site:github.com" in str(q)
        assert "filetype:py" in str(q)
