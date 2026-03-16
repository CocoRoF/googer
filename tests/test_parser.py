"""Tests for the HTML parser."""

from googer.parser import GoogleParser
from googer.results import TextResult


class TestGoogleParser:
    """GoogleParser extraction tests."""

    SAMPLE_HTML = """
    <html>
    <body>
        <div data-snc="1">
            <a href="/url?q=https://example.com&sa=U">
                <div role="link">Example Title</div>
            </a>
            <div data-sncf="1">This is the body text of the result.</div>
        </div>
        <div data-snc="2">
            <a href="/url?q=https://python.org&sa=U">
                <div role="link">Python.org</div>
            </a>
            <div data-sncf="1">The official Python website.</div>
        </div>
    </body>
    </html>
    """

    def test_parse_text_results(self) -> None:
        parser = GoogleParser(
            items_xpath="//div[@data-snc]",
            elements_xpath={
                "title": ".//div[@role='link']//text()",
                "href": ".//a/@href",
                "body": "./div[@data-sncf]//text()",
            },
        )
        results = parser.parse(self.SAMPLE_HTML, TextResult)
        assert len(results) == 2
        assert results[0].title == "Example Title"
        assert results[0].href == "/url?q=https://example.com&sa=U"
        assert "body text" in results[0].body

    def test_parse_empty_html(self) -> None:
        parser = GoogleParser(
            items_xpath="//div[@data-snc]",
            elements_xpath={"title": ".//h3//text()"},
        )
        results = parser.parse("<html><body></body></html>", TextResult)
        assert results == []

    def test_parser_reusable(self) -> None:
        """Parser can be used multiple times."""
        parser = GoogleParser(
            items_xpath="//div[@data-snc]",
            elements_xpath={"title": ".//div[@role='link']//text()"},
        )
        r1 = parser.parse(self.SAMPLE_HTML, TextResult)
        r2 = parser.parse(self.SAMPLE_HTML, TextResult)
        assert len(r1) == len(r2)
