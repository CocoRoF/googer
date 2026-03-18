"""Tests for the Googer library — unit tests (no network)."""

import time

import pytest

from googer import Googer, Query
from googer.cache import SearchCache
from googer.config import (
    BRAVE_SAFESEARCH_MAP,
    BRAVE_TIMELIMIT_MAP,
    DDG_SAFESEARCH_MAP,
    DDG_TIMELIMIT_MAP,
    DEFAULT_CACHE_TTL,
    DEFAULT_ENGINE,
    ENGINE_FALLBACK_ORDER,
    SAFESEARCH_MAP,
    TIMELIMIT_MAP,
    VERSION,
)
from googer.exceptions import GoogerException
from googer.ranker import Ranker
from googer.results import AnswerResult, ResultsAggregator, TextResult
from googer.utils import (
    build_region_params,
    expand_proxy_alias,
    extract_clean_url,
    extract_ddg_url,
    extract_yahoo_redirect_url,
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


class TestExtractDdgUrl:
    """DuckDuckGo redirect URL extraction."""

    def test_uddg_redirect(self) -> None:
        url = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpath&rut=abc123"
        assert extract_ddg_url(url) == "https://example.com/path"

    def test_direct_url(self) -> None:
        url = "https://example.com/direct"
        assert extract_ddg_url(url) == "https://example.com/direct"

    def test_empty(self) -> None:
        assert extract_ddg_url("") == ""

    def test_uddg_with_https(self) -> None:
        url = "https://duckduckgo.com/l/?uddg=https%3A%2F%2Fpython.org&rut=xyz"
        assert extract_ddg_url(url) == "https://python.org"


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
        assert len(r) == 4  # title, href, body, provider

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

    def test_ddg_safesearch_map(self) -> None:
        assert DDG_SAFESEARCH_MAP["on"] == "1"
        assert DDG_SAFESEARCH_MAP["moderate"] == "-1"
        assert DDG_SAFESEARCH_MAP["off"] == "-2"

    def test_ddg_timelimit_map(self) -> None:
        assert "d" in DDG_TIMELIMIT_MAP
        assert "w" in DDG_TIMELIMIT_MAP
        assert "m" in DDG_TIMELIMIT_MAP
        assert "y" in DDG_TIMELIMIT_MAP

    def test_default_engine(self) -> None:
        assert DEFAULT_ENGINE == "auto"

    def test_fallback_order(self) -> None:
        assert ENGINE_FALLBACK_ORDER == (
            "duckduckgo", "brave", "ecosia", "yahoo", "aol", "google", "naver",
        )


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

    def test_engine_auto(self) -> None:
        g = Googer(engine="auto")
        assert g._engine_preference == "auto"

    def test_engine_duckduckgo(self) -> None:
        g = Googer(engine="duckduckgo")
        assert g._engine_preference == "duckduckgo"

    def test_engine_google(self) -> None:
        g = Googer(engine="google")
        assert g._engine_preference == "google"

    def test_default_backend_is_http(self) -> None:
        g = Googer()
        assert g._backend == "http"

    def test_browser_backend_lazy(self) -> None:
        g = Googer(backend="browser")
        assert g._browser_client is None  # Not created until needed

    def test_resolve_providers_auto(self) -> None:
        g = Googer(engine="auto")
        providers = g._resolve_providers()
        assert providers == list(ENGINE_FALLBACK_ORDER)

    def test_resolve_providers_specific(self) -> None:
        g = Googer(engine="duckduckgo")
        providers = g._resolve_providers()
        assert providers == ["duckduckgo"]

    def test_resolve_providers_override(self) -> None:
        g = Googer(engine="auto")
        providers = g._resolve_providers("google")
        assert providers == ["google"]

    def test_unknown_provider_raises(self) -> None:
        g = Googer()
        with pytest.raises(GoogerException, match="Unknown provider"):
            g._get_engine("nonexistent", "text")


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


# ---------------------------------------------------------------------------
# DuckDuckGo engine internals (no network)
# ---------------------------------------------------------------------------


class TestDuckDuckGoEngines:
    """DuckDuckGo engine unit tests."""

    def test_ddg_text_engine_exists(self) -> None:
        from googer.engines import ENGINES

        assert "duckduckgo" in ENGINES
        assert "text" in ENGINES["duckduckgo"]

    def test_ddg_all_types_exist(self) -> None:
        from googer.engines import ENGINES

        for search_type in ("text", "images", "news", "videos"):
            assert search_type in ENGINES["duckduckgo"], f"DDG missing {search_type} engine"

    def test_google_all_types_exist(self) -> None:
        from googer.engines import ENGINES

        for search_type in ("text", "images", "news", "videos"):
            assert search_type in ENGINES["google"], f"Google missing {search_type} engine"

    def test_ddg_text_build_params(self) -> None:
        from googer.engines.duckduckgo import DuckDuckGoTextEngine
        from googer.http_client import HttpClient

        engine = DuckDuckGoTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "us-en", "moderate", None)
        assert params["q"] == "python"
        assert params["kl"] == "wt-wt"  # us-en maps to worldwide
        assert params["kp"] == "-1"  # moderate

    def test_ddg_text_build_params_region(self) -> None:
        from googer.engines.duckduckgo import DuckDuckGoTextEngine
        from googer.http_client import HttpClient

        engine = DuckDuckGoTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "kr-ko", "off", "d")
        assert params["kl"] == "kr-ko"
        assert params["kp"] == "-2"  # off
        assert params["df"] == "d"

    def test_ddg_extract_next_form(self) -> None:
        from googer.engines.duckduckgo import DuckDuckGoTextEngine

        html = """
        <html><body>
        <form action="/html/" method="post">
            <input type="hidden" name="q" value="python">
            <input type="hidden" name="s" value="30">
            <input type="hidden" name="kl" value="wt-wt">
            <input type="submit" value="Next">
        </form>
        </body></html>
        """
        result = DuckDuckGoTextEngine._extract_next_form(html)
        assert result is not None
        assert result["q"] == "python"
        assert result["s"] == "30"

    def test_ddg_extract_next_form_missing(self) -> None:
        from googer.engines.duckduckgo import DuckDuckGoTextEngine

        html = "<html><body>No form here</body></html>"
        assert DuckDuckGoTextEngine._extract_next_form(html) is None

    def test_ddg_text_post_process(self) -> None:
        from googer.engines.duckduckgo import DuckDuckGoTextEngine
        from googer.http_client import HttpClient

        engine = DuckDuckGoTextEngine(http_client=HttpClient(timeout=5))
        results = [
            TextResult(
                title="Python.org",
                href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.python.org%2F&rut=abc",
                body="Official Python site",
            ),
            TextResult(title="", href="", body=""),  # Should be filtered
        ]
        cleaned = engine.post_process(results)
        assert len(cleaned) == 1
        assert cleaned[0].href == "https://www.python.org/"

    def test_ddg_url_extraction(self) -> None:
        from googer.engines.duckduckgo import _extract_ddg_url

        # DDG redirect
        url = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com&rut=token"
        assert _extract_ddg_url(url) == "https://example.com"

        # Direct URL
        assert _extract_ddg_url("https://example.com") == "https://example.com"

        # Empty
        assert _extract_ddg_url("") == ""

    def test_ddg_region_mapping(self) -> None:
        from googer.engines.duckduckgo import _ddg_region

        assert _ddg_region("us-en") == "wt-wt"
        assert _ddg_region("kr-ko") == "kr-ko"
        assert _ddg_region("") == "wt-wt"


