"""HTML parser for Googer.

Provides a robust XPath-driven extraction engine that converts raw
Google result pages into structured result objects.
"""

import logging
from collections.abc import Mapping
from functools import cached_property
from typing import TypeVar

from lxml import html as lxml_html
from lxml.etree import HTMLParser as LHTMLParser

from .results import BaseResult

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseResult)


class GoogleParser:
    """XPath-based parser for Google search result pages.

    Args:
        items_xpath: XPath expression that selects individual result nodes.
        elements_xpath: Mapping from result-field name to an XPath expression
            evaluated *relative* to each item node.

    """

    def __init__(
        self,
        items_xpath: str,
        elements_xpath: Mapping[str, str],
    ) -> None:
        self.items_xpath = items_xpath
        self.elements_xpath = elements_xpath

    @cached_property
    def _html_parser(self) -> LHTMLParser:
        """Lazily-initialised lxml HTML parser."""
        return LHTMLParser(
            remove_blank_text=True,
            remove_comments=True,
            remove_pis=True,
            collect_ids=False,
        )

    # -- public API ---------------------------------------------------------

    def parse(self, html_text: str, result_cls: type[T]) -> list[T]:
        """Parse *html_text* and return a list of *result_cls* instances.

        Args:
            html_text: Raw HTML from a Google results page.
            result_cls: The dataclass type to instantiate for each result.

        Returns:
            Extracted results (may be empty).

        """
        html_text = self._pre_process(html_text)
        tree = lxml_html.fromstring(html_text, parser=self._html_parser)
        items = tree.xpath(self.items_xpath)

        results: list[T] = []
        for item in items:
            result = result_cls()
            for field_name, xpath_expr in self.elements_xpath.items():
                parts = (x.strip() for x in item.xpath(xpath_expr))
                data = " ".join("".join(parts).split())
                if data:
                    setattr(result, field_name, data)
            results.append(result)

        logger.debug("Parsed %d items from %d HTML bytes", len(results), len(html_text))
        return results

    # -- extensible hooks ---------------------------------------------------

    def _pre_process(self, html_text: str) -> str:
        """Optional pre-processing of raw HTML before parsing.

        Subclasses can override this to strip unwanted sections,
        inject fixes, etc.
        """
        return html_text
