"""
adzuna_search.py — Adzuna API search tool for the job-search skill system.

Reads credentials from .claude/config/api-keys.md, runs searches for the
given page across all role terms × locations, deduplicates on Adzuna job ID,
applies hard excludes (category whitelist, US location/auth signals), flattens
and enriches results, and writes a processed JSON file for Claude to read and
write into raw-results-queue.json.

Usage:
    python adzuna_search.py [--output /path/to/results.json] [--page N]

Output JSON format:
    {
        "run_date": "YYYY-MM-DD",
        "page": N,
        "searches": [
            {"query": "...", "where": "...", "raw_count": N, "total_available": N}
        ],
        "results": [
            {
                "title": "...",
                "company": "...",
                "location": "...",
                "salary_min": N or null,
                "salary_max": N or null,
                "salary_display": "...",
                "redirect_url": "...",   # adzuna.ca/land/... redirect
                "created": "YYYY-MM-DDTHH:MM:SSZ",
                "search_terms": ["data analyst", "business analyst"]  # deduplicated role terms that matched this ID; written to scout-cache Search Terms column
            }
        ],
        "deduplication_removed": N,
        "hard_excluded": N,
        "hard_excluded_reasons": ["Company — Role: reason", ...]
    }
"""

import json
import os
import re
import sys
import time
import argparse
import subprocess
from datetime import date
from typing import Any, Optional
from urllib.parse import urlencode

# Add the shared library directory to the import path so we can use project_paths
# and http_client without installing them as packages.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../lib'))
from project_paths import get_project_root
from http_client import fetch_url_urllib as fetch_url

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Adzuna's Canadian job search API. {page} is replaced with the page number
# at runtime. The /ca/ path segment scopes all results to Canada.
API_BASE_TEMPLATE = "https://api.adzuna.com/v1/api/jobs/ca/search/{page}"

# How long (in seconds) to wait for a single API response before giving up.
API_TIMEOUT = 30

# Number of times to retry a failed API call before recording an error.
API_MAX_RETRIES = 3

# Base delay (in seconds) for exponential back-off between retries.
# Actual wait = API_RETRY_DELAY_BASE * 2^attempt  (e.g. 2s, 4s, 8s).
# The retry logic itself is implemented in skills/lib/http_client.py —
# fetch_url() handles back-off automatically; this constant just configures
# the base delay passed to that function.
API_RETRY_DELAY_BASE = 2

# How many job results to request per API call. Adzuna's max is 50.
RESULTS_PER_SEARCH = 50

# Role keywords for which we run separate API searches.
# We issue one search call per term × per location (see the searches list in main()).
# Adzuna does not support boolean/phrase query syntax in the `what` parameter —
# multi-word strings are tokenised as individual words (too broad). Separate
# single-concept calls per term is the only reliable approach.
SEARCH_TERMS = [
    "data analyst",
    "data engineer",
    "analytics engineer",
    "analytics manager",
    "business analyst",
    "data integration",
]

# Regex patterns matched against the truncated job description field from Adzuna.
# If any pattern matches, the job is hard-excluded before Chrome opens the URL.
# These are unambiguous signals that the role requires US work authorisation or
# is physically located in the US — not recoverable by reading the full JD.
HARD_EXCLUDE_PATTERNS = [
    # US work auth required — explicit language in description
    r"must be (?:authorized|eligible) to work in the (?:us|united states)",
    r"us (?:work )?(?:authorization|authorisation|citizenship) required",
    r"must be a u\.?s\.? (?:citizen|permanent resident)",
    # Security clearance requirements are almost exclusively US-based
    r"security clearance",
    # On-site role in a major US city — "on-site in New York" etc.
    r"\bon[-\s]?site\b.{0,60}\b(?:new york|san francisco|seattle|austin|chicago|boston|los angeles|denver)\b",
]

