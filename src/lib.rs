// googer — Rust core library with PyO3 Python bindings
//
// Module layout mirrors the original Python package:
//   config      — constants & configuration
//   exceptions  — error types
//   user_agents — rotating User-Agent strings
//   utils       — URL/text normalization helpers
//   results     — result dataclasses (TextResult, ImageResult, etc.)
//   query_builder — fluent query builder
//   http_client — HTTP client with retries & rate-limit detection
//   parser      — HTML/XPath-equivalent CSS-selector parser
//   ranker      — simple relevance ranker
//   engines     — search engine implementations
//   lib (here)  — PyO3 module definition

pub mod config;
pub mod engines;
pub mod exceptions;
pub mod http_client;
pub mod parser;
pub mod query_builder;
pub mod ranker;
pub mod results;
pub mod user_agents;
pub mod utils;

use pyo3::prelude::*;

use engines::base::SearchEngine;
use engines::image::GoogleImagesEngine;
use engines::news::GoogleNewsEngine;
use engines::text::GoogleTextEngine;
use engines::video::GoogleVideosEngine;
use exceptions::{
    PyGoogerException, PyHttpException, PyNoResultsException, PyParseException,
    PyQueryBuildException, PyRateLimitException, PyTimeoutException,
};
use query_builder::PyQuery;
use results::{PyImageResult, PyNewsResult, PyTextResult, PyVideoResult};

// ---------------------------------------------------------------------------
// The main Googer class exposed to Python
// ---------------------------------------------------------------------------

/// Core search facade exposed to Python as ``googer._core.Googer``.
#[pyclass(name = "Googer")]
pub struct PyGooger {
    http: http_client::HttpClient,
    ranker: ranker::Ranker,
}

#[pymethods]
impl PyGooger {
    #[new]
    #[pyo3(signature = (proxy=None, timeout=None, verify=true, max_retries=3))]
    fn new(
        proxy: Option<String>,
        timeout: Option<u64>,
        verify: bool,
        max_retries: u32,
    ) -> PyResult<Self> {
        let resolved_proxy = utils::expand_proxy_alias(proxy.as_deref())
            .or_else(|| std::env::var("GOOGER_PROXY").ok());
        let timeout = timeout.unwrap_or(config::DEFAULT_TIMEOUT);
        let http =
            http_client::HttpClient::new(resolved_proxy.as_deref(), timeout, verify, max_retries)
                .map_err(|e| {
                PyGoogerException::new_err(format!("Failed to create HTTP client: {e}"))
            })?;
        Ok(Self {
            http,
            ranker: ranker::Ranker::new(3),
        })
    }

    fn __enter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    #[pyo3(signature = (_exc_type=None, _exc_val=None, _exc_tb=None))]
    fn __exit__(
        &self,
        _exc_type: Option<PyObject>,
        _exc_val: Option<PyObject>,
        _exc_tb: Option<PyObject>,
    ) {
    }

