/**
 * extract_csrf.js
 *
 * What it does:
 *   Reads the CSRF token from the browser's cookies. LinkedIn's Voyager API
 *   requires this token in the `csrf-token` request header to authenticate
 *   API calls made from the browser session.
 *
 * Called from:
 *   scout-link SKILL.md — Step 4: run once before the per-card fetch loop.
 *   Pass the returned token as [CSRF] in fetch_job_posting.js.
 *
 * How it works:
 *   The CSRF token is stored in the `JSESSIONID` cookie. LinkedIn sometimes
 *   wraps the value in double quotes, so the regex strips those too.
 *
 * Returns (as the last evaluated expression):
 *   String — the raw CSRF token value (e.g. "ajax:1234567890123456789")
 *   Empty string '' — if the JSESSIONID cookie is not present
 */

// Extract the JSESSIONID value from document.cookie.
// The cookie string looks like: JSESSIONID="ajax:123..." or JSESSIONID=ajax:123...
// The regex captures everything after JSESSIONID= up to the next ; or end of string,
// and the [^";]+ pattern strips any surrounding double-quote characters.
const csrfToken = document.cookie.match(/JSESSIONID="?([^";]+)/)?.[1] || '';

csrfToken;
