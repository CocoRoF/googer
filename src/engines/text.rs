// Google text/web search engine — mirrors googer/engines/text.py

use log::warn;
use scraper::{Html, Selector};

use crate::config::{
    GOOGLE_TEXT_URL, TEXT_BODY_SELECTOR, TEXT_HREF_SELECTOR, TEXT_ITEMS_SELECTOR,
    TEXT_TITLE_SELECTOR, TIMELIMIT_MAP,
};
use crate::exceptions::GoogerError;
use crate::http_client::HttpClient;
use crate::parser::{first_attr, first_text};
use crate::results::TextResult;
use crate::utils::{extract_clean_url, normalize_field};

use super::base::{build_base_params, SearchEngine};

pub struct GoogleTextEngine;

impl SearchEngine<TextResult> for GoogleTextEngine {
    fn search(
        &self,
        http: &HttpClient,
        query: &str,
        region: &str,
        safesearch: &str,
        timelimit: Option<&str>,
        page: usize,
    ) -> Result<Vec<TextResult>, GoogerError> {
        let mut params = build_base_params(query, region, safesearch, page);

        if let Some(tl) = timelimit {
            if let Some(mapped) = TIMELIMIT_MAP.get(tl) {
                params.push(("tbs".to_string(), format!("qdr:{mapped}")));
            }
        }

        let response = http.get(GOOGLE_TEXT_URL, &params)?;
        if !response.ok() {
            warn!("Text engine returned status {}", response.status_code);
            return Ok(Vec::new());
        }

        let results = parse_text_results(&response.text);
        Ok(post_process_text(results))
    }
}

fn parse_text_results(html: &str) -> Vec<TextResult> {
    let document = Html::parse_document(html);
    let items_sel = Selector::parse(TEXT_ITEMS_SELECTOR).unwrap();
    let title_sel = Selector::parse(TEXT_TITLE_SELECTOR).unwrap();
    let href_sel = Selector::parse(TEXT_HREF_SELECTOR).unwrap();
    let body_sel = Selector::parse(TEXT_BODY_SELECTOR).unwrap();

    let mut results = Vec::new();

    for item in document.select(&items_sel) {
        let title = first_text(&item, &title_sel);
        let href = first_attr(&item, &href_sel, "href");
        let body = first_text(&item, &body_sel);

        results.push(TextResult {
            title: normalize_field("title", &title),
            href: normalize_field("href", &href),
            body: normalize_field("body", &body),
        });
    }

    results
}

fn post_process_text(results: Vec<TextResult>) -> Vec<TextResult> {
    results
        .into_iter()
        .filter_map(|mut r| {
            r.href = extract_clean_url(&r.href);
            if !r.title.is_empty() && r.href.starts_with("http") {
                Some(r)
            } else {
                None
            }
        })
        .collect()
}
