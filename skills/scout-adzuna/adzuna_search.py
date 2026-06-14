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
                "description": "...",   # truncated ~500 chars from API
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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../lib'))
from project_paths import get_project_root
from http_client import fetch_url_urllib as fetch_url

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_BASE_TEMPLATE = "https://api.adzuna.com/v1/api/jobs/ca/search/{page}"
API_TIMEOUT = 30
API_MAX_RETRIES = 3
API_RETRY_DELAY_BASE = 2  # seconds; actual delay = base * 2^attempt (exponential backoff)
RESULTS_PER_SEARCH = 50

# Role keywords — one API call per term per location.
# Adzuna does not document boolean/phrase syntax for the `what` parameter;
# space-separated words are tokenised individually (too broad for multi-word titles).
# Separate calls per term is the only reliable approach.
SEARCH_TERMS = [
    "data analyst",
    "data engineer",
    "analytics engineer",
    "analytics manager",
    "business analyst",
    "data integration",
]

# Hard-exclude location/auth patterns (applied before Chrome — these are
# unambiguous signals in the truncated description or location field)
HARD_EXCLUDE_PATTERNS = [
    # US work auth required
    r"must be (?:authorized|eligible) to work in the (?:us|united states)",
    r"us (?:work )?(?:authorization|authorisation|citizenship) required",
    r"must be a u\.?s\.? (?:citizen|permanent resident)",
    r"security clearance",
    # Explicit US-only on-site
    r"\bon[-\s]?site\b.{0,60}\b(?:new york|san francisco|seattle|austin|chicago|boston|los angeles|denver)\b",
]

ALLOWED_CATEGORIES = {
    "it jobs",
    "engineering jobs",
    "consultancy jobs",
}

