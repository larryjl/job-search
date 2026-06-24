"""
HTTP fetch utilities for job-search skills.

Two transport functions are provided, each targeting a different runtime
environment:

fetch_json_curl
    Uses the system `curl` binary instead of Python's urllib. This is
    necessary inside the Claude sandbox, where the sandbox firewall blocks
    outbound connections made by Python's urllib/http.client stack but
    permits curl. Used by ats_sweep.py and any skill that hits external APIs
    from within the sandbox.

fetch_url_urllib
    Uses Python's built-in urllib. Works in local/non-sandbox runs where the
    firewall restriction does not apply. Used by adzuna_search.py.

Both functions implement the same retry / exponential-backoff contract:
    - 429 (rate-limited) or 5xx (server error): retry with backoff
    - 4xx other than 429: bail immediately (retrying will not change the outcome)
    - Timeout or connection error: retry
    - Returns None (fetch_url_urllib) or raises RuntimeError (fetch_json_curl)
      when all retries are exhausted or an unrecoverable error occurs
"""

import json
import subprocess
import sys
import time
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ---------------------------------------------------------------------------
# curl-based (sandbox-safe)
# ---------------------------------------------------------------------------

def fetch_json_curl(
    url: str,
    timeout: int = 20,
    max_retries: int = 2,
    retry_delay_base: int = 2,
) -> Optional[dict | list]:
    """
    GET a URL via curl and return parsed JSON, with retry and exponential backoff.

    curl is used instead of urllib because the Claude sandbox firewall permits
    outbound curl subprocess calls but blocks Python's urllib/http.client.

    Retry policy:
        - 429 (rate limit) or 5xx (server error): retry with exponential backoff
        - 4xx (except 429): bail immediately — the server has rejected the request
          and retrying the same request will produce the same rejection
        - Timeout (curl exit code 28): retry — transient network condition
        - Other non-zero curl exit codes: bail immediately (e.g. DNS failure)

    Args:
        url: URL to fetch
        timeout: Per-request timeout in seconds passed to curl --max-time (default 20)
        max_retries: Total number of attempts before giving up (default 2)
        retry_delay_base: Base seconds for exponential backoff (default 2)

    Returns:
        Parsed JSON as a dict or list.

    Raises:
        RuntimeError: On unrecoverable error or when all retries are exhausted.
    """
    for attempt in range(max_retries):
        # Exponential backoff: 2s on first retry, 4s on second, 8s on third, etc.
        # Calculated here (before the request) so it's available to any branch
        # that decides to sleep and continue.
        delay = retry_delay_base * (2 ** attempt)  # e.g. 2, 4, 8 seconds

        result = subprocess.run(
            [
                "curl",
                "-s",                        # silent mode: suppress progress meter
                "--max-time", str(timeout),  # hard timeout per attempt
                "-H", "Accept: application/json",
                # -w appends a format string to stdout AFTER the response body.
                # "\n%{http_code}" writes the HTTP status code on its own line,
                # which we parse below to detect 4xx/5xx without needing -I (HEAD).
                "-w", "\n%{http_code}",
                url,
            ],
            capture_output=True,
            text=True,
        )

        # curl exit code 28 = CURLE_OPERATION_TIMEDOUT — the --max-time limit
        # was reached. This is a transient condition; worth retrying.
        if result.returncode == 28:
            if attempt < max_retries - 1:
                print(
                    f"  ⚠️  Timeout — waiting {delay}s, retry {attempt+1}/{max_retries}",
                    file=sys.stderr,
                )
                time.sleep(delay)
                continue
            raise RuntimeError("Request timed out after all retries")

        # Any other non-zero exit code (e.g. 6 = DNS failure, 7 = connection
        # refused) is treated as unrecoverable — retrying the same URL won't help.
        if result.returncode != 0:
            detail = result.stderr.strip() or f"curl exit {result.returncode}"
            raise RuntimeError(detail)

        # Split response: everything before the last newline is the body;
        # the last line is the HTTP status code appended by -w "\n%{http_code}".
        body, _, status_line = result.stdout.rstrip().rpartition("\n")
        try:
            status_code = int(status_line.strip())
        except ValueError:
            # Parsing failed — assume 200 and treat the whole output as the body.
            # This handles edge cases where the server response has no body and
            # only the status code appears in stdout.
            body = result.stdout
            status_code = 200

        # 429 Too Many Requests — honour the rate limit with a backoff sleep.
        if status_code == 429:
            if attempt < max_retries - 1:
                print(
                    f"  ⚠️  Rate limited — waiting {delay}s, retry {attempt+1}/{max_retries}",
                    file=sys.stderr,
                )
                time.sleep(delay)
                continue
            raise RuntimeError("Rate limited after all retries")

        # 5xx Server Error — transient; retry with backoff.
        if status_code >= 500:
            if attempt < max_retries - 1:
                print(
                    f"  ⚠️  Server error {status_code} — waiting {delay}s, retry {attempt+1}/{max_retries}",
                    file=sys.stderr,
                )
                time.sleep(delay)
                continue
            raise RuntimeError(f"Server error {status_code} after all retries")

        # 4xx Client Error (other than 429) — the request itself is bad (wrong
        # URL, auth error, resource not found). Retrying won't change anything.
        if status_code >= 400:
            raise RuntimeError(f"HTTP {status_code}")

        # Success — parse and return the JSON body.
        try:
            return json.loads(body)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"JSON parse error: {e}")

    raise RuntimeError("Max retries reached")