# ---------------------------------------------------------------------------
# Brave engine internals (no network)
# ---------------------------------------------------------------------------


class TestBraveEngines:
    """Brave Search engine unit tests."""

    def test_brave_registered(self) -> None:
        from googer.engines import ENGINES

        assert "brave" in ENGINES

    def test_brave_types_exist(self) -> None:
        from googer.engines import ENGINES

        for search_type in ("text", "news", "videos"):
            assert search_type in ENGINES["brave"], f"Brave missing {search_type} engine"

    def test_brave_no_images(self) -> None:
        """Brave images require JS rendering and are not supported."""
        from googer.engines import ENGINES

        assert "images" not in ENGINES["brave"]

    def test_brave_text_build_params(self) -> None:
        from googer.engines.brave import BraveTextEngine
        from googer.http_client import HttpClient

        engine = BraveTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "us-en", "moderate", None)
        assert params["q"] == "python"
        assert params["source"] == "web"
        assert params["country"] == "us"
        assert params["lang"] == "en"
        assert params["safesearch"] == "moderate"

    def test_brave_text_build_params_timelimit(self) -> None:
        from googer.engines.brave import BraveTextEngine
        from googer.http_client import HttpClient

        engine = BraveTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "kr-ko", "off", "d")
        assert params["tf"] == "pd"
        assert params["safesearch"] == "off"
        assert params["country"] == "kr"

    def test_brave_text_build_params_pagination(self) -> None:
        from googer.engines.brave import BraveTextEngine
        from googer.http_client import HttpClient

        engine = BraveTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "us-en", "moderate", None, page=3)
        assert params["offset"] == "2"

    def test_brave_text_build_params_page1_no_offset(self) -> None:
        from googer.engines.brave import BraveTextEngine
        from googer.http_client import HttpClient

        engine = BraveTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "us-en", "moderate", None, page=1)
        assert "offset" not in params

    def test_brave_news_build_params(self) -> None:
        from googer.engines.brave import BraveNewsEngine
        from googer.http_client import HttpClient

        engine = BraveNewsEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "us-en", "on", "w")
        assert params["source"] == "news"
        assert params["safesearch"] == "strict"
        assert params["tf"] == "pw"

    def test_brave_videos_build_params(self) -> None:
        from googer.engines.brave import BraveVideosEngine
        from googer.http_client import HttpClient

        engine = BraveVideosEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python tutorial", "us-en", "off", "m")
        assert params["source"] == "videos"
        assert params["safesearch"] == "off"
        assert params["tf"] == "pm"

    def test_brave_text_post_process(self) -> None:
        from googer.engines.brave import BraveTextEngine
        from googer.http_client import HttpClient

        engine = BraveTextEngine(http_client=HttpClient(timeout=5))
        results = [
            TextResult(title="Good", href="https://example.com", body="Body"),
            TextResult(title="", href="", body=""),  # no title => filtered
            TextResult(title="No URL", href="javascript:void(0)", body="Body"),  # bad URL
        ]
        cleaned = engine.post_process(results)
        assert len(cleaned) == 1
        assert cleaned[0].title == "Good"

    def test_brave_region_helper(self) -> None:
        from googer.engines.brave import _brave_region

        assert _brave_region("us-en") == "us"
        assert _brave_region("kr-ko") == "kr"
        assert _brave_region("") == ""

    def test_brave_lang_helper(self) -> None:
        from googer.engines.brave import _brave_lang

        assert _brave_lang("us-en") == "en"
        assert _brave_lang("kr-ko") == "ko"
        assert _brave_lang("") == "en"
        assert _brave_lang("us") == "us"  # single part falls back


