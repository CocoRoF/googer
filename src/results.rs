// Result types — mirrors googer/results.py
//
// Each search category has its own struct with serde support.
// PyO3 wrappers expose them to Python with dict-like access.

use pyo3::prelude::*;
use pyo3::types::PyDict;
use serde::{Deserialize, Serialize};
use std::collections::HashSet;

use crate::utils::normalize_field;

// ---------------------------------------------------------------------------
// Rust-side result structs
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TextResult {
    pub title: String,
    pub href: String,
    pub body: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ImageResult {
    pub title: String,
    pub image: String,
    pub thumbnail: String,
    pub url: String,
    pub height: String,
    pub width: String,
    pub source: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct NewsResult {
    pub title: String,
    pub url: String,
    pub body: String,
    pub source: String,
    pub date: String,
    pub image: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct VideoResult {
    pub title: String,
    pub url: String,
    pub body: String,
    pub duration: String,
    pub source: String,
    pub date: String,
    pub thumbnail: String,
}

// ---------------------------------------------------------------------------
// Normalization for results — uses utils::normalize_field
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Trait for generic dedup
// ---------------------------------------------------------------------------

pub trait HasField {
    fn get_field(&self, name: &str) -> &str;
}

impl HasField for TextResult {
    fn get_field(&self, name: &str) -> &str {
        match name {
            "title" => &self.title,
            "href" => &self.href,
            "body" => &self.body,
            _ => "",
        }
    }
}

impl HasField for ImageResult {
    fn get_field(&self, name: &str) -> &str {
        match name {
            "title" => &self.title,
            "image" => &self.image,
            "thumbnail" => &self.thumbnail,
            "url" => &self.url,
            "height" => &self.height,
            "width" => &self.width,
            "source" => &self.source,
            _ => "",
        }
    }
}

impl HasField for NewsResult {
    fn get_field(&self, name: &str) -> &str {
        match name {
            "title" => &self.title,
            "url" => &self.url,
            "body" => &self.body,
            "source" => &self.source,
            "date" => &self.date,
            "image" => &self.image,
            _ => "",
        }
    }
}

impl HasField for VideoResult {
    fn get_field(&self, name: &str) -> &str {
        match name {
            "title" => &self.title,
            "url" => &self.url,
            "body" => &self.body,
            "duration" => &self.duration,
            "source" => &self.source,
            "date" => &self.date,
            "thumbnail" => &self.thumbnail,
            _ => "",
        }
    }
}

/// Deduplicate results by the first non-empty cache field.
pub fn dedup_results<T: HasField + Clone>(items: Vec<T>, cache_fields: &[&str]) -> Vec<T> {
    let mut seen = HashSet::new();
    let mut result = Vec::new();
    for item in items {
        let key = cache_fields
            .iter()
            .find_map(|f| {
                let v = item.get_field(f);
                if v.is_empty() { None } else { Some(v.to_string()) }
            })
            .unwrap_or_default();
        if key.is_empty() || seen.insert(key) {
            result.push(item);
        }
    }
    result
}

// ---------------------------------------------------------------------------
// PyO3 wrappers
// ---------------------------------------------------------------------------

#[pyclass(name = "TextResult")]
#[derive(Clone)]
pub struct PyTextResult {
    inner: TextResult,
}

impl From<TextResult> for PyTextResult {
    fn from(r: TextResult) -> Self {
        Self { inner: r }
    }
}

#[pymethods]
impl PyTextResult {
    #[new]
    #[pyo3(signature = (title="", href="", body=""))]
    fn new(title: &str, href: &str, body: &str) -> Self {
        Self {
            inner: TextResult {
                title: normalize_field("title", title),
                href: normalize_field("href", href),
                body: normalize_field("body", body),
            },
        }
    }

    #[getter]
    fn title(&self) -> &str {
        &self.inner.title
    }
    #[getter]
    fn href(&self) -> &str {
        &self.inner.href
    }
    #[getter]
    fn body(&self) -> &str {
        &self.inner.body
    }

    fn to_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("title", &self.inner.title)?;
        dict.set_item("href", &self.inner.href)?;
        dict.set_item("body", &self.inner.body)?;
        Ok(dict)
    }

    fn keys(&self) -> Vec<&str> {
        vec!["title", "href", "body"]
    }
    fn values(&self) -> Vec<&str> {
        vec![&self.inner.title, &self.inner.href, &self.inner.body]
    }
    fn items(&self) -> Vec<(&str, &str)> {
        vec![
            ("title", self.inner.title.as_str()),
            ("href", self.inner.href.as_str()),
            ("body", self.inner.body.as_str()),
        ]
    }

    #[pyo3(signature = (key, default=None))]
    fn get(&self, key: &str, default: Option<&str>) -> Option<String> {
        match key {
            "title" => Some(self.inner.title.clone()),
            "href" => Some(self.inner.href.clone()),
            "body" => Some(self.inner.body.clone()),
            _ => default.map(|d| d.to_string()),
        }
    }

    fn __getitem__(&self, key: &str) -> PyResult<String> {
        match key {
            "title" => Ok(self.inner.title.clone()),
            "href" => Ok(self.inner.href.clone()),
            "body" => Ok(self.inner.body.clone()),
            _ => Err(pyo3::exceptions::PyKeyError::new_err(key.to_string())),
        }
    }

    fn __contains__(&self, key: &str) -> bool {
        matches!(key, "title" | "href" | "body")
    }

    fn __len__(&self) -> usize {
        3
    }

    fn __repr__(&self) -> String {
        format!(
            "TextResult(title={:?}, href={:?}, body={:?})",
            self.inner.title, self.inner.href, self.inner.body
        )
    }

    fn __str__(&self) -> String {
        format!(
            "TextResult(title={:?}, href={:?})",
            self.inner.title, self.inner.href
        )
    }
}

// -- ImageResult -----------------------------------------------------------

#[pyclass(name = "ImageResult")]
#[derive(Clone)]
pub struct PyImageResult {
    inner: ImageResult,
}

impl From<ImageResult> for PyImageResult {
    fn from(r: ImageResult) -> Self {
        Self { inner: r }
    }
}

#[pymethods]
impl PyImageResult {
    #[new]
    #[pyo3(signature = (title="", image="", thumbnail="", url="", height="", width="", source=""))]
    fn new(
        title: &str,
        image: &str,
        thumbnail: &str,
        url: &str,
        height: &str,
        width: &str,
        source: &str,
    ) -> Self {
        Self {
            inner: ImageResult {
                title: normalize_field("title", title),
                image: normalize_field("image", image),
                thumbnail: normalize_field("thumbnail", thumbnail),
                url: normalize_field("url", url),
                height: height.to_string(),
                width: width.to_string(),
                source: normalize_field("source", source),
            },
        }
    }

    #[getter]
    fn title(&self) -> &str { &self.inner.title }
    #[getter]
    fn image(&self) -> &str { &self.inner.image }
    #[getter]
    fn thumbnail(&self) -> &str { &self.inner.thumbnail }
    #[getter]
    fn url(&self) -> &str { &self.inner.url }
    #[getter]
    fn height(&self) -> &str { &self.inner.height }
    #[getter]
    fn width(&self) -> &str { &self.inner.width }
    #[getter]
    fn source(&self) -> &str { &self.inner.source }

    fn to_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("title", &self.inner.title)?;
        dict.set_item("image", &self.inner.image)?;
        dict.set_item("thumbnail", &self.inner.thumbnail)?;
        dict.set_item("url", &self.inner.url)?;
        dict.set_item("height", &self.inner.height)?;
        dict.set_item("width", &self.inner.width)?;
        dict.set_item("source", &self.inner.source)?;
        Ok(dict)
    }

    fn keys(&self) -> Vec<&str> {
        vec!["title", "image", "thumbnail", "url", "height", "width", "source"]
    }

    fn values(&self) -> Vec<&str> {
        vec![
            &self.inner.title, &self.inner.image, &self.inner.thumbnail,
            &self.inner.url, &self.inner.height, &self.inner.width, &self.inner.source,
        ]
    }

    fn items(&self) -> Vec<(&str, &str)> {
        vec![
            ("title", self.inner.title.as_str()),
            ("image", self.inner.image.as_str()),
            ("thumbnail", self.inner.thumbnail.as_str()),
            ("url", self.inner.url.as_str()),
            ("height", self.inner.height.as_str()),
            ("width", self.inner.width.as_str()),
            ("source", self.inner.source.as_str()),
        ]
    }

    #[pyo3(signature = (key, default=None))]
    fn get(&self, key: &str, default: Option<&str>) -> Option<String> {
        match key {
            "title" => Some(self.inner.title.clone()),
            "image" => Some(self.inner.image.clone()),
            "thumbnail" => Some(self.inner.thumbnail.clone()),
            "url" => Some(self.inner.url.clone()),
            "height" => Some(self.inner.height.clone()),
            "width" => Some(self.inner.width.clone()),
            "source" => Some(self.inner.source.clone()),
            _ => default.map(|d| d.to_string()),
        }
    }

    fn __getitem__(&self, key: &str) -> PyResult<String> {
        self.get(key, None)
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err(key.to_string()))
    }

    fn __contains__(&self, key: &str) -> bool {
        matches!(key, "title" | "image" | "thumbnail" | "url" | "height" | "width" | "source")
    }

    fn __len__(&self) -> usize { 7 }

    fn __repr__(&self) -> String {
        format!("ImageResult(title={:?}, url={:?})", self.inner.title, self.inner.url)
    }
}