# ---------------------------------------------------------------------------
# urllib-based (local / non-sandbox)
# ---------------------------------------------------------------------------

def fetch_url_urllib(
    url: str,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay_base: int = 2,
) -> Optional[dict[str, Any]]:
    """
    GET a URL via urllib and return parsed JSON, with retry and exponential backoff.

    Retry policy:
        - 429 or 5xx: retry with exponential backoff
        - Other 4xx: bail immediately
        - URLError (DNS failure, connection refused, network unreachable): retry —
          these are often transient infrastructure blips
        - JSONDecodeError: bail immediately — retrying the same URL will return
          the same malformed body; there is nothing to gain from another attempt

    Args:
        url: URL to fetch
        timeout: Per-request timeout in seconds (default 30)
        max_retries: Total number of attempts before giving up (default 3)
        retry_delay_base: Base seconds for exponential backoff (default 2)

    Returns:
        Parsed JSON as a dict or list, or None on failure.
    """
    for attempt in range(max_retries):
        # Exponential backoff delay, computed upfront for any branch that needs it
        delay = retry_delay_base * (2 ** attempt)
        try:
            # urllib.request.Request wraps the URL so we can attach headers.
            # urlopen() will raise HTTPError for 4xx/5xx responses rather than
            # returning a response object, which lets us handle them in the
            # except block below.
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=timeout) as resp:
                # resp.read() returns bytes; decode to str before JSON parsing.
                return json.loads(resp.read().decode("utf-8"))

        except HTTPError as e:
            # 429: rate-limited — sleep and retry
            if e.code == 429:
                print(
                    f"  ⚠️  Rate limited — waiting {delay}s (attempt {attempt+1}/{max_retries})",
                    file=sys.stderr,
                )
                time.sleep(delay)
            # 5xx: server-side error — transient, worth retrying
            elif e.code >= 500:
                print(
                    f"  ⚠️  Server error {e.code} — waiting {delay}s, retry {attempt+1}/{max_retries}",
                    file=sys.stderr,
                )
                time.sleep(delay)
            else:
                # 4xx other than 429: client-side error (bad URL, auth, not found)
                # Retrying will not change the outcome.
                print(f"  ❌ HTTP {e.code}: {e.reason}", file=sys.stderr)
                return None

        except URLError as e:
            # URLError covers DNS failures, connection refused, and network errors.
            # These can be transient (e.g. brief DNS hiccup), so we retry.
            print(
                f"  ⚠️  Connection error — waiting {delay}s, retry {attempt+1}/{max_retries}: {e.reason}",
                file=sys.stderr,
            )
            time.sleep(delay)

        except json.JSONDecodeError as e:
            # The response was received but was not valid JSON. Retrying the same
            # URL will return the same broken body, so bail immediately.
            print(f"  ❌ JSON parse error: {e}", file=sys.stderr)
            return None

        except Exception as e:
            # Catch-all for unexpected errors (e.g. SSL certificate issues).
            # Log and bail — we don't know if retrying would help.
            print(f"  ❌ Unexpected error: {e}", file=sys.stderr)
            return None

    print("  ❌ Max retries reached.", file=sys.stderr)
    return None
