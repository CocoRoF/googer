// Base engine shared logic — mirrors googer/engines/base.py
//
// Provides shared parameter building and multi-page search.

use crate::config::{RESULTS_PER_PAGE, SAFESEARCH_MAP};
use crate::exceptions::GoogerError;
use crate::http_client::HttpClient;
use crate::utils::build_region_params;

/// Build the minimal parameter set shared by all engines.
pub fn build_base_params(
    query: &str,
    region: &str,
    safesearch: &str,
    page: usize,
) -> Vec<(String, String)> {
    let mut params = vec![("q".to_string(), query.to_string())];

    let safe_val = SAFESEARCH_MAP
        .get(safesearch.to_lowercase().as_str())
        .copied()
        .unwrap_or("moderate");
    params.push(("safe".to_string(), safe_val.to_string()));

    let start = (page.saturating_sub(1)) * RESULTS_PER_PAGE;
    params.push(("start".to_string(), start.to_string()));

    params.extend(build_region_params(region));
    params
}

/// Trait for a search engine that can produce results of type `T`.
pub trait SearchEngine<T> {
    /// Perform a single-page search.
    fn search(
        &self,
        http: &HttpClient,
        query: &str,
        region: &str,
        safesearch: &str,
        timelimit: Option<&str>,
        page: usize,
    ) -> Result<Vec<T>, GoogerError>;

    /// Search across multiple pages until max_results are collected.
    fn search_pages(
        &self,
        http: &HttpClient,
        query: &str,
        region: &str,
        safesearch: &str,
        timelimit: Option<&str>,
        max_results: usize,
    ) -> Result<Vec<T>, GoogerError> {
        let mut all_results: Vec<T> = Vec::new();
        let pages_needed = max_results.div_ceil(RESULTS_PER_PAGE);

        for page in 1..=pages_needed {
            let batch = self.search(http, query, region, safesearch, timelimit, page)?;
            if batch.is_empty() {
                break;
            }
            all_results.extend(batch);
            if all_results.len() >= max_results {
                break;
            }
        }

        all_results.truncate(max_results);
        Ok(all_results)
    }
}
