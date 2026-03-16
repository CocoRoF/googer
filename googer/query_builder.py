"""Advanced Google query builder for Googer.

Provides a fluent, chainable API for constructing complex Google search
queries using all supported operators.

Example::

    from googer import Query

    q = (
        Query("machine learning")
        .exact("neural network")
        .site("arxiv.org")
        .filetype("pdf")
        .exclude("tutorial")
        .date_range("2024-01-01", "2024-12-31")
    )
    print(q)
    # machine learning "neural network" site:arxiv.org filetype:pdf -tutorial daterange:2024-01-01..2024-12-31
"""

from __future__ import annotations

from .exceptions import QueryBuildException


class Query:
    """Fluent builder for Google search queries.

    Every modifier method returns ``self`` so calls can be chained.

    Args:
        base: The core search terms.

    Raises:
        QueryBuildException: On invalid parameter combinations.

    """

    def __init__(self, base: str = "") -> None:
        self._base = base.strip()
        self._exact_phrases: list[str] = []
        self._or_terms: list[str] = []
        self._exclude_terms: list[str] = []
        self._site: str | None = None
        self._filetype: str | None = None
        self._intitle: str | None = None
        self._inurl: str | None = None
        self._intext: str | None = None
        self._related: str | None = None
        self._cache: str | None = None
        self._date_start: str | None = None
        self._date_end: str | None = None
        self._extras: list[str] = []

    # -- Chainable modifiers ------------------------------------------------

    def exact(self, phrase: str) -> Query:
        """Add an exact-match phrase (wrapped in double quotes).

        Args:
            phrase: The phrase to match exactly.

        Returns:
            Self for chaining.

        """
        if phrase.strip():
            self._exact_phrases.append(phrase.strip())
        return self

    def or_term(self, term: str) -> Query:
        """Add an OR-alternative term.

        Args:
            term: A term that Google should treat as an alternative.

        Returns:
            Self for chaining.

        """
        if term.strip():
            self._or_terms.append(term.strip())
        return self

    def exclude(self, term: str) -> Query:
        """Exclude pages containing *term*.

        Args:
            term: Word or phrase to exclude.

        Returns:
            Self for chaining.

        """
        if term.strip():
            self._exclude_terms.append(term.strip())
        return self

    def site(self, domain: str) -> Query:
        """Restrict results to a specific site or domain.

        Args:
            domain: e.g. ``"github.com"`` or ``"*.edu"``.

        Returns:
            Self for chaining.

        """
        self._site = domain.strip()
        return self

    def filetype(self, ext: str) -> Query:
        """Restrict results to a specific file type.

        Args:
            ext: File extension without the dot (``"pdf"``, ``"docx"``, …).

        Returns:
            Self for chaining.

        """
        self._filetype = ext.strip().lstrip(".")
        return self

    def intitle(self, text: str) -> Query:
        """Require *text* to appear in the page title.

        Args:
            text: Text that must appear in the title.

        Returns:
            Self for chaining.

        """
        self._intitle = text.strip()
        return self

    def inurl(self, text: str) -> Query:
        """Require *text* to appear in the page URL.

        Args:
            text: Text that must appear in the URL.

        Returns:
            Self for chaining.

        """
        self._inurl = text.strip()
        return self

    def intext(self, text: str) -> Query:
        """Require *text* to appear in the page body.

        Args:
            text: Text that must appear in the body.

        Returns:
            Self for chaining.

        """
        self._intext = text.strip()
        return self

    def related(self, url: str) -> Query:
        """Find pages related to *url*.

        Args:
            url: Reference URL.

        Returns:
            Self for chaining.

        """
        self._related = url.strip()
        return self

    def cache(self, url: str) -> Query:
        """Request Google's cached version of *url*.

        Args:
            url: URL to retrieve cache for.

        Returns:
            Self for chaining.

        """
        self._cache = url.strip()
        return self

    def date_range(self, start: str, end: str) -> Query:
        """Restrict to a custom date range.

        Google uses ``daterange:`` with Julian dates, but this builder
        accepts ISO-format strings and converts them internally.

        Args:
            start: Start date in ``YYYY-MM-DD`` format.
            end:   End date in ``YYYY-MM-DD`` format.

        Returns:
            Self for chaining.

        """
        self._date_start = start.strip()
        self._date_end = end.strip()
        return self

    def raw(self, fragment: str) -> Query:
        """Append an arbitrary raw fragment to the query.

        Use this for any operator not directly supported by the builder.

        Args:
            fragment: Raw query fragment.

        Returns:
            Self for chaining.

        """
        if fragment.strip():
            self._extras.append(fragment.strip())
        return self

    # -- Build the final query string ---------------------------------------

    def build(self) -> str:
        """Compile the query into a single Google-compatible search string.

        Returns:
            The final query string.

        Raises:
            QueryBuildException: If the resulting query is empty.

        """
        parts: list[str] = []

        # Base terms
        if self._base:
            parts.append(self._base)

        # Exact phrases
        for phrase in self._exact_phrases:
            parts.append(f'"{phrase}"')

        # OR terms
        if self._or_terms:
            or_block = " OR ".join(self._or_terms)
            parts.append(f"({or_block})")

        # Exclusions
        for term in self._exclude_terms:
            parts.append(f"-{term}")

        # Operators
        if self._site:
            parts.append(f"site:{self._site}")
        if self._filetype:
            parts.append(f"filetype:{self._filetype}")
        if self._intitle:
            parts.append(f"intitle:{self._intitle}")
        if self._inurl:
            parts.append(f"inurl:{self._inurl}")
        if self._intext:
            parts.append(f"intext:{self._intext}")
        if self._related:
            parts.append(f"related:{self._related}")
        if self._cache:
            parts.append(f"cache:{self._cache}")

        # Date range
        if self._date_start and self._date_end:
            parts.append(f"after:{self._date_start} before:{self._date_end}")

        # Raw extras
        parts.extend(self._extras)

        query = " ".join(parts).strip()
        if not query:
            msg = "Cannot build an empty query. Provide at least a base term."
            raise QueryBuildException(msg)
        return query

    # -- Dunder methods -----------------------------------------------------

    def __str__(self) -> str:
        """Return the compiled query string."""
        return self.build()

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        try:
            q = self.build()
        except QueryBuildException:
            q = "<empty>"
        return f"Query({q!r})"

    def __bool__(self) -> bool:
        """``True`` if the query is non-empty."""
        try:
            return bool(self.build())
        except QueryBuildException:
            return False
