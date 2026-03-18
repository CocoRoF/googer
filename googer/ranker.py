"""Simple filter ranker for Googer.

Provides a lightweight, zero-dependency relevance ranker that
buckets results based on query-token overlap.
"""

import re
from typing import Final, TypeVar

_T = TypeVar("_T")


class Ranker:
    """Rank search results by query-token overlap.

    Strategy:
      1. Pull any *Wikipedia* result to the top.
      2. Bucket remaining results:
         - query tokens appear in **both** title & body
         - title only
         - body only
         - neither
      3. Return concatenated buckets in that priority order.

    Args:
        min_token_length: Ignore query tokens shorter than this.

    """

    _splitter: Final = re.compile(r"\W+")

    def __init__(self, min_token_length: int = 3) -> None:
        self.min_token_length = min_token_length

    # -- internals ----------------------------------------------------------

    def _tokenize(self, query: str) -> set[str]:
        """Split on non-word chars and drop short tokens."""
        return {
            tok
            for tok in self._splitter.split(query.lower())
            if len(tok) >= self.min_token_length
        }

    @staticmethod
    def _has_any(text: str, tokens: set[str]) -> bool:
        """Return ``True`` if *text* contains any of *tokens*."""
        lower = text.lower()
        return any(tok in lower for tok in tokens)

    # -- public API ---------------------------------------------------------

    def rank(self, docs: list[_T], query: str) -> list[_T]:
        """Return *docs* reordered by relevance to *query*.

        Args:
            docs: List of result objects or dicts (must support ``.get()``
                for ``title``, ``body``/``description``, ``href``/``url``).
            query: The original search query.

        Returns:
            Reordered copy of *docs*.

        """
        tokens = self._tokenize(query)
        if not tokens:
            return docs

        wiki: list[_T] = []
        both: list[_T] = []
        title_only: list[_T] = []
        body_only: list[_T] = []
        neither: list[_T] = []

        for doc in docs:
            href = doc.get("href", doc.get("url", ""))  # type: ignore[union-attr]
            title = doc.get("title", "")  # type: ignore[union-attr]
            body = doc.get("body", doc.get("description", doc.get("snippet", "")))  # type: ignore[union-attr]

            # Skip Wikimedia category pages
            if "Category:" in title and "Wikimedia" in title:
                continue

            # Wikipedia boost
            if "wikipedia.org" in href:
                wiki.append(doc)
                continue

            hit_title = self._has_any(title, tokens)
            hit_body = self._has_any(body, tokens)

            if hit_title and hit_body:
                both.append(doc)
            elif hit_title:
                title_only.append(doc)
            elif hit_body:
                body_only.append(doc)
            else:
                neither.append(doc)

        return wiki + both + title_only + body_only + neither