# ---------------------------------------------------------------------------
# Config — Brave constants
# ---------------------------------------------------------------------------


class TestBraveConfig:
    """Brave Search configuration constants."""

    def test_brave_safesearch_map(self) -> None:
        assert BRAVE_SAFESEARCH_MAP["on"] == "strict"
        assert BRAVE_SAFESEARCH_MAP["moderate"] == "moderate"
        assert BRAVE_SAFESEARCH_MAP["off"] == "off"

    def test_brave_timelimit_map(self) -> None:
        assert BRAVE_TIMELIMIT_MAP["d"] == "pd"
        assert BRAVE_TIMELIMIT_MAP["w"] == "pw"
        assert BRAVE_TIMELIMIT_MAP["m"] == "pm"
        assert BRAVE_TIMELIMIT_MAP["y"] == "py"

    def test_cache_defaults(self) -> None:
        assert DEFAULT_CACHE_TTL == 300


# ---------------------------------------------------------------------------
# SearchCache
# ---------------------------------------------------------------------------


class TestSearchCache:
    """TTL-based in-memory cache."""

    def test_set_and_get(self) -> None:
        cache = SearchCache(ttl=60)
        cache.set("key1", [1, 2, 3])
        assert cache.get("key1") == [1, 2, 3]

    def test_get_missing(self) -> None:
        cache = SearchCache(ttl=60)
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self) -> None:
        cache = SearchCache(ttl=1)
        cache.set("key1", "value")
        assert cache.get("key1") == "value"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_clear(self) -> None:
        cache = SearchCache(ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        assert cache.size == 2
        cache.clear()
        assert cache.size == 0

    def test_make_key_deterministic(self) -> None:
        k1 = SearchCache.make_key(query="python", region="us-en")
        k2 = SearchCache.make_key(query="python", region="us-en")
        assert k1 == k2

    def test_make_key_different_params(self) -> None:
        k1 = SearchCache.make_key(query="python", region="us-en")
        k2 = SearchCache.make_key(query="python", region="kr-ko")
        assert k1 != k2

    def test_make_key_ignores_none(self) -> None:
        k1 = SearchCache.make_key(query="python", timelimit=None)
        k2 = SearchCache.make_key(query="python")
        assert k1 == k2

    def test_max_size_eviction(self) -> None:
        cache = SearchCache(ttl=60, max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # should evict oldest
        assert cache.size <= 3

    def test_size_property(self) -> None:
        cache = SearchCache(ttl=60)
        assert cache.size == 0
        cache.set("k", "v")
        assert cache.size == 1


# ---------------------------------------------------------------------------
# AnswerResult
# ---------------------------------------------------------------------------


class TestAnswerResult:
    """AnswerResult dataclass."""

    def test_default_values(self) -> None:
        r = AnswerResult()
        assert r.heading == ""
        assert r.abstract == ""
        assert r.url == ""
        assert r.source == ""
        assert r.answer == ""
        assert r.answer_type == ""
        assert r.image == ""
        assert r.related is None

    def test_with_values(self) -> None:
        r = AnswerResult(
            heading="Python",
            abstract="A programming language.",
            url="https://en.wikipedia.org/wiki/Python",
            source="Wikipedia",
            answer="",
            answer_type="A",
            image="https://example.com/img.png",
            related=[{"text": "Java", "url": "https://example.com/java"}],
        )
        assert r.heading == "Python"
        assert r.abstract == "A programming language."
        assert r.source == "Wikipedia"
        assert r.related is not None
        assert len(r.related) == 1
        assert r.related[0]["text"] == "Java"

    def test_to_dict(self) -> None:
        r = AnswerResult(heading="Test", abstract="Body text.")
        d = r.to_dict()
        assert d["heading"] == "Test"
        assert d["abstract"] == "Body text."

    def test_normalisation_for_strings(self) -> None:
        """AnswerResult normalises string fields but leaves list fields alone."""
        r = AnswerResult()
        r.source = "<b>Wikipedia</b>"
        assert r.source == "Wikipedia"  # HTML stripped (source normaliser)
        r.related = [{"text": "test"}]
        assert r.related == [{"text": "test"}]  # list untouched


# ---------------------------------------------------------------------------
# Provider field on results
# ---------------------------------------------------------------------------


class TestProviderField:
    """All result types should have a provider field."""

    def test_text_result_provider(self) -> None:
        r = TextResult(title="Test", provider="duckduckgo")
        assert r.provider == "duckduckgo"

    def test_text_result_provider_default(self) -> None:
        r = TextResult(title="Test")
        assert r.provider == ""

    def test_text_result_provider_in_dict(self) -> None:
        r = TextResult(title="Test", provider="brave")
        d = r.to_dict()
        assert d["provider"] == "brave"

    def test_provider_on_all_types(self) -> None:
        from googer.results import ImageResult, NewsResult, VideoResult

        for cls in (TextResult, ImageResult, NewsResult, VideoResult):
            r = cls(provider="test_provider")  # type: ignore[call-arg]
            assert r.provider == "test_provider"


# ---------------------------------------------------------------------------
# Googer — multi-engine & cache (no network)
# ---------------------------------------------------------------------------


class TestGoogerMultiEngine:
    """Multi-engine related tests (no network)."""

    def test_resolve_providers_multi(self) -> None:
        g = Googer(engine="multi")
        providers = g._resolve_providers()
        assert providers == ["multi"]

    def test_resolve_providers_brave(self) -> None:
        g = Googer(engine="brave")
        providers = g._resolve_providers()
        assert providers == ["brave"]

    def test_resolve_providers_auto_includes_brave(self) -> None:
        g = Googer(engine="auto")
        providers = g._resolve_providers()
        assert "brave" in providers

    def test_engine_preference_brave(self) -> None:
        g = Googer(engine="brave")
        assert g._engine_preference == "brave"

    def test_engine_preference_multi(self) -> None:
        g = Googer(engine="multi")
        assert g._engine_preference == "multi"

    def test_get_engine_brave_text(self) -> None:
        from googer.engines.brave import BraveTextEngine

        g = Googer()
        engine = g._get_engine("brave", "text")
        assert isinstance(engine, BraveTextEngine)

    def test_get_engine_brave_news(self) -> None:
        from googer.engines.brave import BraveNewsEngine

        g = Googer()
        engine = g._get_engine("brave", "news")
        assert isinstance(engine, BraveNewsEngine)

    def test_get_engine_brave_videos(self) -> None:
        from googer.engines.brave import BraveVideosEngine

        g = Googer()
        engine = g._get_engine("brave", "videos")
        assert isinstance(engine, BraveVideosEngine)

    def test_get_engine_brave_images_raises(self) -> None:
        g = Googer()
        with pytest.raises(GoogerException, match="no 'images' engine"):
            g._get_engine("brave", "images")


class TestGoogerCache:
    """Cache integration in Googer class (no network)."""

    def test_cache_enabled_by_default(self) -> None:
        g = Googer()
        assert g._cache is not None

    def test_cache_disabled_with_zero_ttl(self) -> None:
        g = Googer(cache_ttl=0)
        assert g._cache is None

    def test_clear_cache(self) -> None:
        g = Googer()
        assert g._cache is not None
        g._cache.set("testkey", "testvalue")
        assert g._cache.size == 1
        g.clear_cache()
        assert g._cache.size == 0

    def test_clear_cache_when_disabled(self) -> None:
        """clear_cache() should not raise when cache is disabled."""
        g = Googer(cache_ttl=0)
        g.clear_cache()  # should not raise


# ---------------------------------------------------------------------------
# Yahoo redirect URL extraction
# ---------------------------------------------------------------------------


class TestExtractYahooRedirectUrl:
    """Yahoo/AOL redirect URL extraction."""

    def test_yahoo_redirect(self) -> None:
        url = (
            "https://r.search.yahoo.com/_ylt=xxx;_ylu=yyy"
            "/RV=2/RE=1775029680/RO=10"
            "/RU=https%3a%2f%2fwww.python.org%2f/RK=2/RS=abc123-"
        )
        assert extract_yahoo_redirect_url(url) == "https://www.python.org/"

    def test_yahoo_redirect_encoded(self) -> None:
        url = (
            "https://r.search.yahoo.com/_ylt=x;_ylu=y"
            "/RV=2/RE=1775029680/RO=10"
            "/RU=https%3a%2f%2fwww.w3schools.com%2fpython%2f/RK=2/RS=z-"
        )
        assert extract_yahoo_redirect_url(url) == "https://www.w3schools.com/python/"

    def test_direct_url_passthrough(self) -> None:
        url = "https://example.com/path"
        assert extract_yahoo_redirect_url(url) == "https://example.com/path"

    def test_empty(self) -> None:
        assert extract_yahoo_redirect_url("") == ""


# ---------------------------------------------------------------------------
# Ecosia engine internals (no network)
# ---------------------------------------------------------------------------


class TestEcosiaEngine:
    """Ecosia search engine unit tests."""

    def test_ecosia_registered(self) -> None:
        from googer.engines import ENGINES

        assert "ecosia" in ENGINES
        assert "text" in ENGINES["ecosia"]

    def test_ecosia_text_build_params(self) -> None:
        from googer.engines.ecosia import EcosiaTextEngine
        from googer.http_client import HttpClient

        engine = EcosiaTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "us-en", "moderate", None)
        assert params["q"] == "python"
        assert params["language"] == "en"

    def test_ecosia_text_build_params_page(self) -> None:
        from googer.engines.ecosia import EcosiaTextEngine
        from googer.http_client import HttpClient

        engine = EcosiaTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "us-en", "moderate", None, page=3)
        assert params["p"] == "2"

    def test_ecosia_text_build_params_page1_no_p(self) -> None:
        from googer.engines.ecosia import EcosiaTextEngine
        from googer.http_client import HttpClient

        engine = EcosiaTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "us-en", "moderate", None, page=1)
        assert "p" not in params

    def test_ecosia_text_post_process(self) -> None:
        from googer.engines.ecosia import EcosiaTextEngine
        from googer.http_client import HttpClient

        engine = EcosiaTextEngine(http_client=HttpClient(timeout=5))
        results = [
            TextResult(title="Good", href="https://example.com", body="Body"),
            TextResult(title="", href="", body=""),   # no title
            TextResult(title="Bad", href="javascript:void(0)", body=""),  # bad href
        ]
        cleaned = engine.post_process(results)
        assert len(cleaned) == 1
        assert cleaned[0].title == "Good"

    def test_ecosia_lang_helper(self) -> None:
        from googer.engines.ecosia import _ecosia_lang

        assert _ecosia_lang("us-en") == "en"
        assert _ecosia_lang("kr-ko") == "ko"
        assert _ecosia_lang("") == "en"


