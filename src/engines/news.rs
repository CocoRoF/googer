// Google news search engine — mirrors googer/engines/news.py

use log::warn;
use scraper::{Html, Selector};

use crate::config::{
    GOOGLE_NEWS_URL, NEWS_DATE_SELECTOR, NEWS_ITEMS_SELECTOR, NEWS_SOURCE_SELECTOR,
    NEWS_TITLE_SELECTOR, TBM_NEWS, TIMELIMIT_MAP,
};
use crate::exceptions::GoogerError;
use crate::http_client::HttpClient;
use crate::parser::first_text;
use crate::results::NewsResult;
use crate::utils::{extract_clean_url, normalize_field};

use super::base::{build_base_params, SearchEngine};

pub struct GoogleNewsEngine;

impl SearchEngine<NewsResult> for GoogleNewsEngine {
    fn search(
        &self,
        http: &HttpClient,
        query: &str,
        region: &str,
        safesearch: &str,
        timelimit: Option<&str>,
        page: usize,
    ) -> Result<Vec<NewsResult>, GoogerError> {
        let mut params = build_base_params(query, region, safesearch, page);
        params.push(("tbm".to_string(), TBM_NEWS.to_string()));

        if let Some(tl) = timelimit {
            if let Some(mapped) = TIMELIMIT_MAP.get(tl) {
                params.push(("tbs".to_string(), format!("qdr:{mapped}")));
            }
        }

        let response = http.get(GOOGLE_NEWS_URL, &params)?;
        if !response.ok() {
            warn!("News engine returned status {}", response.status_code);
            return Ok(Vec::new());
        }

        let results = parse_news_results(&response.text);
        Ok(post_process_news(results))
    }
}

fn parse_news_results(html: &str) -> Vec<NewsResult> {
    let document = Html::parse_document(html);
    let items_sel = Selector::parse(NEWS_ITEMS_SELECTOR).unwrap();
    let title_sel = Selector::parse(NEWS_TITLE_SELECTOR).unwrap();
    let source_sel = Selector::parse(NEWS_SOURCE_SELECTOR).unwrap();
    let date_sel = Selector::parse(NEWS_DATE_SELECTOR).unwrap();

    let mut results = Vec::new();

    for item in document.select(&items_sel) {
        let title = first_text(&item, &title_sel);
        // For news, the URL is the href attribute of the <a> item itself
        let url = item.value().attr("href").unwrap_or("").to_string();
        let body = first_text(&item, &title_sel); // body mirrors title in news
        let source = first_text(&item, &source_sel);
        let date = first_text(&item, &date_sel);

        results.push(NewsResult {
            title: normalize_field("title", &title),
            url: normalize_field("url", &url),
            body: normalize_field("body", &body),
            source: normalize_field("source", &source),
            date: normalize_field("date", &date),
            image: String::new(),
        });
    }

    results
}

fn post_process_news(results: Vec<NewsResult>) -> Vec<NewsResult> {
    results
        .into_iter()
        .filter_map(|mut r| {
            r.url = extract_clean_url(&r.url);
            if !r.title.is_empty() {
                Some(r)
            } else {
                None
            }
        })
        .collect()
}