// -- NewsResult -----------------------------------------------------------

#[pyclass(name = "NewsResult")]
#[derive(Clone)]
pub struct PyNewsResult {
    inner: NewsResult,
}

impl From<NewsResult> for PyNewsResult {
    fn from(r: NewsResult) -> Self {
        Self { inner: r }
    }
}

#[pymethods]
impl PyNewsResult {
    #[new]
    #[pyo3(signature = (title="", url="", body="", source="", date="", image=""))]
    fn new(title: &str, url: &str, body: &str, source: &str, date: &str, image: &str) -> Self {
        Self {
            inner: NewsResult {
                title: normalize_field("title", title),
                url: normalize_field("url", url),
                body: normalize_field("body", body),
                source: normalize_field("source", source),
                date: normalize_field("date", date),
                image: normalize_field("image", image),
            },
        }
    }

    #[getter]
    fn title(&self) -> &str { &self.inner.title }
    #[getter]
    fn url(&self) -> &str { &self.inner.url }
    #[getter]
    fn body(&self) -> &str { &self.inner.body }
    #[getter]
    fn source(&self) -> &str { &self.inner.source }
    #[getter]
    fn date(&self) -> &str { &self.inner.date }
    #[getter]
    fn image(&self) -> &str { &self.inner.image }

    fn to_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("title", &self.inner.title)?;
        dict.set_item("url", &self.inner.url)?;
        dict.set_item("body", &self.inner.body)?;
        dict.set_item("source", &self.inner.source)?;
        dict.set_item("date", &self.inner.date)?;
        dict.set_item("image", &self.inner.image)?;
        Ok(dict)
    }

    fn keys(&self) -> Vec<&str> {
        vec!["title", "url", "body", "source", "date", "image"]
    }

    fn values(&self) -> Vec<&str> {
        vec![
            &self.inner.title, &self.inner.url, &self.inner.body,
            &self.inner.source, &self.inner.date, &self.inner.image,
        ]
    }

    fn items(&self) -> Vec<(&str, &str)> {
        vec![
            ("title", self.inner.title.as_str()),
            ("url", self.inner.url.as_str()),
            ("body", self.inner.body.as_str()),
            ("source", self.inner.source.as_str()),
            ("date", self.inner.date.as_str()),
            ("image", self.inner.image.as_str()),
        ]
    }

    #[pyo3(signature = (key, default=None))]
    fn get(&self, key: &str, default: Option<&str>) -> Option<String> {
        match key {
            "title" => Some(self.inner.title.clone()),
            "url" => Some(self.inner.url.clone()),
            "body" => Some(self.inner.body.clone()),
            "source" => Some(self.inner.source.clone()),
            "date" => Some(self.inner.date.clone()),
            "image" => Some(self.inner.image.clone()),
            _ => default.map(|d| d.to_string()),
        }
    }

    fn __getitem__(&self, key: &str) -> PyResult<String> {
        self.get(key, None)
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err(key.to_string()))
    }

    fn __contains__(&self, key: &str) -> bool {
        matches!(key, "title" | "url" | "body" | "source" | "date" | "image")
    }

    fn __len__(&self) -> usize { 6 }

    fn __repr__(&self) -> String {
        format!("NewsResult(title={:?}, url={:?})", self.inner.title, self.inner.url)
    }
}