# ---------------------------------------------------------------------------
# Yahoo engine internals (no network)
# ---------------------------------------------------------------------------


class TestYahooEngine:
    """Yahoo search engine unit tests."""

    def test_yahoo_registered(self) -> None:
        from googer.engines import ENGINES

        assert "yahoo" in ENGINES
        assert "text" in ENGINES["yahoo"]

    def test_yahoo_text_build_params(self) -> None:
        from googer.engines.yahoo import YahooTextEngine
        from googer.http_client import HttpClient

        engine = YahooTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "us-en", "moderate", None)
        assert params["p"] == "python"
        assert params["ei"] == "UTF-8"

    def test_yahoo_text_build_params_page(self) -> None:
        from googer.engines.yahoo import YahooTextEngine
        from googer.http_client import HttpClient

        engine = YahooTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "us-en", "moderate", None, page=3)
        assert params["b"] == "21"

    def test_yahoo_text_build_params_page1_no_b(self) -> None:
        from googer.engines.yahoo import YahooTextEngine
        from googer.http_client import HttpClient

        engine = YahooTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "us-en", "moderate", None, page=1)
        assert "b" not in params

    def test_yahoo_text_post_process(self) -> None:
        from googer.engines.yahoo import YahooTextEngine
        from googer.http_client import HttpClient

        engine = YahooTextEngine(http_client=HttpClient(timeout=5))
        results = [
            TextResult(
                title="Python.org",
                href=(
                    "https://r.search.yahoo.com/_ylt=x;_ylu=y"
                    "/RV=2/RE=123/RO=10"
                    "/RU=https%3a%2f%2fwww.python.org%2f/RK=2/RS=abc-"
                ),
                body="Official site",
            ),
            TextResult(title="", href="", body=""),  # filtered
        ]
        cleaned = engine.post_process(results)
        assert len(cleaned) == 1
        assert cleaned[0].href == "https://www.python.org/"