# Adzuna returns a "category" label for each posting. We only want roles in
# tech-adjacent categories. This whitelist filters out trades, healthcare,
# teaching, logistics, and other unrelated fields that sometimes surface
# when searching broad terms like "data analyst".
# All values are lowercase — they are compared against category_label.lower().
ALLOWED_CATEGORIES = {
    "it jobs",
    "engineering jobs",
    "consultancy jobs",
}

# Regex patterns matched against the location display string from the API.
# US state abbreviations and full state/country names are a reliable signal
# that the role is US-based (Adzuna's /ca/ endpoint occasionally surfaces
# US roles, especially for remote postings).
HARD_EXCLUDE_LOCATION_PATTERNS = [
    # US state postal abbreviations — word-boundary anchored to avoid false
    # positives like "CA" matching "CANADA" (which doesn't have a word boundary
    # after the abbreviation when it's part of "Canada").
    r"\b(?:NY|CA|TX|WA|MA|IL|CO|FL|GA|OR|MN|NC|VA|OH|PA|AZ|MI|NJ|IN|MO|TN|MD|WI|CT|NV|UT|KY|LA|AL|SC|AR|IA|MS|KS|NE|NM|ID|WV|HI|NH|ME|RI|MT|DE|SD|ND|AK|VT|WY)\b",
    # Common full US state names — also word-boundary anchored.
    r"\b(?:New York|California|Texas|Washington|Massachusetts|Illinois|Colorado|Florida|Georgia|Oregon)\b",
    # Explicit country signals
    r"\bUnited States\b",
    r"\bUSA?\b",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_credentials(project_root: str) -> tuple[str, str]:
    """Read ADZUNA_APP_ID and ADZUNA_API_KEY from .claude/config/api-keys.md.

    The api-keys.md file uses a Markdown list format for each credential.
    The Adzuna section is expected to look like:

        ## Adzuna
        - **app_id:** abc123
        - **app_key:** def456

    The regex patterns below match the bold-label Markdown format and capture
    the value (the non-whitespace token after the colon and space).

    Args:
        project_root: Absolute path to the root of the job-search project.

    Returns:
        A (app_id, app_key) tuple of strings.

    Raises:
        FileNotFoundError: If api-keys.md does not exist.
        ValueError: If the expected keys are not found in the file.
    """
    keys_path = os.path.join(project_root, ".claude", "config", "api-keys.md")
    if not os.path.exists(keys_path):
        raise FileNotFoundError(f"api-keys.md not found at {keys_path}")

    with open(keys_path) as f:
        content = f.read()

    # Each credential is written as a bold Markdown label followed by its value.
    # Pattern: **app_id:** <non-whitespace-value>
    # \S+ captures everything up to the next whitespace (newline, space, etc.).
    app_id_match  = re.search(r"\*\*app_id:\*\*\s*(\S+)", content)
    app_key_match = re.search(r"\*\*app_key:\*\*\s*(\S+)", content)

    if not app_id_match or not app_key_match:
        raise ValueError(
            "Could not find app_id or app_key in api-keys.md under ## Adzuna. "
            "Expected format:\n- **app_id:** <value>\n- **app_key:** <value>"
        )

    # group(1) returns the first capture group — the value after the label.
    return app_id_match.group(1), app_key_match.group(1)


def format_salary(job: dict) -> str:
    """Format a salary range from a job dict into a human-readable string.

    Adzuna provides separate salary_min and salary_max fields. This function
    builds a display string covering four cases: both bounds present, only a
    lower bound, only an upper bound, or no salary data at all.

    Args:
        job: A dict containing optional "salary_min" and "salary_max" keys.
             Values are expected to be numeric (int or float) or None/missing.

    Returns:
        A formatted string such as "$80,000–$100,000 CAD", "From $60,000 CAD",
        "Up to $120,000 CAD", or "Not posted" when no salary data is available.
    """
    lo = job.get("salary_min")
    hi = job.get("salary_max")

    if lo and hi:
        # Both bounds are present — show a range with an en-dash separator.
        return f"${lo:,.0f}–${hi:,.0f} CAD"
    if lo:
        # Only a minimum is known.
        return f"From ${lo:,.0f} CAD"
    if hi:
        # Only a maximum is known.
        return f"Up to ${hi:,.0f} CAD"

    # No salary data in the posting.
    return "Not posted"


def dedup_key(job: dict) -> str:
    """Build a deduplication key for a raw Adzuna job result.

    The same job often appears multiple times in our results because we run
    one search per SEARCH_TERM × per location, and a single posting can match
    several terms and both locations. We need a stable key to detect these
    duplicates before processing.

    Strategy — prefer Adzuna's numeric job ID:
        Adzuna embeds the job ID in the redirect_url path segment
        (/land/ad/<id> or /details/<id>). Extracting it gives a compact,
        collision-free key that correctly identifies the same posting even if
        the title or company name was inconsistently formatted across results.

    Fallback — company + title:
        If the redirect_url is malformed or missing the ID segment (rare in
        practice), we fall back to a normalised "company||title" string.
        This can theoretically collapse two distinct roles with the same title
        at the same company (e.g. two "Senior Data Engineer" openings on
        different teams), but this edge case is unlikely and acceptable.

    Args:
        job: A raw Adzuna API result dict.

    Returns:
        A string key — either "id:<numeric_id>" or "company||title".
    """
    redirect_url = job.get("redirect_url") or ""

    # Try to extract the numeric Adzuna job ID from the redirect URL.
    # Two known URL patterns:
    #   /land/ad/<id>   — standard redirect through the Adzuna landing page
    #   /details/<id>   — direct detail page (used in some API responses)
    m = re.search(r"/(?:land/ad|details)/(\d+)", redirect_url)
    if m:
        # Prefix with "id:" to make the key type explicit and avoid any
        # accidental collision with the company||title fallback keys.
        return f"id:{m.group(1)}"

    # Fallback: normalise company and title to lower-case, collapse internal
    # whitespace, and join with a double-pipe separator that is unlikely to
    # appear in either field naturally.
    company = (job.get("company", {}).get("display_name") or "unknown").lower().strip()
    title   = (job.get("title") or "unknown").lower().strip()
    company = re.sub(r"\s+", " ", company)
    title   = re.sub(r"\s+", " ", title)
    return f"{company}||{title}"


def is_hard_excluded(job: dict) -> Optional[str]:
    """Return a reason string if the job should be dropped before Chrome opens it.

    Hard excludes are checks that can be made reliably from the truncated
    Adzuna API fields alone (location display name + short description snippet).
    They catch unambiguous disqualifiers — US-only roles and irrelevant job
    categories — so we avoid spending Chrome sessions on clear non-starters.

    Checks are applied in order:
        1. Category whitelist — the job must belong to an approved category
           (IT, engineering, or consultancy). All other categories are excluded.
        2. Location field — US state abbreviations and country names signal a
           US-based role even when the description looks relevant.
        3. Description field — explicit US work authorisation language or
           security clearance requirements confirm a US role.

    Args:
        job: A raw Adzuna API result dict.

    Returns:
        A human-readable reason string if the job should be excluded, or None
        if the job passes all checks and should proceed to Chrome scoring.
    """
    # Adzuna may return the location as either a dict with a "display_name" key
    # or a plain string depending on API version — handle both defensively.
    loc_raw  = job.get("location", "")
    location = (loc_raw.get("display_name") if isinstance(loc_raw, dict) else loc_raw) or ""

    description = job.get("description") or ""
    title       = job.get("title") or ""

    # Same dict-or-string handling for the company field.
    company_raw = job.get("company", "")
    company     = (company_raw.get("display_name") if isinstance(company_raw, dict) else company_raw) or ""

    # --- Check 1: Category whitelist ---
    # Adzuna assigns each posting to exactly one category. We only want roles
    # in the ALLOWED_CATEGORIES set. Any other category (e.g. "healthcare jobs",
    # "teaching jobs", "trade jobs") is irrelevant and excluded here, before any
    # further checks. This is a whitelist approach: unknown categories are excluded
    # by default, which is safer than a blacklist that requires ongoing maintenance.
    category_raw   = job.get("category", {})
    category_label = (category_raw.get("label") if isinstance(category_raw, dict) else category_raw) or ""
    if category_label.lower() not in ALLOWED_CATEGORIES:
        return f"Category not in whitelist: {category_label!r}"

    # --- Check 2: US location signal ---
    # Match US state abbreviations and country names in the location display string.
    for pattern in HARD_EXCLUDE_LOCATION_PATTERNS:
        if re.search(pattern, location, re.IGNORECASE):
            return f"US location: {location}"

    # --- Check 3: US work auth / clearance in description ---
    # The Adzuna API returns only a short snippet (~300 chars) of the description.
    # These patterns are specific enough that a partial match is reliable.
    for pattern in HARD_EXCLUDE_PATTERNS:
        if re.search(pattern, description, re.IGNORECASE):
            return f"Description signal: {pattern[:40]}..."

    # All checks passed — job should proceed to Chrome scoring.
    return None


def parse_job(job: dict) -> dict:
    """Parse and flatten a raw Adzuna API job result into a clean output dict.

    The raw Adzuna response contains nested structures (e.g. company.display_name,
    location.display_name) and fields we don't need downstream. This function
    extracts only the fields used by the scout skill and flattens any nested
    dicts into plain strings.

    Note: the "search_terms" field is intentionally left empty here. The caller
    (main()) fills it in after deduplication, once it knows all the role-term
    searches that returned this job ID. See the deduplication block in main()
    for details.

    Args:
        job: A raw Adzuna API result dict (one element from the "results" array).

    Returns:
        A flat dict with only the fields needed for downstream processing.
    """
    return {
        "id":             job.get("id"),
        "title":          job.get("title", ""),
        "company":        job.get("company", {}).get("display_name", ""),
        "location":       job.get("location", {}).get("display_name", ""),
        "salary_min":     job.get("salary_min"),
        "salary_max":     job.get("salary_max"),
        "salary_display": format_salary(job),
        "redirect_url":   job.get("redirect_url", ""),
        "created":        job.get("created", ""),
        # Populated by main() after deduplication overlap analysis — see caller.
        "search_terms":   [],
    }


# ---------------------------------------------------------------------------
# Main search logic
# ---------------------------------------------------------------------------

def run_search(
    app_id: str,
    app_key: str,
    what: str,
    where: Optional[str],
    label: str,
    page: int,
) -> tuple[list[dict], int]:
    """Run one Adzuna search and return (raw API result list, total available count).

    This function constructs the API URL, calls the Adzuna endpoint, and returns
    the raw result list exactly as the API returned it — no filtering or
    transformation is done here. That keeps the caller in control of dedup and
    exclude logic.

    Args:
        app_id:  Adzuna application ID credential.
        app_key: Adzuna API key credential.
        what:    The role search term (e.g. "data analyst"). Maps to the Adzuna
                 `what` query parameter.
        where:   City/region string to scope results geographically (e.g. "Calgary").
                 Pass None to omit the `where` parameter entirely, which produces a
                 national Canada search. The /ca/ URL path already limits results to
                 Canada, so omitting `where` is a valid "search all of Canada" query
                 rather than accidentally widening to other countries.
        label:   A short identifier string for logging (e.g. "calgary", "canada_remote").
                 Not sent to the API; used only in stderr progress messages.
        page:    Which page of results to fetch. Page 1 returns the most recent
                 RESULTS_PER_SEARCH postings; page 2 returns the next batch, etc.

    Returns:
        A tuple of (results, total_available) where:
            results         — list of raw job dicts from the API "results" array
            total_available — total number of results Adzuna reports for this query
                              (may be much larger than RESULTS_PER_SEARCH)
    """
    # Build the query parameter dict. Required params: app_id, app_key.
    # Optional but important: results_per_page, what, max_days_old, sort_by.
    params: dict[str, Any] = {
        "app_id":           app_id,
        "app_key":          app_key,
        "results_per_page": RESULTS_PER_SEARCH,
        "what":             what,
        # Only surface postings from the last two weeks — older roles are unlikely
        # to still be accepting applications.
        "max_days_old":     14,
        "content-type":     "application/json",
        # Sort by date descending so the newest postings appear on page 1.
        "sort_by":          "date",
    }

    # Only include the `where` parameter if a location was specified.
    # Omitting it entirely (rather than passing an empty string) triggers
    # Adzuna's national search behaviour.
    if where:
        params["where"] = where

    url = f"{API_BASE_TEMPLATE.format(page=page)}?{urlencode(params)}"

    print(f"  🔍 Search (page {page}): {what!r} in {where!r}...", file=sys.stderr)

    # fetch_url (imported from http_client) handles retries and back-off.
    # It returns a parsed dict on success, or None if all retries fail.
    data = fetch_url(url)

    if data is None:
        print(f"  ❌ Search failed for {what!r} in {where!r}", file=sys.stderr)
        return [], 0

    results = data.get("results", [])
    # "count" is Adzuna's total match count for this query across all pages,
    # not just the current page. Useful for estimating how many more pages exist.
    total = data.get("count", len(results))
    print(f"     → {len(results)} results (of {total} total matches)", file=sys.stderr)
    return results, total


def main():
    parser = argparse.ArgumentParser(description="Adzuna job search for job-search skill")
    parser.add_argument("--output", default="/tmp/adzuna_results.json",
                        help="Path to write JSON output (default: /tmp/adzuna_results.json)")
    parser.add_argument("--page", type=int, default=1,
                        help="Adzuna results page to fetch (default: 1)")
    args = parser.parse_args()

    project_root = get_project_root()
    app_id, app_key = read_credentials(project_root)

    print(f"🔎 Starting Adzuna search (page {args.page})...", file=sys.stderr)

    # Accumulate raw API results as (raw_job_dict, source_label) tuples.
    # A tuple is used because the two values (job dict + source label) are
    # always paired together — the tuple makes that pairing explicit and
    # immutable, preventing accidental misalignment when iterating later.
    # The source_label encodes "search_term|location_label" so we can later
    # reconstruct which terms and locations matched each job ID.
    all_raw: list[tuple[dict, str]] = []
    search_log = []

    # We run two location scopes for every search term:
    #   ("Calgary", "calgary")      — where=Calgary passed to API; city-scoped results.
    #   (None, "canada_remote")     — where param omitted; national Canada search.
    #                                  The /ca/ URL path already scopes to Canada, so
    #                                  this captures remote roles listed without a city.
    # This covers both local Calgary positions and remote roles posted nationally.
    searches: list[tuple[Optional[str], str]] = [
        ("Calgary", "calgary"),
        (None, "canada_remote"),
    ]

    for term in SEARCH_TERMS:
        for where, label in searches:
            raw, total_available = run_search(app_id, app_key, term, where, label, args.page)
            search_log.append({
                "query":           term,
                # Use a human-readable fallback label in the log when where is None.
                "where":           where or "canada (national)",
                "raw_count":       len(raw),
                "total_available": total_available,
            })
            # Tag each raw result with a "term|location" label. The pipe separator
            # lets us split term from location later (search_terms in parse_job
            # should contain only the term, not the location string).
            source_label = f"{term}|{label}"
            all_raw.extend((job, source_label) for job in raw)
            # Brief pause between consecutive API calls to be a polite client
            # and avoid triggering rate limiting.
            time.sleep(0.5)

    print(f"\n  📦 Total raw results before dedup: {len(all_raw)}", file=sys.stderr)

    # ---------------------------------------------------------------------------
    # Deduplication
    # ---------------------------------------------------------------------------
    # The same posting frequently appears under multiple search terms and/or
    # both location scopes. We deduplicate on the Adzuna job ID (extracted from
    # redirect_url by dedup_key()).
    #
    # Two parallel dicts track each unique key:
    #   seen      — maps key → list of all source_labels that returned it.
    #               Accumulating all labels (not just the first) lets us record
    #               every role term that matched this posting in search_terms.
    #   seen_raw  — maps key → the first raw job dict we received for this key.
    #               We only need one copy of the raw data to call parse_job().
    seen:     dict[str, list[str]] = {}
    seen_raw: dict[str, dict]      = {}
    dedup_removed = 0

    for raw_job, source_label in all_raw:
        key = dedup_key(raw_job)
        if key in seen:
            # Duplicate — record the extra source label and count it as removed.
            seen[key].append(source_label)
            dedup_removed += 1
        else:
            # First time we've seen this key — store it.
            seen[key]     = [source_label]
            seen_raw[key] = raw_job

    print(f"  🗂️  After deduplication: {len(seen)} ({dedup_removed} removed)", file=sys.stderr)

    # ---------------------------------------------------------------------------
    # Hard excludes and final parse
    # ---------------------------------------------------------------------------
    # Hard excludes must run on the raw job dicts (before parse_job) because
    # parse_job drops the "category" field — which is the primary exclude signal.
    # We check each unique job against is_hard_excluded() first, then call
    # parse_job() only on those that pass.
    clean_jobs:    list[dict] = []
    hard_excluded: list[str]  = []

    for key, source_labels in seen.items():
        raw_job = seen_raw[key]
        reason  = is_hard_excluded(raw_job)

        if reason:
            # Build a human-readable log entry for the excluded role.
            company = (raw_job.get("company", {}).get("display_name") or "")
            title   = raw_job.get("title") or ""
            hard_excluded.append(f"{company} — {title}: {reason}")
        else:
            job = parse_job(raw_job)
            # Three nested operations to build the search_terms list:
            #   1. label.split("|")[0]  — extract the term before the pipe
            #                             (each label is "term|location_label")
            #   2. set(...)             — deduplicate: the same term can appear
            #                             via multiple location scopes
            #   3. sorted(...)          — alphabetise for stable output ordering
            job["search_terms"] = sorted(set(label.split("|")[0] for label in source_labels))
            clean_jobs.append(job)

    print(f"  🚫 Hard excluded: {len(hard_excluded)}", file=sys.stderr)
    print(f"  ✅ Proceeding to queue: {len(clean_jobs)}", file=sys.stderr)

    output = {
        "run_date":              date.today().isoformat(),
        "page":                  args.page,
        "searches":              search_log,
        "results":               clean_jobs,
        "deduplication_removed": dedup_removed,
        "hard_excluded":         len(hard_excluded),
        "hard_excluded_reasons": hard_excluded,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  💾 Results written to {args.output}", file=sys.stderr)
    print(f"  Summary: {len(clean_jobs)} candidates added to queue", file=sys.stderr)

    # Print a compact machine-readable JSON summary to stdout.
    # SKILL.md captures this line (not the stderr progress output) to learn
    # how many candidates were found and where the full results file lives.
    print(json.dumps({
        "candidate_count": len(clean_jobs),
        "output_path":     args.output,
        "hard_excluded":   len(hard_excluded),
        "dedup_removed":   dedup_removed,
        "page":            args.page,
    }))


# When this file is run directly (e.g. `python adzuna_search.py`), Python sets
# __name__ to "__main__" so main() runs. When it's imported by another script
# (e.g. `import adzuna_search`), __name__ is the module name ("adzuna_search")
# so main() does NOT run automatically — only the definitions are loaded.
if __name__ == "__main__":
    main()