// -- VideoResult -----------------------------------------------------------

#[pyclass(name = "VideoResult")]
#[derive(Clone)]
pub struct PyVideoResult {
    inner: VideoResult,
}

impl From<VideoResult> for PyVideoResult {
    fn from(r: VideoResult) -> Self {
        Self { inner: r }
    }
}

#[pymethods]
impl PyVideoResult {
    #[new]
    #[pyo3(signature = (title="", url="", body="", duration="", source="", date="", thumbnail=""))]
    fn new(
        title: &str, url: &str, body: &str, duration: &str,
        source: &str, date: &str, thumbnail: &str,
    ) -> Self {
        Self {
            inner: VideoResult {
                title: normalize_field("title", title),
                url: normalize_field("url", url),
                body: normalize_field("body", body),
                duration: duration.to_string(),
                source: normalize_field("source", source),
                date: normalize_field("date", date),
                thumbnail: normalize_field("thumbnail", thumbnail),
            },
        }
    }

    #[getter]
    fn title(&self) -> &str { &self.inner.title }
    #[getter]
    fn url(&self) -> &str { &self.inner.url }
    #[getter]
    fn body(&self) -> &str { &self.inner.body }
    #[getter]
    fn duration(&self) -> &str { &self.inner.duration }
    #[getter]
    fn source(&self) -> &str { &self.inner.source }
    #[getter]
    fn date(&self) -> &str { &self.inner.date }
    #[getter]
    fn thumbnail(&self) -> &str { &self.inner.thumbnail }

