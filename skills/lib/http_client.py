"""
HTTP fetch utilities for job-search skills.

Two transport functions:
- fetch_json_curl: Uses curl (needed in the Claude sandbox where urllib is blocked
  by the firewall). Used by ats_sweep.py and any skill hitting external APIs.
- fetch_url_urllib: Uses urllib (works outside the sandbox / in local runs).
  Used by adzuna_search.py.

Both implement the same retry/exponential-backoff contract:
- 429 or 5xx: retry with backoff
- 4xx (except 429): bail immediately
- Timeout / connection error: retry
- Returns None (fetch_url_urllib) or raises RuntimeError (fetch_json_curl) on failure
"""

import json
import re
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

    urllib is blocked by the Claude sandbox firewall; curl is not.

    Retry policy:
    - 429 (rate limit) or 5xx (server error): retry with exponential backoff
    - 4xx (except 429): bail immediately — retrying won't help
    - Timeout (curl exit 28): retry
    - Other curl errors: bail immediately

    Args:
        url: URL to fetch
        timeout: Per-request timeout in seconds (default 20)
        max_retries: Total attempts (default 2)
        retry_delay_base: Base seconds for exponential backoff (default 2)

    Raises:
        RuntimeError: On unrecoverable error or exhausted retries
    """
    for attempt in range(max_retries):
        delay = retry_delay_base * (2 ** attempt)  # 2s, 4s, ...

        result = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout),
             "-H", "Accept: application/json",
             "-w", "\n%{http_code}",
             url],
            capture_output=True, text=True,
        )

        if result.returncode == 28:  # timeout
            if attempt < max_retries - 1:
                print(f"  ⚠️  Timeout — waiting {delay}s, retry {attempt+1}/{max_retries}",
                      file=sys.stderr)
                time.sleep(delay)
                continue
            raise RuntimeError("Request timed out after all retries")

        if result.returncode != 0:
            detail = result.stderr.strip() or f"curl exit {result.returncode}"
            raise RuntimeError(detail)

        body, _, status_line = result.stdout.rstrip().rpartition("\n")
        try:
            status_code = int(status_line.strip())
        except ValueError:
            body = result.stdout
            status_code = 200

        if status_code == 429:
            if attempt < max_retries - 1:
                print(f"  ⚠️  Rate limited — waiting {delay}s, retry {attempt+1}/{max_retries}",
                      file=sys.stderr)
                time.sleep(delay)
                continue
            raise RuntimeError("Rate limited after all retries")

        if status_code >= 500:
            if attempt < max_retries - 1:
                print(f"  ⚠️  Server error {status_code} — waiting {delay}s, retry {attempt+1}/{max_retries}",
                      file=sys.stderr)
                time.sleep(delay)
                continue
            raise RuntimeError(f"Server error {status_code} after all retries")

        if status_code >= 400:
            raise RuntimeError(f"HTTP {status_code}")

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
    - URLError (DNS, connection refused, network unreachable): retry
    - JSONDecodeError: bail immediately (retrying won't fix a malformed response)

    Args:
        url: URL to fetch
        timeout: Per-request timeout in seconds (default 30)
        max_retries: Total attempts (default 3)
        retry_delay_base: Base seconds for exponential backoff (default 2)

    Returns:
        Parsed JSON dict/list, or None on failure.
    """
    for attempt in range(max_retries):
        delay = retry_delay_base * (2 ** attempt)
        try:
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))

        except HTTPError as e:
            if e.code == 429:
                print(f"  ⚠️  Rate limited — waiting {delay}s (attempt {attempt+1}/{max_retries})",
                      file=sys.stderr)
                time.sleep(delay)
            elif e.code >= 500:
                print(f"  ⚠️  Server error {e.code} — waiting {delay}s, retry {attempt+1}/{max_retries}",
                      file=sys.stderr)
                time.sleep(delay)
            else:
                print(f"  ❌ HTTP {e.code}: {e.reason}", file=sys.stderr)
                return None

        except URLError as e:
            print(f"  ⚠️  Connection error — waiting {delay}s, retry {attempt+1}/{max_retries}: {e.reason}",
                  file=sys.stderr)
            time.sleep(delay)

        except json.JSONDecodeError as e:
            print(f"  ❌ JSON parse error: {e}", file=sys.stderr)
            return None

        except Exception as e:
            print(f"  ❌ Unexpected error: {e}", file=sys.stderr)
            return None

    print("  ❌ Max retries reached.", file=sys.stderr)
    return None
