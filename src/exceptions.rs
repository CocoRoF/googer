// Googer exceptions — mirrors googer/exceptions.py
//
// Defines both Rust error types (with thiserror) and PyO3 exception classes
// so Python consumers get the same exception hierarchy.

use pyo3::create_exception;
use pyo3::exceptions::PyException;
use thiserror::Error;

// ---------------------------------------------------------------------------
// Rust-side error enum
// ---------------------------------------------------------------------------

#[derive(Debug, Error)]
pub enum GoogerError {
    #[error("{0}")]
    General(String),

    #[error("HTTP error: {0}")]
    Http(String),

    #[error("Timeout: {0}")]
    Timeout(String),

    #[error("Rate limited: {0}")]
    RateLimit(String),

    #[error("Parse error: {0}")]
    Parse(String),

    #[error("Query build error: {0}")]
    QueryBuild(String),

    #[error("No results: {0}")]
    NoResults(String),
}

// ---------------------------------------------------------------------------
// Python exception classes
// ---------------------------------------------------------------------------

create_exception!(googer._core, PyGoogerException, PyException, "Base exception for all Googer errors.");
create_exception!(googer._core, PyHttpException, PyGoogerException, "Raised when an HTTP request fails unexpectedly.");
create_exception!(googer._core, PyTimeoutException, PyGoogerException, "Raised when a request exceeds the configured timeout.");
create_exception!(googer._core, PyRateLimitException, PyGoogerException, "Raised when Google returns a rate-limit / CAPTCHA response.");
create_exception!(googer._core, PyParseException, PyGoogerException, "Raised when HTML parsing fails to extract expected data.");
create_exception!(googer._core, PyQueryBuildException, PyGoogerException, "Raised when a search query cannot be constructed.");
create_exception!(googer._core, PyNoResultsException, PyGoogerException, "Raised when a search returns zero results.");
