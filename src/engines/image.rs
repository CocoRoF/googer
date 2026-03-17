// Google image search engine — mirrors googer/engines/images.py

use log::warn;
use scraper::{Html, Selector};

use crate::config::{
    GOOGLE_IMAGES_URL, IMAGE_COLOR_MAP, IMAGE_ITEMS_SELECTOR, IMAGE_LICENSE_MAP,
    IMAGE_SIZE_MAP, IMAGE_THUMBNAIL_SELECTOR, IMAGE_TITLE_SELECTOR, IMAGE_TYPE_MAP,
    IMAGE_URL_SELECTOR, TBM_IMAGES, TIMELIMIT_MAP,
};
use crate::exceptions::GoogerError;
use crate::http_client::HttpClient;
use crate::parser::{first_attr, first_text};
use crate::results::ImageResult;
use crate::utils::{extract_clean_url, normalize_field};

use super::base::{build_base_params, SearchEngine};

pub struct GoogleImagesEngine {
    pub size: Option<String>,
    pub color: Option<String>,
    pub image_type: Option<String>,
    pub license_type: Option<String>,
}

impl SearchEngine<ImageResult> for GoogleImagesEngine {
    fn search(
        &self,
        http: &HttpClient,
        query: &str,
        region: &str,
        safesearch: &str,
        timelimit: Option<&str>,
        page: usize,
    ) -> Result<Vec<ImageResult>, GoogerError> {
        let mut params = build_base_params(query, region, safesearch, page);
        params.push(("tbm".to_string(), TBM_IMAGES.to_string()));

        // Build tbs parameter with filters
        let mut tbs_parts: Vec<String> = Vec::new();
        if let Some(tl) = timelimit {
            if let Some(mapped) = TIMELIMIT_MAP.get(tl) {
                tbs_parts.push(format!("qdr:{mapped}"));
            }
        }
        if let Some(ref s) = self.size {
            if let Some(mapped) = IMAGE_SIZE_MAP.get(s.as_str()) {
                tbs_parts.push(mapped.to_string());
            }
        }
        if let Some(ref c) = self.color {
            if let Some(mapped) = IMAGE_COLOR_MAP.get(c.as_str()) {
                tbs_parts.push(mapped.to_string());
            }
        }
        if let Some(ref t) = self.image_type {
            if let Some(mapped) = IMAGE_TYPE_MAP.get(t.as_str()) {
                tbs_parts.push(mapped.to_string());
            }
        }
        if let Some(ref l) = self.license_type {
            if let Some(mapped) = IMAGE_LICENSE_MAP.get(l.as_str()) {
                tbs_parts.push(mapped.to_string());
            }
        }
        if !tbs_parts.is_empty() {
            params.push(("tbs".to_string(), tbs_parts.join(",")));
        }

        let response = http.get(GOOGLE_IMAGES_URL, &params)?;
        if !response.ok() {
            warn!("Images engine returned status {}", response.status_code);
            return Ok(Vec::new());
        }

        let results = parse_image_results(&response.text);
        Ok(post_process_images(results))
    }
}

fn parse_image_results(html: &str) -> Vec<ImageResult> {
    let document = Html::parse_document(html);
    let items_sel = Selector::parse(IMAGE_ITEMS_SELECTOR).unwrap();
    let title_sel = Selector::parse(IMAGE_TITLE_SELECTOR).unwrap();
    let url_sel = Selector::parse(IMAGE_URL_SELECTOR).unwrap();
    let thumb_sel = Selector::parse(IMAGE_THUMBNAIL_SELECTOR).unwrap();

    let mut results = Vec::new();

    for item in document.select(&items_sel) {
        let title = first_text(&item, &title_sel);
        let url = first_attr(&item, &url_sel, "href");
        let thumbnail = first_attr(&item, &thumb_sel, "src");

        results.push(ImageResult {
            title: normalize_field("title", &title),
            url: normalize_field("url", &url),
            thumbnail: normalize_field("thumbnail", &thumbnail),
            ..Default::default()
        });
    }

    results
}

fn post_process_images(results: Vec<ImageResult>) -> Vec<ImageResult> {
    results
        .into_iter()
        .filter_map(|mut r| {
            r.url = extract_clean_url(&r.url);
            if !r.title.is_empty() || !r.thumbnail.is_empty() {
                Some(r)
            } else {
                None
            }
        })
        .collect()
}
