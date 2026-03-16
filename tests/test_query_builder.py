"""Tests for the Query builder."""

import pytest

from googer.exceptions import QueryBuildException
from googer.query_builder import Query


class TestQueryBasic:
    """Basic query construction."""

    def test_simple_query(self) -> None:
        q = Query("python programming")
        assert str(q) == "python programming"

    def test_empty_query_raises(self) -> None:
        with pytest.raises(QueryBuildException):
            Query().build()

    def test_bool_false_for_empty(self) -> None:
        assert not Query()

    def test_bool_true_for_non_empty(self) -> None:
        assert Query("test")

    def test_repr(self) -> None:
        q = Query("hello")
        assert repr(q) == "Query('hello')"

    def test_repr_empty(self) -> None:
        q = Query()
        assert repr(q) == "Query('<empty>')"


class TestQueryExactPhrase:
    """Exact phrase matching."""

    def test_single_exact(self) -> None:
        q = Query("python").exact("machine learning")
        assert str(q) == 'python "machine learning"'

    def test_multiple_exact(self) -> None:
        q = Query("AI").exact("deep learning").exact("neural network")
        assert str(q) == 'AI "deep learning" "neural network"'

    def test_empty_exact_ignored(self) -> None:
        q = Query("test").exact("").exact("  ")
        assert str(q) == "test"


class TestQueryOrTerms:
    """OR alternatives."""

    def test_or_terms(self) -> None:
        q = Query("python").or_term("java").or_term("rust")
        assert str(q) == "python (java OR rust)"


class TestQueryExclusions:
    """Term exclusions."""

    def test_exclude(self) -> None:
        q = Query("python").exclude("tutorial").exclude("beginner")
        assert str(q) == "python -tutorial -beginner"


class TestQueryOperators:
    """Google search operators."""

    def test_site(self) -> None:
        q = Query("python").site("github.com")
        assert str(q) == "python site:github.com"

    def test_filetype(self) -> None:
        q = Query("report").filetype("pdf")
        assert str(q) == "python report filetype:pdf" or str(q) == "report filetype:pdf"

    def test_filetype_strips_dot(self) -> None:
        q = Query("report").filetype(".pdf")
        assert "filetype:pdf" in str(q)

    def test_intitle(self) -> None:
        q = Query("python").intitle("tutorial")
        assert str(q) == "python intitle:tutorial"

    def test_inurl(self) -> None:
        q = Query("python").inurl("docs")
        assert str(q) == "python inurl:docs"

    def test_intext(self) -> None:
        q = Query("python").intext("programming")
        assert str(q) == "python intext:programming"

    def test_related(self) -> None:
        q = Query().related("https://python.org")
        assert str(q) == "related:https://python.org"

    def test_cache(self) -> None:
        q = Query().cache("https://python.org")
        assert str(q) == "cache:https://python.org"


class TestQueryDateRange:
    """Date range filtering."""

    def test_date_range(self) -> None:
        q = Query("AI news").date_range("2024-01-01", "2024-12-31")
        assert "after:2024-01-01 before:2024-12-31" in str(q)


class TestQueryRaw:
    """Raw query fragments."""

    def test_raw(self) -> None:
        q = Query("test").raw("define:python")
        assert str(q) == "test define:python"


class TestQueryChaining:
    """Complex chained queries."""

    def test_full_chain(self) -> None:
        q = (
            Query("machine learning")
            .exact("neural network")
            .site("arxiv.org")
            .filetype("pdf")
            .exclude("tutorial")
        )
        result = str(q)
        assert "machine learning" in result
        assert '"neural network"' in result
        assert "site:arxiv.org" in result
        assert "filetype:pdf" in result
        assert "-tutorial" in result
