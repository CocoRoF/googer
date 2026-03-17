// Google video search engine — mirrors googer/engines/videos.py

use log::warn;
use scraper::{Html, Selector};

use crate::config::{
    GOOGLE_VIDEOS_URL, TBM_VIDEOS, TIMELIMIT_MAP, VIDEO_BODY_SELECTOR,
    VIDEO_DATE_SELECTOR, VIDEO_DURATION_MAP, VIDEO_DURATION_SELECTOR, VIDEO_HREF_SELECTOR,
    VIDEO_ITEMS_SELECTOR, VIDEO_SOURCE_SELECTOR, VIDEO_TITLE_SELECTOR,
};
use crate::exceptions::GoogerError;
use crate::http_client::HttpClient;
use crate::parser::{first_attr, first_text};
use crate::results::VideoResult;
use crate::utils::{extract_clean_url, normalize_field};

use super::base::{build_base_params, SearchEngine};

pub struct GoogleVideosEngine {
    pub duration: Option<String>,
}

impl SearchEngine<VideoResult> for GoogleVideosEngine {
    fn search(
        &self,
        http: &HttpClient,
        query: &str,
        region: &str,
        safesearch: &str,
        timelimit: Option<&str>,
        page: usize,
    ) -> Result<Vec<VideoResult>, GoogerError> {
        let mut params = build_base_params(query, region, safesearch, page);
        params.push(("tbm".to_string(), TBM_VIDEOS.to_string()));

        let mut tbs_parts: Vec<String> = Vec::new();
        if let Some(tl) = timelimit {
            if let Some(mapped) = TIMELIMIT_MAP.get(tl) {
                tbs_parts.push(format!("qdr:{mapped}"));
            }
        }
        if let Some(ref d) = self.duration {
            if let Some(mapped) = VIDEO_DURATION_MAP.get(d.as_str()) {
                tbs_parts.push(mapped.to_string());
            }
        }
        if !tbs_parts.is_empty() {
            params.push(("tbs".to_string(), tbs_parts.join(",")));
        }

        let response = http.get(GOOGLE_VIDEOS_URL, &params)?;
        if !response.ok() {
            warn!("Videos engine returned status {}", response.status_code);
            return Ok(Vec::new());
        }

        let results = parse_video_results(&response.text);
        Ok(post_process_videos(results))
    }
}

fn parse_video_results(html: &str) -> Vec<VideoResult> {
    let document = Html::parse_document(html);
    let items_sel = Selector::parse(VIDEO_ITEMS_SELECTOR).unwrap();
    let title_sel = Selector::parse(VIDEO_TITLE_SELECTOR).unwrap();
    let href_sel = Selector::parse(VIDEO_HREF_SELECTOR).unwrap();
    let body_sel = Selector::parse(VIDEO_BODY_SELECTOR).unwrap();
    let duration_sel = Selector::parse(VIDEO_DURATION_SELECTOR).unwrap();
    let source_sel = Selector::parse(VIDEO_SOURCE_SELECTOR).unwrap();
    let date_sel = Selector::parse(VIDEO_DATE_SELECTOR).unwrap();

    let mut results = Vec::new();

    for item in document.select(&items_sel) {
        let title = first_text(&item, &title_sel);
        let url = first_attr(&item, &href_sel, "href");
        let body = first_text(&item, &body_sel);
        let duration = first_text(&item, &duration_sel);
        let source = first_text(&item, &source_sel);
        let date = first_text(&item, &date_sel);

        results.push(VideoResult {
            title: normalize_field("title", &title),
            url: normalize_field("url", &url),
            body: normalize_field("body", &body),
            duration,
            source: normalize_field("source", &source),
            date: normalize_field("date", &date),
            thumbnail: String::new(),
        });
    }

    results
}

fn post_process_videos(results: Vec<VideoResult>) -> Vec<VideoResult> {
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