    fn to_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("title", &self.inner.title)?;
        dict.set_item("url", &self.inner.url)?;
        dict.set_item("body", &self.inner.body)?;
        dict.set_item("duration", &self.inner.duration)?;
        dict.set_item("source", &self.inner.source)?;
        dict.set_item("date", &self.inner.date)?;
        dict.set_item("thumbnail", &self.inner.thumbnail)?;
        Ok(dict)
    }

    fn keys(&self) -> Vec<&str> {
        vec!["title", "url", "body", "duration", "source", "date", "thumbnail"]
    }

    fn values(&self) -> Vec<&str> {
        vec![
            &self.inner.title, &self.inner.url, &self.inner.body,
            &self.inner.duration, &self.inner.source, &self.inner.date, &self.inner.thumbnail,
        ]
    }

    fn items(&self) -> Vec<(&str, &str)> {
        vec![
            ("title", self.inner.title.as_str()),
            ("url", self.inner.url.as_str()),
            ("body", self.inner.body.as_str()),
            ("duration", self.inner.duration.as_str()),
            ("source", self.inner.source.as_str()),
            ("date", self.inner.date.as_str()),
            ("thumbnail", self.inner.thumbnail.as_str()),
        ]
    }

    #[pyo3(signature = (key, default=None))]
    fn get(&self, key: &str, default: Option<&str>) -> Option<String> {
        match key {
            "title" => Some(self.inner.title.clone()),
            "url" => Some(self.inner.url.clone()),
            "body" => Some(self.inner.body.clone()),
            "duration" => Some(self.inner.duration.clone()),
            "source" => Some(self.inner.source.clone()),
            "date" => Some(self.inner.date.clone()),
            "thumbnail" => Some(self.inner.thumbnail.clone()),
            _ => default.map(|d| d.to_string()),
        }
    }

    fn __getitem__(&self, key: &str) -> PyResult<String> {
        self.get(key, None)
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err(key.to_string()))
    }

    fn __contains__(&self, key: &str) -> bool {
        matches!(key, "title" | "url" | "body" | "duration" | "source" | "date" | "thumbnail")
    }

    fn __len__(&self) -> usize { 7 }

    fn __repr__(&self) -> String {
        format!("VideoResult(title={:?}, url={:?})", self.inner.title, self.inner.url)
    }
}
