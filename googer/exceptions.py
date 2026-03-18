"""Googer exceptions.

Defines a clear exception hierarchy for Google search operations.
All exceptions inherit from :class:`GoogerException` so callers
can catch a single base type when they don't need granularity.
"""


class GoogerException(Exception):
    """Base exception for all Googer errors."""


class HttpException(GoogerException):
    """Raised when an HTTP request fails unexpectedly."""


class TimeoutException(GoogerException):
    """Raised when a request exceeds the configured timeout."""


class RateLimitException(GoogerException):
    """Raised when Google returns a rate-limit / CAPTCHA response."""


class ParseException(GoogerException):
    """Raised when HTML parsing fails to extract expected data."""


class QueryBuildException(GoogerException):
    """Raised when a search query cannot be constructed."""


class NoResultsException(GoogerException):
    """Raised when a search returns zero results."""
