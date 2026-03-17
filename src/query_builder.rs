// Query builder — mirrors googer/query_builder.py
//
// Provides a fluent, chainable API for constructing complex Google search
// queries. Exposed to Python via PyO3.

use pyo3::prelude::*;

use crate::exceptions::PyQueryBuildException;

/// Internal query builder state.
#[derive(Debug, Clone, Default)]
pub struct QueryBuilder {
    pub base: String,
    pub exact_phrases: Vec<String>,
    pub or_terms: Vec<String>,
    pub exclude_terms: Vec<String>,
    pub site: Option<String>,
    pub filetype: Option<String>,
    pub intitle: Option<String>,
    pub inurl: Option<String>,
    pub intext: Option<String>,
    pub related: Option<String>,
    pub cache: Option<String>,
    pub date_start: Option<String>,
    pub date_end: Option<String>,
    pub extras: Vec<String>,
}

impl QueryBuilder {
    pub fn new(base: &str) -> Self {
        Self {
            base: base.trim().to_string(),
            ..Default::default()
        }
    }

    pub fn build(&self) -> Result<String, String> {
        let mut parts: Vec<String> = Vec::new();

        if !self.base.is_empty() {
            parts.push(self.base.clone());
        }

        for phrase in &self.exact_phrases {
            parts.push(format!("\"{phrase}\""));
        }

        if !self.or_terms.is_empty() {
            let or_block = self.or_terms.join(" OR ");
            parts.push(format!("({or_block})"));
        }

        for term in &self.exclude_terms {
            parts.push(format!("-{term}"));
        }

        if let Some(ref s) = self.site {
            parts.push(format!("site:{s}"));
        }
        if let Some(ref f) = self.filetype {
            parts.push(format!("filetype:{f}"));
        }
        if let Some(ref t) = self.intitle {
            parts.push(format!("intitle:{t}"));
        }
        if let Some(ref u) = self.inurl {
            parts.push(format!("inurl:{u}"));
        }
        if let Some(ref t) = self.intext {
            parts.push(format!("intext:{t}"));
        }
        if let Some(ref r) = self.related {
            parts.push(format!("related:{r}"));
        }
        if let Some(ref c) = self.cache {
            parts.push(format!("cache:{c}"));
        }

        if let (Some(ref start), Some(ref end)) = (&self.date_start, &self.date_end) {
            parts.push(format!("after:{start} before:{end}"));
        }

        parts.extend(self.extras.iter().cloned());

        let query = parts.join(" ").trim().to_string();
        if query.is_empty() {
            return Err("Cannot build an empty query. Provide at least a base term.".to_string());
        }
        Ok(query)
    }
}

// ---------------------------------------------------------------------------
// PyO3 wrapper
// ---------------------------------------------------------------------------

#[pyclass(name = "Query")]
#[derive(Clone)]
pub struct PyQuery {
    inner: QueryBuilder,
}

#[pymethods]
impl PyQuery {
    #[new]
    #[pyo3(signature = (base=""))]
    fn new(base: &str) -> Self {
        Self {
            inner: QueryBuilder::new(base),
        }
    }

    /// Add an exact-match phrase (wrapped in double quotes).
    fn exact<'a>(mut slf: PyRefMut<'a, Self>, phrase: &str) -> PyRefMut<'a, Self> {
        let p = phrase.trim();
        if !p.is_empty() {
            slf.inner.exact_phrases.push(p.to_string());
        }
        slf
    }

    /// Add an OR-alternative term.
    fn or_term<'a>(mut slf: PyRefMut<'a, Self>, term: &str) -> PyRefMut<'a, Self> {
        let t = term.trim();
        if !t.is_empty() {
            slf.inner.or_terms.push(t.to_string());
        }
        slf
    }

    /// Exclude pages containing the term.
    fn exclude<'a>(mut slf: PyRefMut<'a, Self>, term: &str) -> PyRefMut<'a, Self> {
        let t = term.trim();
        if !t.is_empty() {
            slf.inner.exclude_terms.push(t.to_string());
        }
        slf
    }

    /// Restrict results to a specific site or domain.
    fn site<'a>(mut slf: PyRefMut<'a, Self>, domain: &str) -> PyRefMut<'a, Self> {
        slf.inner.site = Some(domain.trim().to_string());
        slf
    }

    /// Restrict results to a specific file type.
    fn filetype<'a>(mut slf: PyRefMut<'a, Self>, ext: &str) -> PyRefMut<'a, Self> {
        slf.inner.filetype = Some(ext.trim().trim_start_matches('.').to_string());
        slf
    }

    /// Require text to appear in the page title.
    fn intitle<'a>(mut slf: PyRefMut<'a, Self>, text: &str) -> PyRefMut<'a, Self> {
        slf.inner.intitle = Some(text.trim().to_string());
        slf
    }

    /// Require text to appear in the page URL.
    fn inurl<'a>(mut slf: PyRefMut<'a, Self>, text: &str) -> PyRefMut<'a, Self> {
        slf.inner.inurl = Some(text.trim().to_string());
        slf
    }

    /// Require text to appear in the page body.
    fn intext<'a>(mut slf: PyRefMut<'a, Self>, text: &str) -> PyRefMut<'a, Self> {
        slf.inner.intext = Some(text.trim().to_string());
        slf
    }

    /// Find pages related to a URL.
    fn related<'a>(mut slf: PyRefMut<'a, Self>, url: &str) -> PyRefMut<'a, Self> {
        slf.inner.related = Some(url.trim().to_string());
        slf
    }

    /// Request Google's cached version of a URL.
    fn cache<'a>(mut slf: PyRefMut<'a, Self>, url: &str) -> PyRefMut<'a, Self> {
        slf.inner.cache = Some(url.trim().to_string());
        slf
    }

    /// Restrict to a custom date range (ISO format: YYYY-MM-DD).
    fn date_range<'a>(mut slf: PyRefMut<'a, Self>, start: &str, end: &str) -> PyRefMut<'a, Self> {
        slf.inner.date_start = Some(start.trim().to_string());
        slf.inner.date_end = Some(end.trim().to_string());
        slf
    }

    /// Append an arbitrary raw fragment to the query.
    fn raw<'a>(mut slf: PyRefMut<'a, Self>, fragment: &str) -> PyRefMut<'a, Self> {
        let f = fragment.trim();
        if !f.is_empty() {
            slf.inner.extras.push(f.to_string());
        }
        slf
    }

    /// Compile the query into a Google-compatible search string.
    fn build(&self) -> PyResult<String> {
        self.inner.build().map_err(PyQueryBuildException::new_err)
    }

    fn __str__(&self) -> PyResult<String> {
        self.build()
    }

    fn __repr__(&self) -> String {
        match self.inner.build() {
            Ok(q) => format!("Query({q:?})"),
            Err(_) => "Query('<empty>')".to_string(),
        }
    }

    fn __bool__(&self) -> bool {
        self.inner.build().is_ok()
    }
}
