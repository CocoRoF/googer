// Utility functions — mirrors googer/utils.py
//
// URL normalization, text cleaning, date conversion, proxy expansion,
// region parameter building.

use regex::Regex;
use std::sync::LazyLock;
use unicode_normalization::UnicodeNormalization;

static RE_STRIP_TAGS: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"<.*?>").unwrap());
static RE_MULTI_SPACES: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\s+").unwrap());

/// Unquote a URL and normalize spaces.
pub fn normalize_url(url: &str) -> String {
    if url.is_empty() {
        return String::new();
    }
    let decoded = urlencoding::decode(url)
        .map(|c| c.into_owned())
        .unwrap_or_else(|_| url.to_string());
    decoded.replace(' ', "+")
}

/// Normalize text for display.
///
/// Pipeline: strip HTML tags → unescape entities → NFC normalize →
/// remove control characters → collapse whitespace.
pub fn normalize_text(raw: &str) -> String {
    if raw.is_empty() {
        return String::new();
    }

    // 1. Strip HTML tags
    let text = RE_STRIP_TAGS.replace_all(raw, "");

    // 2. Unescape HTML entities
    let text = html_escape::decode_html_entities(&text);

    // 3. Unicode NFC normalization
    let text: String = text.nfc().collect();

    // 4. Remove control characters
    let text: String = text
        .chars()
        .filter(|c| !c.is_control() || *c == ' ' || *c == '\n' || *c == '\t')
        .collect();

    // 5. Collapse whitespace
    RE_MULTI_SPACES.replace_all(&text, " ").trim().to_string()
}

/// Convert a Unix timestamp to ISO-8601, or pass through a string.
pub fn normalize_date(value: &str) -> String {
    // Try to parse as integer (Unix timestamp)
    if let Ok(ts) = value.parse::<i64>() {
        if ts >= 0 {
            let secs = ts;
            let days = secs / 86400;
            let time_of_day = secs % 86400;
            let hours = time_of_day / 3600;
            let minutes = (time_of_day % 3600) / 60;
            let seconds = time_of_day % 60;

            // Simple days-to-date conversion (from Unix epoch 1970-01-01)
            let (year, month, day) = days_to_ymd(days);
            return format!(
                "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}+00:00",
                year, month, day, hours, minutes, seconds
            );
        }
    }
    value.to_string()
}

/// Convert days since Unix epoch to (year, month, day).
fn days_to_ymd(days: i64) -> (i64, i64, i64) {
    // Algorithm from Howard Hinnant's date algorithms
    let z = days + 719468;
    let era = if z >= 0 { z } else { z - 146096 } / 146097;
    let doe = z - era * 146097;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if m <= 2 { y + 1 } else { y };
    (y, m, d)
}

/// Extract the actual destination URL from a Google redirect URL.
///
/// Google wraps outbound links in `/url?q=<target>&...`.
pub fn extract_clean_url(raw_url: &str) -> String {
    if raw_url.starts_with("/url?q=") {
        if let Some(rest) = raw_url.strip_prefix("/url?q=") {
            let target = rest.split('&').next().unwrap_or(rest);
            return normalize_url(target);
        }
    }
    normalize_url(raw_url)
}

/// Expand shorthand proxy aliases.
///
/// Currently supports: "tb" → socks5h://127.0.0.1:9150 (Tor Browser)
pub fn expand_proxy_alias(proxy: Option<&str>) -> Option<String> {
    match proxy {
        Some("tb") => Some("socks5h://127.0.0.1:9150".to_string()),
        Some(p) => Some(p.to_string()),
        None => None,
    }
}

/// Parse a region code (e.g. "us-en") into Google query parameters.
pub fn build_region_params(region: &str) -> Vec<(String, String)> {
    let lower = region.to_lowercase();
    let parts: Vec<&str> = lower.split('-').collect();
    let (country, lang) = if parts.len() == 2 {
        (parts[0].to_string(), parts[1].to_string())
    } else {
        ("us".to_string(), "en".to_string())
    };

    vec![
        ("hl".to_string(), lang.clone()),
        ("lr".to_string(), format!("lang_{lang}")),
        ("gl".to_string(), country.to_uppercase()),
    ]
}

// ---------------------------------------------------------------------------
// Field normalization (shared by results.rs and engines)
// ---------------------------------------------------------------------------

/// Fields that use URL normalization
const URL_FIELDS: &[&str] = &["href", "url", "thumbnail", "image"];
/// Fields that use text normalization
const TEXT_FIELDS: &[&str] = &[
    "title",
    "body",
    "description",
    "snippet",
    "author",
    "publisher",
    "source",
    "content",
];
/// Fields that use date normalization
const DATE_FIELDS: &[&str] = &["date"];

/// Apply the appropriate normalizer for a given field name.
pub fn normalize_field(name: &str, value: &str) -> String {
    if value.is_empty() {
        return String::new();
    }
    if URL_FIELDS.contains(&name) {
        normalize_url(value)
    } else if DATE_FIELDS.contains(&name) {
        normalize_date(value)
    } else if TEXT_FIELDS.contains(&name) {
        normalize_text(value)
    } else {
        value.to_string()
    }
}
