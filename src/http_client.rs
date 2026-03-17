// HTTP client — mirrors googer/http_client.py
//
// Wraps reqwest with retries, User-Agent rotation, and rate-limit detection.

use std::time::Duration;

use log::{debug, warn};
use reqwest::blocking::{Client, ClientBuilder};
use reqwest::header::{HeaderMap, HeaderValue, USER_AGENT};
use reqwest::Proxy;

use crate::config::{RATE_LIMIT_INDICATORS, RETRY_BACKOFF_FACTOR};
use crate::exceptions::GoogerError;
use crate::user_agents::get_gsa_user_agent;

/// A thin wrapper around a blocking reqwest response.
pub struct Response {
    pub status_code: u16,
    pub text: String,
}

impl Response {
    pub fn ok(&self) -> bool {
        (200..300).contains(&self.status_code)
    }
}

/// HTTP client with retry logic and rate-limit detection.
pub struct HttpClient {
    client: Client,
    max_retries: u32,
}

impl HttpClient {
    /// Create a new HTTP client.
    pub fn new(
        proxy: Option<&str>,
        timeout: u64,
        verify: bool,
        max_retries: u32,
    ) -> Result<Self, GoogerError> {
        let mut builder = ClientBuilder::new()
            .timeout(Duration::from_secs(timeout))
            .cookie_store(true)
            .danger_accept_invalid_certs(!verify);

        if let Some(proxy_url) = proxy {
            let p =
                Proxy::all(proxy_url).map_err(|e| GoogerError::Http(format!("Bad proxy: {e}")))?;
            builder = builder.proxy(p);
        }

        let mut headers = HeaderMap::new();
        headers.insert(
            USER_AGENT,
            HeaderValue::from_str(&get_gsa_user_agent()).unwrap(),
        );
        builder = builder.default_headers(headers);

        let client = builder
            .build()
            .map_err(|e| GoogerError::Http(format!("Failed to build HTTP client: {e}")))?;

        Ok(Self {
            client,
            max_retries,
        })
    }

    /// Perform a GET request with retries.
    pub fn get(
        &self,
        url: &str,
        params: &[(String, String)],
    ) -> Result<Response, GoogerError> {
        let mut last_err: Option<GoogerError> = None;

        for attempt in 1..=self.max_retries {
            debug!("GET {} (attempt {}/{})", url, attempt, self.max_retries);

            match self
                .client
                .get(url)
                .query(params)
                .header(USER_AGENT, get_gsa_user_agent())
                .send()
            {
                Ok(resp) => {
                    let status = resp.status().as_u16();
                    let text = resp
                        .text()
                        .unwrap_or_default();
                    let response = Response {
                        status_code: status,
                        text,
                    };

                    if is_rate_limited(&response) {
                        if attempt < self.max_retries {
                            warn!("Rate limit detected, retrying...");
                            backoff(attempt);
                            continue;
                        }
                        return Err(GoogerError::RateLimit(
                            "Google rate limit detected.".to_string(),
                        ));
                    }

                    return Ok(response);
                }
                Err(e) => {
                    if e.is_timeout() {
                        last_err = Some(GoogerError::Timeout(e.to_string()));
                    } else {
                        last_err = Some(GoogerError::Http(e.to_string()));
                    }
                    if attempt < self.max_retries {
                        backoff(attempt);
                        continue;
                    }
                }
            }
        }

        Err(last_err.unwrap_or_else(|| {
            GoogerError::Http(format!(
                "Request failed after {} retries",
                self.max_retries
            ))
        }))
    }
}

/// Check if the response indicates a rate limit / CAPTCHA.
fn is_rate_limited(response: &Response) -> bool {
    if response.status_code == 429 {
        return true;
    }
    let text_lower = response.text.to_lowercase();
    RATE_LIMIT_INDICATORS
        .iter()
        .any(|ind| text_lower.contains(ind))
}

/// Exponential backoff.
fn backoff(attempt: u32) {
    let delay = RETRY_BACKOFF_FACTOR * 2.0_f64.powi(attempt as i32 - 1);
    std::thread::sleep(Duration::from_secs_f64(delay));
}
