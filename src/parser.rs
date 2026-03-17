// HTML parser — mirrors googer/parser.py
//
// Uses the `scraper` crate (CSS selectors) instead of lxml XPath.
// Each engine defines its own extraction logic via the `ParseConfig` trait.

use scraper::{Html, Selector};

/// Get all text content from an element, joining with spaces.
pub fn element_text(element: &scraper::ElementRef) -> String {
    element
        .text()
        .map(|t| t.trim())
        .filter(|t| !t.is_empty())
        .collect::<Vec<_>>()
        .join(" ")
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

/// Get first attribute value from the first matching child element.
pub fn first_attr(element: &scraper::ElementRef, selector: &Selector, attr: &str) -> String {
    element
        .select(selector)
        .next()
        .and_then(|el| el.value().attr(attr))
        .unwrap_or("")
        .to_string()
}

/// Get text from the first matching child element.
pub fn first_text(element: &scraper::ElementRef, selector: &Selector) -> String {
    element
        .select(selector)
        .next()
        .map(|el| element_text(&el))
        .unwrap_or_default()
}

/// Parse HTML and select items using the given CSS selector.
pub fn select_items(html: &str, items_selector: &str) -> Vec<String> {
    let document = Html::parse_document(html);
    let selector = Selector::parse(items_selector).unwrap();
    document
        .select(&selector)
        .map(|el| el.html())
        .collect()
}