    /// Perform a Google web/text search.
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (query, *, region="us-en", safesearch="moderate", timelimit=None, max_results=10, page=1, rank=true))]
    fn search(
        &self,
        query: &str,
        region: &str,
        safesearch: &str,
        timelimit: Option<&str>,
        max_results: usize,
        #[allow(unused_variables)] page: usize,
        rank: bool,
    ) -> PyResult<Vec<PyTextResult>> {
        let query_str = query.trim();
        if query_str.is_empty() {
            return Err(PyGoogerException::new_err(
                "Search query must not be empty.",
            ));
        }
        let engine = GoogleTextEngine;
        let raw = engine
            .search_pages(
                &self.http,
                query_str,
                region,
                safesearch,
                timelimit,
                max_results,
            )
            .map_err(|e| PyGoogerException::new_err(e.to_string()))?;
        if raw.is_empty() {
            return Err(PyNoResultsException::new_err(format!(
                "No results found for query: {query_str:?}"
            )));
        }
        let deduped = results::dedup_results(raw, &["href"]);
        let mut ranked: Vec<results::TextResult> = if rank {
            self.ranker.rank_text(deduped, query_str)
        } else {
            deduped
        };
        ranked.truncate(max_results);
        Ok(ranked.into_iter().map(PyTextResult::from).collect())
    }

    /// Perform a Google image search.
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (query, *, region="us-en", safesearch="moderate", timelimit=None, max_results=10, size=None, color=None, image_type=None, license_type=None))]
    fn images(
        &self,
        query: &str,
        region: &str,
        safesearch: &str,
        timelimit: Option<&str>,
        max_results: usize,
        size: Option<&str>,
        color: Option<&str>,
        image_type: Option<&str>,
        license_type: Option<&str>,
    ) -> PyResult<Vec<PyImageResult>> {
        let query_str = query.trim();
        if query_str.is_empty() {
            return Err(PyGoogerException::new_err(
                "Search query must not be empty.",
            ));
        }
        let engine = GoogleImagesEngine {
            size: size.map(String::from),
            color: color.map(String::from),
            image_type: image_type.map(String::from),
            license_type: license_type.map(String::from),
        };
        let raw = engine
            .search_pages(
                &self.http,
                query_str,
                region,
                safesearch,
                timelimit,
                max_results,
            )
            .map_err(|e| PyGoogerException::new_err(e.to_string()))?;
        if raw.is_empty() {
            return Err(PyNoResultsException::new_err(format!(
                "No results found for query: {query_str:?}"
            )));
        }
        let deduped = results::dedup_results(raw, &["url", "image"]);
        let mut results: Vec<results::ImageResult> = deduped;
        results.truncate(max_results);
        Ok(results.into_iter().map(PyImageResult::from).collect())
    }

    /// Perform a Google news search.
    #[pyo3(signature = (query, *, region="us-en", safesearch="moderate", timelimit=None, max_results=10))]
    fn news(
        &self,
        query: &str,
        region: &str,
        safesearch: &str,
        timelimit: Option<&str>,
        max_results: usize,
    ) -> PyResult<Vec<PyNewsResult>> {
        let query_str = query.trim();
        if query_str.is_empty() {
            return Err(PyGoogerException::new_err(
                "Search query must not be empty.",
            ));
        }
        let engine = GoogleNewsEngine;
        let raw = engine
            .search_pages(
                &self.http,
                query_str,
                region,
                safesearch,
                timelimit,
                max_results,
            )
            .map_err(|e| PyGoogerException::new_err(e.to_string()))?;
        if raw.is_empty() {
            return Err(PyNoResultsException::new_err(format!(
                "No results found for query: {query_str:?}"
            )));
        }
        let deduped = results::dedup_results(raw, &["url"]);
        let mut results: Vec<results::NewsResult> = deduped;
        results.truncate(max_results);
        Ok(results.into_iter().map(PyNewsResult::from).collect())
    }

    /// Perform a Google video search.
    #[pyo3(signature = (query, *, region="us-en", safesearch="moderate", timelimit=None, max_results=10, duration=None))]
    fn videos(
        &self,
        query: &str,
        region: &str,
        safesearch: &str,
        timelimit: Option<&str>,
        max_results: usize,
        duration: Option<&str>,
    ) -> PyResult<Vec<PyVideoResult>> {
        let query_str = query.trim();
        if query_str.is_empty() {
            return Err(PyGoogerException::new_err(
                "Search query must not be empty.",
            ));
        }
        let engine = GoogleVideosEngine {
            duration: duration.map(String::from),
        };
        let raw = engine
            .search_pages(
                &self.http,
                query_str,
                region,
                safesearch,
                timelimit,
                max_results,
            )
            .map_err(|e| PyGoogerException::new_err(e.to_string()))?;
        if raw.is_empty() {
            return Err(PyNoResultsException::new_err(format!(
                "No results found for query: {query_str:?}"
            )));
        }
        let deduped = results::dedup_results(raw, &["url"]);
        let mut results: Vec<results::VideoResult> = deduped;
        results.truncate(max_results);
        Ok(results.into_iter().map(PyVideoResult::from).collect())
    }
}

// ---------------------------------------------------------------------------
// Python module definition
// ---------------------------------------------------------------------------

/// The native ``googer._core`` extension module.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Initialize logging bridge
    pyo3_log::init();

    // Main class
    m.add_class::<PyGooger>()?;

    // Query builder
    m.add_class::<PyQuery>()?;

    // Result types
    m.add_class::<PyTextResult>()?;
    m.add_class::<PyImageResult>()?;
    m.add_class::<PyNewsResult>()?;
    m.add_class::<PyVideoResult>()?;

    // Exceptions
    m.add("GoogerException", m.py().get_type::<PyGoogerException>())?;
    m.add("HttpException", m.py().get_type::<PyHttpException>())?;
    m.add("TimeoutException", m.py().get_type::<PyTimeoutException>())?;
    m.add(
        "RateLimitException",
        m.py().get_type::<PyRateLimitException>(),
    )?;
    m.add("ParseException", m.py().get_type::<PyParseException>())?;
    m.add(
        "QueryBuildException",
        m.py().get_type::<PyQueryBuildException>(),
    )?;
    m.add(
        "NoResultsException",
        m.py().get_type::<PyNoResultsException>(),
    )?;

    Ok(())
}