# ---------------------------------------------------------------------------
# AOL engine internals (no network)
# ---------------------------------------------------------------------------


class TestAolEngine:
    """AOL search engine unit tests."""

    def test_aol_registered(self) -> None:
        from googer.engines import ENGINES

        assert "aol" in ENGINES
        assert "text" in ENGINES["aol"]

    def test_aol_text_build_params(self) -> None:
        from googer.engines.aol import AolTextEngine
        from googer.http_client import HttpClient

        engine = AolTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "us-en", "moderate", None)
        assert params["q"] == "python"
        assert params["s_it"] == "aol-serp"

    def test_aol_text_build_params_page(self) -> None:
        from googer.engines.aol import AolTextEngine
        from googer.http_client import HttpClient

        engine = AolTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "us-en", "moderate", None, page=2)
        assert params["b"] == "11"

    def test_aol_text_post_process(self) -> None:
        from googer.engines.aol import AolTextEngine
        from googer.http_client import HttpClient

        engine = AolTextEngine(http_client=HttpClient(timeout=5))
        results = [
            TextResult(
                title="W3Schools",
                href=(
                    "https://r.search.yahoo.com/_ylt=x;_ylu=y"
                    "/RV=2/RE=123/RO=10"
                    "/RU=https%3a%2f%2fwww.w3schools.com%2fpython%2f/RK=2/RS=z-"
                ),
                body="Tutorials",
            ),
            TextResult(title="No URL", href="javascript:void(0)", body="X"),
        ]
        cleaned = engine.post_process(results)
        assert len(cleaned) == 1
        assert cleaned[0].href == "https://www.w3schools.com/python/"


