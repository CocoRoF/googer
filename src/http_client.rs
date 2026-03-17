// HTTP client — powered by ureq (synchronous, no tokio dependency)
//
// Wraps ureq with retries, User-Agent rotation, and rate-limit detection.

use std::time::Duration;

use log::{debug, warn};
use ureq::Agent;

use crate::config::{RATE_LIMIT_INDICATORS, RETRY_BACKOFF_FACTOR};
use crate::exceptions::GoogerError;
use crate::user_agents::get_gsa_user_agent;

/// A thin wrapper around an HTTP response.
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
    agent: Agent,
    max_retries: u32,
}

impl HttpClient {
    /// Create a new HTTP client.
    pub fn new(
        proxy: Option<&str>,
        timeout: u64,
        _verify: bool,
        max_retries: u32,
    ) -> Result<Self, GoogerError> {
        let mut builder = ureq::AgentBuilder::new()
            .timeout_read(Duration::from_secs(timeout))
            .timeout_write(Duration::from_secs(timeout))
            .timeout_connect(Duration::from_secs(timeout.min(15)))
            .max_idle_connections(5)
            .redirects(10);

        if let Some(proxy_url) = proxy {
            let proxy = ureq::Proxy::new(proxy_url)
                .map_err(|e| GoogerError::Http(format!("Bad proxy: {e}")))?;
            builder = builder.proxy(proxy);
        }

        let agent = builder.build();
        Ok(Self { agent, max_retries })
    }

    /// Perform a GET request with retries.
    pub fn get(&self, url: &str, params: &[(String, String)]) -> Result<Response, GoogerError> {
        let mut last_err: Option<GoogerError> = None;

        // Build the full URL with query parameters
        let full_url = if params.is_empty() {
            url.to_string()
        } else {
            let query_string: String = params
                .iter()
                .map(|(k, v)| format!("{}={}", urlencoding::encode(k), urlencoding::encode(v)))
                .collect::<Vec<_>>()
                .join("&");
            format!("{}?{}", url, query_string)
        };

        for attempt in 1..=self.max_retries {
            debug!(
                "GET {} (attempt {}/{})",
                full_url, attempt, self.max_retries
            );

            let ua = get_gsa_user_agent();
            let result = self
                .agent
                .get(&full_url)
                .set("User-Agent", &ua)
                .set(
                    "Accept",
                    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                )
                .set("Accept-Language", "en-US,en;q=0.5")
                .call();

            match result {
                Ok(resp) => {
                    let status = resp.status();
                    let text = resp.into_string().unwrap_or_default();
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
                Err(ureq::Error::Status(code, resp)) => {
                    let text = resp.into_string().unwrap_or_default();
                    let response = Response {
                        status_code: code,
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
                Err(ureq::Error::Transport(e)) => {
                    let err_str = e.to_string();
                    if err_str.contains("timeout") || err_str.contains("Timeout") {
                        last_err = Some(GoogerError::Timeout(err_str));
                    } else {
                        last_err = Some(GoogerError::Http(err_str));
                    }
                    if attempt < self.max_retries {
                        backoff(attempt);
                        continue;
                    }
                }
            }
        }

        Err(last_err.unwrap_or_else(|| {
            GoogerError::Http(format!("Request failed after {} retries", self.max_retries))
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
