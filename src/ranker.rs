// Ranker — mirrors googer/ranker.py
//
// Simple filter ranker that buckets results by query-token overlap.

use pyo3::prelude::*;
use regex::Regex;
use std::sync::LazyLock;

use crate::results::{HasField, TextResult};

static SPLITTER: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\W+").unwrap());

pub struct Ranker {
    min_token_length: usize,
}

impl Ranker {
    pub fn new(min_token_length: usize) -> Self {
        Self { min_token_length }
    }

    fn tokenize(&self, query: &str) -> Vec<String> {
        SPLITTER
            .split(&query.to_lowercase())
            .filter(|tok| tok.len() >= self.min_token_length)
            .map(|s| s.to_string())
            .collect()
    }

    fn has_any(text: &str, tokens: &[String]) -> bool {
        let lower = text.to_lowercase();
        tokens.iter().any(|tok| lower.contains(tok.as_str()))
    }

    /// Rank text results by query relevance.
    pub fn rank_text(&self, docs: Vec<TextResult>, query: &str) -> Vec<TextResult> {
        let tokens = self.tokenize(query);
        if tokens.is_empty() {
            return docs;
        }

        let mut wiki = Vec::new();
        let mut both = Vec::new();
        let mut title_only = Vec::new();
        let mut body_only = Vec::new();
        let mut neither = Vec::new();

        for doc in docs {
            let href = doc.get_field("href");
            let title = doc.get_field("title");
            let body = doc.get_field("body");

            // Skip Wikimedia category pages
            if title.contains("Category:") && title.contains("Wikimedia") {
                continue;
            }

            if href.contains("wikipedia.org") {
                wiki.push(doc);
                continue;
            }

            let ht = Self::has_any(title, &tokens);
            let hb = Self::has_any(body, &tokens);

            if ht && hb {
                both.push(doc);
            } else if ht {
                title_only.push(doc);
            } else if hb {
                body_only.push(doc);
            } else {
                neither.push(doc);
            }
        }

        let mut result = Vec::new();
        result.extend(wiki);
        result.extend(both);
        result.extend(title_only);
        result.extend(body_only);
        result.extend(neither);
        result
    }
}

// PyO3 wrapper (not directly needed since ranking happens inside Googer,
// but exposed for advanced users)

#[pyclass(name = "Ranker")]
pub struct PyRanker {
    #[allow(dead_code)]
    inner: Ranker,
}

#[pymethods]
impl PyRanker {
    #[new]
    #[pyo3(signature = (min_token_length=3))]
    fn new(min_token_length: usize) -> Self {
        Self {
            inner: Ranker::new(min_token_length),
        }
    }
}