# ---------------------------------------------------------------------------
# Naver engine internals (no network)
# ---------------------------------------------------------------------------


class TestNaverEngine:
    """Naver search engine unit tests."""

    def test_naver_registered(self) -> None:
        from googer.engines import ENGINES

        assert "naver" in ENGINES
        assert "text" in ENGINES["naver"]

    def test_naver_text_build_params(self) -> None:
        from googer.engines.naver import NaverTextEngine
        from googer.http_client import HttpClient

        engine = NaverTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python programming", "ko-kr", "moderate", None)
        assert params["query"] == "python programming"
        assert params["where"] == "web"

    def test_naver_text_build_params_page(self) -> None:
        from googer.engines.naver import NaverTextEngine
        from googer.http_client import HttpClient

        engine = NaverTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "ko-kr", "moderate", None, page=3)
        assert params["start"] == "21"

    def test_naver_text_build_params_page1_no_start(self) -> None:
        from googer.engines.naver import NaverTextEngine
        from googer.http_client import HttpClient

        engine = NaverTextEngine(http_client=HttpClient(timeout=5))
        params = engine.build_params("python", "ko-kr", "moderate", None, page=1)
        assert "start" not in params

    def test_naver_parse_html(self) -> None:
        from googer.engines.naver import NaverTextEngine

        html = """
        <html><body>
        <div class="fds-web-doc-root">
            <a href="https://example.com">Examplewww.example.com</a>
            <a href="#">Keep에 저장</a>
            <a href="https://keep.naver.com/">Keep에 바로가기</a>
            <a href="https://example.com">Example Title</a>
            <a href="https://example.com">This is the description of the page.</a>
        </div>
        <div class="fds-web-doc-root">
            <a href="https://python.org">Pythonwww.python.org</a>
            <a href="#">Keep에 저장</a>
            <a href="https://keep.naver.com/">Keep</a>
            <a href="https://python.org">Welcome to Python</a>
        </div>
        </body></html>
        """
        results = NaverTextEngine._parse_naver(html)
        assert len(results) == 2
        assert results[0].title == "Example Title"
        assert results[0].href == "https://example.com"
        assert results[0].body == "This is the description of the page."
        assert results[1].title == "Welcome to Python"
        assert results[1].href == "https://python.org"

    def test_naver_parse_empty_html(self) -> None:
        from googer.engines.naver import NaverTextEngine

        results = NaverTextEngine._parse_naver("<html><body></body></html>")
        assert results == []

    def test_naver_parse_no_external_links(self) -> None:
        from googer.engines.naver import NaverTextEngine

        html = """
        <html><body>
        <div class="fds-web-doc-root">
            <a href="#">Bookmark</a>
            <a href="https://keep.naver.com/">Keep</a>
        </div>
        </body></html>
        """
        results = NaverTextEngine._parse_naver(html)
        assert results == []


