// Configuration constants — mirrors googer/config.py

pub const DEFAULT_TIMEOUT: u64 = 10;
pub const DEFAULT_MAX_RETRIES: u32 = 3;
pub const RETRY_BACKOFF_FACTOR: f64 = 0.5;

pub const GOOGLE_TEXT_URL: &str = "https://www.google.com/search";
pub const GOOGLE_IMAGES_URL: &str = "https://www.google.com/search";
pub const GOOGLE_NEWS_URL: &str = "https://www.google.com/search";
pub const GOOGLE_VIDEOS_URL: &str = "https://www.google.com/search";

pub const DEFAULT_REGION: &str = "us-en";
pub const DEFAULT_SAFESEARCH: &str = "moderate";
pub const DEFAULT_MAX_RESULTS: usize = 10;
pub const RESULTS_PER_PAGE: usize = 10;

use std::collections::HashMap;
use std::sync::LazyLock;

pub static SAFESEARCH_MAP: LazyLock<HashMap<&str, &str>> =
    LazyLock::new(|| HashMap::from([("on", "active"), ("moderate", "moderate"), ("off", "off")]));

pub static TIMELIMIT_MAP: LazyLock<HashMap<&str, &str>> =
    LazyLock::new(|| HashMap::from([("h", "h"), ("d", "d"), ("w", "w"), ("m", "m"), ("y", "y")]));

pub static IMAGE_SIZE_MAP: LazyLock<HashMap<&str, &str>> =
    LazyLock::new(|| HashMap::from([("large", "isz:l"), ("medium", "isz:m"), ("icon", "isz:i")]));

pub static IMAGE_COLOR_MAP: LazyLock<HashMap<&str, &str>> = LazyLock::new(|| {
    HashMap::from([
        ("color", "ic:color"),
        ("gray", "ic:gray"),
        ("mono", "ic:mono"),
        ("trans", "ic:trans"),
    ])
});

pub static IMAGE_TYPE_MAP: LazyLock<HashMap<&str, &str>> = LazyLock::new(|| {
    HashMap::from([
        ("face", "itp:face"),
        ("photo", "itp:photo"),
        ("clipart", "itp:clipart"),
        ("lineart", "itp:lineart"),
        ("animated", "itp:animated"),
    ])
});

pub static IMAGE_LICENSE_MAP: LazyLock<HashMap<&str, &str>> =
    LazyLock::new(|| HashMap::from([("creative_commons", "il:cl"), ("commercial", "il:ol")]));

pub static VIDEO_DURATION_MAP: LazyLock<HashMap<&str, &str>> =
    LazyLock::new(|| HashMap::from([("short", "dur:s"), ("medium", "dur:m"), ("long", "dur:l")]));

pub const TBM_NEWS: &str = "nws";
pub const TBM_IMAGES: &str = "isch";
pub const TBM_VIDEOS: &str = "vid";

// CSS selectors (replacing XPath from the Python version)
// text
pub const TEXT_ITEMS_SELECTOR: &str = "div[data-snc]";
pub const TEXT_TITLE_SELECTOR: &str = "div[role='link']";
pub const TEXT_HREF_SELECTOR: &str = "a[href]";
pub const TEXT_BODY_SELECTOR: &str = "div[data-sncf]";

// news
pub const NEWS_ITEMS_SELECTOR: &str = "a.WlydOe";
pub const NEWS_TITLE_SELECTOR: &str = "div[role='heading']";
pub const NEWS_SOURCE_SELECTOR: &str = "div.MgUUmf span";
pub const NEWS_DATE_SELECTOR: &str = "div.OSrXXb span";

// video
pub const VIDEO_ITEMS_SELECTOR: &str = "div.MjjYud";
pub const VIDEO_TITLE_SELECTOR: &str = "h3";
pub const VIDEO_HREF_SELECTOR: &str = "a[href]";
pub const VIDEO_BODY_SELECTOR: &str = "div.ITZIwc";
pub const VIDEO_DURATION_SELECTOR: &str = "div.J1mWY";
pub const VIDEO_SOURCE_SELECTOR: &str = "span.CA5RN span";
pub const VIDEO_DATE_SELECTOR: &str = "span.rQMQod";

// image
pub const IMAGE_ITEMS_SELECTOR: &str = "div.isv-r.PNCib.MSM1fd.BUooTd";
pub const IMAGE_TITLE_SELECTOR: &str = "h3";
pub const IMAGE_URL_SELECTOR: &str = "a[href]";
pub const IMAGE_THUMBNAIL_SELECTOR: &str = "img[src]";

// Rate-limit indicators
pub const RATE_LIMIT_INDICATORS: &[&str] = &[
    "detected unusual traffic",
    "captcha",
    "/sorry/",
    "recaptcha",
];