HARD_EXCLUDE_LOCATION_PATTERNS = [
    # US states (location field)
    r"\b(?:NY|CA|TX|WA|MA|IL|CO|FL|GA|OR|MN|NC|VA|OH|PA|AZ|MI|NJ|IN|MO|TN|MD|WI|CT|NV|UT|KY|LA|AL|SC|AR|IA|MS|KS|NE|NM|ID|WV|HI|NH|ME|RI|MT|DE|SD|ND|AK|VT|WY)\b",
    r"\b(?:New York|California|Texas|Washington|Massachusetts|Illinois|Colorado|Florida|Georgia|Oregon)\b",
    r"\bUnited States\b",
    r"\bUSA?\b",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_credentials(project_root: str) -> tuple[str, str]:
    """Read ADZUNA_APP_ID and ADZUNA_API_KEY from .claude/config/api-keys.md."""
    keys_path = os.path.join(project_root, ".claude", "config", "api-keys.md")
    if not os.path.exists(keys_path):
        raise FileNotFoundError(f"api-keys.md not found at {keys_path}")

    with open(keys_path) as f:
        content = f.read()

    app_id_match = re.search(r"\*\*app_id:\*\*\s*(\S+)", content)
    app_key_match = re.search(r"\*\*app_key:\*\*\s*(\S+)", content)

    if not app_id_match or not app_key_match:
        raise ValueError(
            "Could not find app_id or app_key in api-keys.md under ## Adzuna. "
            "Expected format:\n- **app_id:** <value>\n- **app_key:** <value>"
        )

    return app_id_match.group(1), app_key_match.group(1)



def format_salary(job: dict) -> str:
    lo = job.get("salary_min")
    hi = job.get("salary_max")
    if lo and hi:
        return f"${lo:,.0f}–${hi:,.0f} CAD"
    if lo:
        return f"From ${lo:,.0f} CAD"
    if hi:
        return f"Up to ${hi:,.0f} CAD"
    return "Not posted"


def dedup_key(job: dict) -> str:
    """
    Extract Adzuna job ID from redirect_url for deduplication.
    Falls back to company+title if ID cannot be parsed (should not happen in practice).
    Using job ID avoids collapsing distinct postings that share a title at the same company
    (e.g. two 'Senior Data Engineer' roles on different teams).
    """
    redirect_url = job.get("redirect_url") or ""
    m = re.search(r"/(?:land/ad|details)/(\d+)", redirect_url)
    if m:
        return f"id:{m.group(1)}"
    # Fallback: company+title (covers malformed or missing redirect_url)
    company = (job.get("company", {}).get("display_name") or "unknown").lower().strip()
    title = (job.get("title") or "unknown").lower().strip()
    company = re.sub(r"\s+", " ", company)
    title = re.sub(r"\s+", " ", title)
    return f"{company}||{title}"


def is_hard_excluded(job: dict) -> Optional[str]:
    """
    Returns a reason string if the job should be hard-excluded before Chrome,
    or None if it should proceed.

    Checks:
    - Location field for US state/country signals
    - Truncated description for explicit US work auth language
    """
    loc_raw = job.get("location", "")
    location = (loc_raw.get("display_name") if isinstance(loc_raw, dict) else loc_raw) or ""
    description = job.get("description") or ""
    title = job.get("title") or ""
    company_raw = job.get("company", "")
    company = (company_raw.get("display_name") if isinstance(company_raw, dict) else company_raw) or ""

    # Category whitelist — skip anything not in an allowed category
    category_raw = job.get("category", {})
    category_label = (category_raw.get("label") if isinstance(category_raw, dict) else category_raw) or ""
    if category_label.lower() not in ALLOWED_CATEGORIES:
        return f"Category not in whitelist: {category_label!r}"

    # Location-based exclude
    for pattern in HARD_EXCLUDE_LOCATION_PATTERNS:
        if re.search(pattern, location, re.IGNORECASE):
            return f"US location: {location}"

    # Description-based exclude (US work auth / security clearance)
    for pattern in HARD_EXCLUDE_PATTERNS:
        if re.search(pattern, description, re.IGNORECASE):
            return f"Description signal: {pattern[:40]}..."

    return None


def parse_job(job: dict) -> dict:
    """Parse and flatten a raw Adzuna API job result into a clean dict.

    search_terms: populated by the caller with all role terms that matched this job ID.
    """
    return {
        "id": job.get("id"),
        "title": job.get("title", ""),
        "company": job.get("company", {}).get("display_name", ""),
        "location": job.get("location", {}).get("display_name", ""),
        "description": job.get("description", ""),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "salary_display": format_salary(job),
        "redirect_url": job.get("redirect_url", ""),
        "created": job.get("created", ""),
        "search_terms": [],  # filled in by caller after overlap analysis
    }


# ---------------------------------------------------------------------------
# Main search logic
# ---------------------------------------------------------------------------

def run_search(app_id: str, app_key: str, what: str, where: Optional[str], label: str, page: int) -> tuple[list[dict], int]:
    """Run one Adzuna search and return (raw API result list, total available count).

    where: city/region string (e.g. "Calgary") — included as where param in the API call.
           Pass None to omit the where param entirely, resulting in a national Canada search
           (country is already scoped by the /ca/ path in the URL).
    """
    params: dict[str, Any] = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": RESULTS_PER_SEARCH,
        "what": what,
        "max_days_old": 30,
        "content-type": "application/json",
        "sort_by": "date",
    }
    if where:
        params["where"] = where
    url = f"{API_BASE_TEMPLATE.format(page=page)}?{urlencode(params)}"

    print(f"  🔍 Search (page {page}): {what!r} in {where!r}...", file=sys.stderr)
    data = fetch_url(url)

    if data is None:
        print(f"  ❌ Search failed for {what!r} in {where!r}", file=sys.stderr)
        return [], 0

    results = data.get("results", [])
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

    all_raw: list[tuple[dict, str]] = []  # (raw_job, source_label)
    search_log = []

    # Run one search per role term, for both locations.
    # "Calgary" → where=Calgary param included; city-scoped search.
    # None → where param omitted entirely; national Canada search (country already scoped by URL path /ca/).
    searches: list[tuple[Optional[str], str]] = [
        ("Calgary", "calgary"),
        (None, "canada_remote"),
    ]

    for term in SEARCH_TERMS:
        for where, label in searches:
            raw, total_available = run_search(app_id, app_key, term, where, label, args.page)
            search_log.append({
                "query": term,
                "where": where or "canada (national)",
                "raw_count": len(raw),
                "total_available": total_available,
            })
            # Attach "term|location" label to each raw result; location is stripped later, only term is used for overlap
            source_label = f"{term}|{label}"
            all_raw.extend((job, source_label) for job in raw)
            # Small delay between API calls to be polite
            time.sleep(0.5)

    print(f"\n  📦 Total raw results before dedup: {len(all_raw)}", file=sys.stderr)

    # Deduplicate on Adzuna job ID.
    # Track all term|location labels that matched each ID to derive which role terms overlap.
    seen: dict[str, list[str]] = {}  # key → [source_labels]
    seen_raw: dict[str, dict] = {}   # key → first raw_job seen (used to build the result)
    dedup_removed = 0

    for raw_job, source_label in all_raw:
        key = dedup_key(raw_job)
        if key in seen:
            seen[key].append(source_label)
            dedup_removed += 1
        else:
            seen[key] = [source_label]
            seen_raw[key] = raw_job

    print(f"  🗂️  After deduplication: {len(seen)} ({dedup_removed} removed)", file=sys.stderr)

    # Apply hard excludes on raw jobs before parse_job (category field is not carried through parse_job)
    clean_jobs: list[dict] = []
    hard_excluded: list[str] = []

    for key, source_labels in seen.items():
        raw_job = seen_raw[key]
        reason = is_hard_excluded(raw_job)
        if reason:
            company = (raw_job.get("company", {}).get("display_name") or "")
            title = raw_job.get("title") or ""
            hard_excluded.append(f"{company} — {title}: {reason}")
        else:
            job = parse_job(raw_job)
            # Strip location from labels; search_terms contains role terms only
            job["search_terms"] = sorted(set(label.split("|")[0] for label in source_labels))
            clean_jobs.append(job)

    print(f"  🚫 Hard excluded: {len(hard_excluded)}", file=sys.stderr)
    print(f"  ✅ Proceeding to queue: {len(clean_jobs)}", file=sys.stderr)

    output = {
        "run_date": date.today().isoformat(),
        "page": args.page,
        "searches": search_log,
        "results": clean_jobs,
        "deduplication_removed": dedup_removed,
        "hard_excluded": len(hard_excluded),
        "hard_excluded_reasons": hard_excluded,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  💾 Results written to {args.output}", file=sys.stderr)
    print(f"  Summary: {len(clean_jobs)} candidates added to queue", file=sys.stderr)

    # Print clean summary to stdout for SKILL.md to capture
    print(json.dumps({
        "candidate_count": len(clean_jobs),
        "output_path": args.output,
        "hard_excluded": len(hard_excluded),
        "dedup_removed": dedup_removed,
        "page": args.page,
    }))


if __name__ == "__main__":
    main()
