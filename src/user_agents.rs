// User-Agent management — mirrors googer/user_agents.py
//
// Provides rotating GSA (Google Search App) and Chrome desktop User-Agent
// strings to avoid bot detection.

use rand::seq::SliceRandom;
use rand::Rng;
use std::collections::HashMap;
use std::sync::LazyLock;

// iOS version → list of observed GSA versions
static IOS_GSA_MAP: LazyLock<HashMap<&str, Vec<&str>>> = LazyLock::new(|| {
    HashMap::from([
        ("17_4", vec!["315.0.630091404", "317.0.634488990"]),
        ("17_6_1", vec!["411.0.879111500"]),
        ("18_1_1", vec!["411.0.879111500"]),
        ("18_2", vec!["173.0.391310503"]),
        (
            "18_6_2",
            vec![
                "397.0.836500703",
                "399.2.845414227",
                "410.0.875971614",
                "411.0.879111500",
            ],
        ),
        ("18_7_2", vec!["411.0.879111500"]),
        ("18_7_5", vec!["411.0.879111500"]),
        ("18_7_6", vec!["411.0.879111500"]),
        ("26_1_0", vec!["411.0.879111500"]),
        (
            "26_2_0",
            vec![
                "396.0.833910942",
                "409.0.872648028",
                "411.0.879111500",
            ],
        ),
        ("26_2_1", vec!["409.0.872648028", "411.0.879111500"]),
        (
            "26_3_0",
            vec![
                "406.0.862495628",
                "410.0.875971614",
                "411.0.879111500",
            ],
        ),
        (
            "26_3_1",
            vec![
                "370.0.762543316",
                "404.0.856692123",
                "408.0.868297084",
                "410.0.875971614",
                "411.0.879111500",
            ],
        ),
        ("26_4_0", vec!["411.0.879111500"]),
    ])
});

static CHROME_DESKTOP_UAS: &[&str] = &[
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
];

/// Return a random GSA (Google Search App) User-Agent for iOS.
pub fn get_gsa_user_agent() -> String {
    let mut rng = rand::thread_rng();
    let keys: Vec<&&str> = IOS_GSA_MAP.keys().collect();
    let ios_ver = keys.choose(&mut rng).unwrap();
    let versions = &IOS_GSA_MAP[**ios_ver];
    let gsa_ver = versions.choose(&mut rng).unwrap();
    format!(
        "Mozilla/5.0 (iPhone; CPU iPhone OS {} like Mac OS X) \
         AppleWebKit/605.1.15 (KHTML, like Gecko) \
         GSA/{} Mobile/15E148 Safari/604.1",
        ios_ver, gsa_ver
    )
}

/// Return a random Chrome desktop User-Agent.
pub fn get_chrome_user_agent() -> String {
    let mut rng = rand::thread_rng();
    CHROME_DESKTOP_UAS
        .choose(&mut rng)
        .unwrap()
        .to_string()
}

/// Return a random User-Agent, weighted towards GSA strings (70%).
pub fn get_random_user_agent() -> String {
    let mut rng = rand::thread_rng();
    if rng.gen::<f64>() < 0.7 {
        get_gsa_user_agent()
    } else {
        get_chrome_user_agent()
    }
}