# ---------------------------------------------------------------------------
# Googer — new engine integration (no network)
# ---------------------------------------------------------------------------


class TestGoogerNewEngines:
    """New engine integration tests (no network)."""

    def test_get_engine_ecosia(self) -> None:
        from googer.engines.ecosia import EcosiaTextEngine

        g = Googer()
        engine = g._get_engine("ecosia", "text")
        assert isinstance(engine, EcosiaTextEngine)

    def test_get_engine_yahoo(self) -> None:
        from googer.engines.yahoo import YahooTextEngine

        g = Googer()
        engine = g._get_engine("yahoo", "text")
        assert isinstance(engine, YahooTextEngine)

    def test_get_engine_aol(self) -> None:
        from googer.engines.aol import AolTextEngine

        g = Googer()
        engine = g._get_engine("aol", "text")
        assert isinstance(engine, AolTextEngine)

    def test_get_engine_naver(self) -> None:
        from googer.engines.naver import NaverTextEngine

        g = Googer()
        engine = g._get_engine("naver", "text")
        assert isinstance(engine, NaverTextEngine)

    def test_resolve_providers_ecosia(self) -> None:
        g = Googer(engine="ecosia")
        assert g._resolve_providers() == ["ecosia"]

    def test_resolve_providers_yahoo(self) -> None:
        g = Googer(engine="yahoo")
        assert g._resolve_providers() == ["yahoo"]

    def test_resolve_providers_aol(self) -> None:
        g = Googer(engine="aol")
        assert g._resolve_providers() == ["aol"]

    def test_resolve_providers_naver(self) -> None:
        g = Googer(engine="naver")
        assert g._resolve_providers() == ["naver"]

    def test_auto_fallback_includes_new_engines(self) -> None:
        g = Googer(engine="auto")
        providers = g._resolve_providers()
        for provider in ("ecosia", "yahoo", "aol", "naver"):
            assert provider in providers

    def test_ecosia_no_images(self) -> None:
        g = Googer()
        with pytest.raises(GoogerException, match="no 'images' engine"):
            g._get_engine("ecosia", "images")

    def test_naver_no_videos(self) -> None:
        g = Googer()
        with pytest.raises(GoogerException, match="no 'videos' engine"):
            g._get_engine("naver", "videos")

    def test_custom_ttl(self) -> None:
        g = Googer(cache_ttl=120)
        assert g._cache is not None
        assert g._cache._ttl == 120
