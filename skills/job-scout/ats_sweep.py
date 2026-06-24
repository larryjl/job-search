"""
ats_sweep.py — Concurrent ATS API sweep for the job-search skill system.

Reads the ### ATS-API section of profile/targets.md, calls the
Greenhouse / Lever / Ashby public APIs concurrently, filters by role keywords,
and writes a JSON file that the job-scout SKILL.md reads for further processing.

Usage:
    python3 ats_sweep.py [--output /tmp/ats_results.json] [--companies Neo,KOHO]
                         [--ignore-recheck] [--workers 8]

    --companies     Comma-separated company names (substring match, case-insensitive).
                    If omitted, sweeps all ATS-API companies whose Re-check After
                    date has passed (or is not set).
    --ignore-recheck  Run all companies regardless of Re-check After date.
    --workers       Max concurrent API calls (default: 8).

Output JSON format:
    {
        "run_date": "YYYY-MM-DD",
        "companies_attempted": N,
        "companies_skipped_recheck": N,
        "results": [
            {
                "company": "...",
                "ats": "greenhouse|lever|ashby",
                "slug": "...",
                "title": "...",
                "location": "...",
                "workplace_type": "...",    # remote / hybrid / on-site / ""
                "description": "...",       # up to 3000 chars, plain text
                "url": "...",               # direct posting URL
                "needs_chrome_fallback": bool  # true if JD was empty/truncated
            }
        ],
        "zero_match_companies": ["Company A", "Company B", ...],
        "error_companies": [{"company": "...", "error": "..."}]
    }
"""

import json
import os
import re
import sys
import subprocess
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from typing import Optional

# Add the shared library directory to the import path so we can use project_paths,
# http_client, and extractors without installing them as packages.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../lib'))
from project_paths import get_project_root
from http_client import fetch_json_curl as fetch_json
from extractors import strip_html

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# How long (in seconds) to wait for a single ATS API response before giving up.
API_TIMEOUT = 20

# Number of times to retry a failed API call before recording an error for that company.
# Kept deliberately low — ATS APIs are generally reliable, and one retry is enough
# to handle transient blips without making the sweep feel slow.
API_MAX_RETRIES = 2

# Base delay for exponential back-off between retries.
# Actual wait = API_RETRY_DELAY_BASE * 2^attempt  (e.g. 2s, 4s for attempt 0 and 1).
API_RETRY_DELAY_BASE = 2

# Maximum number of plain-text characters to store from each job description.
# Truncating here keeps the JSON output manageable; Claude reads the full JD
# via Chrome fallback when needed.
DESCRIPTION_MAX_CHARS = 3000

# If a job description (after HTML stripping) is shorter than this many characters,
# it almost certainly means the ATS served a stub rather than the real content.
# Such jobs are flagged with needs_chrome_fallback=True so SKILL.md knows to
# open the posting in Chrome to fetch the complete description.
DESCRIPTION_FALLBACK_THRESHOLD = 200

# Role keywords used to decide whether a job title is relevant.
# A posting matches if ANY of these strings appears as a substring in the title
# (case-insensitive). Update this list to broaden or narrow the sweep.
ROLE_KEYWORDS = [
    "data analyst",
    "data engineer",
    "analytics engineer",
    "analytics manager",
    "integration analyst",
    "integration engineer",
]

# Public API endpoint templates for each supported ATS platform.
# {slug} is replaced at runtime with the company-specific identifier extracted
# from the careers URL in targets.md.
#   Greenhouse: ?content=true asks the API to include the full job description HTML.
#   Lever:      ?mode=json returns the full posting list as a JSON array.
#   Ashby:      no extra params needed; the board endpoint returns all active jobs.
ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever":      "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby":      "https://api.ashbyhq.com/posting-api/job-board/{slug}",
}

# ---------------------------------------------------------------------------
# targets.md parser
# ---------------------------------------------------------------------------

def parse_targets(project_root: str) -> list[dict]:
    """Parse the ### ATS-API section of targets.md and return company metadata.

    The targets.md file is the authoritative list of companies to sweep. Each
    company line within the ### ATS-API section is a pipe-delimited record:

        - Name | description | ATS platform | careers URL | city | notes | last_checked | recheck_after

    This function extracts only the companies whose ATS platform is one of
    greenhouse / lever / ashby, derives the API slug from the careers URL,
    and parses the optional Re-check After date used for sweep gating.

    Args:
        project_root: Absolute path to the root of the job-search project
                      (used to locate .claude/memory/targets.md).

    Returns:
        A list of dicts, one per eligible company:
            {
                "name": str,
                "ats": "greenhouse" | "lever" | "ashby",
                "slug": str,           # company identifier for the API endpoint
                "careers_url": str,    # original URL from targets.md
                "recheck_after": date | None,  # skip sweep until this date passes
            }
    """
    targets_path = os.path.join(project_root, ".claude", "memory", "targets.md")
    with open(targets_path, encoding="utf-8") as f:
        content = f.read()

    # Locate the start of the ### ATS-API section.
    # re.MULTILINE makes ^ match the start of any line (not just the whole string).
    start_m = re.search(r"^### ATS-API", content, re.MULTILINE)
    if not start_m:
        raise ValueError("Could not find '### ATS-API' section in targets.md")

    # Find the next ### heading (exactly three hashes — not ####) that follows
    # the ATS-API section. The search starts from where the section heading ends
    # so we don't re-match the ATS-API heading itself.
    # The negative lookahead (?!#) ensures we stop at ### but not ####.
    end_m = re.search(r"^### (?!#)", content[start_m.end():], re.MULTILINE)

    # Slice out just the ATS-API block. If no following ### heading exists,
    # take everything from the ATS-API heading to end of file.
    ats_block = (
        content[start_m.start() : start_m.end() + end_m.start()]
        if end_m
        else content[start_m.start():]
    )

    companies = []

    # Iterate over every line in the extracted block, looking for list items.
    # List items start with "- " (dash space). Non-list lines (headings, blank
    # lines, prose) are skipped by the startswith check.
    for line in ats_block.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue

        # Strip the leading "- " and split the remainder on pipe characters.
        # Each cell is stripped of surrounding whitespace.
        # Expected column order (0-indexed):
        #   0: name  1: description  2: ATS platform  3: careers URL
        #   4: city  5: notes  6: last_checked  7: recheck_after
        parts = [p.strip() for p in line[2:].split("|")]
        if len(parts) < 4:
            # Need at minimum: name, description, ATS, URL
            continue

        name_raw    = parts[0]
        # Column 2 holds the ATS platform name; lower-case for reliable matching.
        ats_raw     = parts[2].lower() if len(parts) > 2 else ""
        url_raw     = parts[3] if len(parts) > 3 else ""
        # Column 7 is optional — may not exist if the line has fewer than 8 columns.
        recheck_raw = parts[7].strip() if len(parts) > 7 else ""

        # Normalise the ATS platform name to one of the three supported values.
        # The cell might read "Greenhouse (ATS-API)" or similar, so we use 'in'
        # rather than an exact equality check.
        if "greenhouse" in ats_raw:
            ats = "greenhouse"
        elif "lever" in ats_raw:
            ats = "lever"
        elif "ashby" in ats_raw:
            ats = "ashby"
        else:
            # Not an ATS-API company (probably a browser-only company listed
            # in a different section). Skip silently.
            continue

        # Derive the company slug from the careers URL using ATS-specific patterns.
        slug = _extract_slug(url_raw, ats)
        if not slug:
            # Without a slug we cannot construct the API URL, so skip and warn.
            print(f"  ⚠️  Could not extract slug for {name_raw} ({url_raw}) — skipping",
                  file=sys.stderr)
            continue

        # Parse the optional Re-check After date (YYYY-MM-DD).
        # If the field is blank or malformed, recheck_after stays None,
        # meaning the company will always be included in sweeps.
        recheck_after = None
        if recheck_raw:
            try:
                recheck_after = datetime.strptime(recheck_raw, "%Y-%m-%d").date()
            except ValueError:
                # Malformed date — treat as if no recheck date is set.
                pass

        # Some company names in targets.md include a parenthetical domain hint
        # like "Neo (neo.com)". Strip it so output filenames stay clean.
        name = re.sub(r"\s*\(.*?\)\s*$", "", name_raw).strip()

        companies.append({
            "name": name,
            "ats": ats,
            "slug": slug,
            "careers_url": url_raw,
            "recheck_after": recheck_after,
        })

    return companies


def _extract_slug(url: str, ats: str) -> Optional[str]:
    """Extract the company slug from a known ATS careers URL.

    Each ATS platform uses a predictable URL structure where the company's
    unique identifier (the "slug") appears as a path segment. For example:

        Greenhouse public board:  https://job-boards.greenhouse.io/acmecorp
        Greenhouse legacy board:  https://boards.greenhouse.io/acmecorp
        Lever:                    https://jobs.lever.co/acmecorp
        Ashby:                    https://jobs.ashbyhq.com/acmecorp

    Multiple patterns are listed per ATS to cover URL variants that appear
    in the wild (e.g. branded Greenhouse boards vs. the canonical boards URL,
    or a URL that goes directly to the API endpoint).

    Args:
        url: The careers page URL as stored in targets.md.
        ats: One of "greenhouse", "lever", "ashby".

    Returns:
        The slug string (e.g. "acmecorp"), or None if no pattern matched.
    """
    patterns = {
        "greenhouse": [
            # New-style public board: job-boards.greenhouse.io/<slug>
            r"job-boards\.greenhouse\.io/([^/?#\s]+)",
            # Legacy public board: boards.greenhouse.io/<slug>
            r"boards\.greenhouse\.io/([^/?#\s]+)",
            # Direct API URL (rare — stored if the user pasted the API endpoint):
            # boards-api.greenhouse.io/v1/boards/<slug>
            r"boards-api\.greenhouse\.io/v1/boards/([^/?#\s]+)",
        ],
        "lever": [
            # All Lever boards follow this single pattern: jobs.lever.co/<slug>
            r"jobs\.lever\.co/([^/?#\s]+)",
        ],
        "ashby": [
            # All Ashby boards follow this single pattern: jobs.ashbyhq.com/<slug>
            r"jobs\.ashbyhq\.com/([^/?#\s]+)",
        ],
    }

    for pattern in patterns.get(ats, []):
        m = re.search(pattern, url, re.IGNORECASE)
        if m:
            # group(1) is the first capture group — the slug itself.
            # rstrip("/") removes any trailing slash that some URLs include.
            return m.group(1).rstrip("/")

    # No pattern matched — caller will log a warning and skip this company.
    return None

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

# (fetch_json is imported from skills/lib/http_client.py, which handles
# retries and exponential back-off internally.)

# ---------------------------------------------------------------------------
# ATS-specific parsers
# ---------------------------------------------------------------------------


def _matches_keywords(title: str) -> bool:
    """Return True if the job title contains at least one role keyword.

    Matching is case-insensitive substring search. A title like
    "Senior Data Analyst, Payments" matches "data analyst".
    The ROLE_KEYWORDS list at the top of this module controls which
    titles are considered relevant.

    Args:
        title: Raw job title string from the ATS API.

    Returns:
        True if any keyword is found in the lowercased title, False otherwise.
    """
    # Lower-case once so every 'in' check below is case-insensitive.
    t = title.lower()
    return any(k in t for k in ROLE_KEYWORDS)


def _parse_greenhouse(data: dict | list, company: str) -> list[dict]:
    """Parse a Greenhouse API response and return keyword-matched job dicts.

    Greenhouse returns a top-level dict with a "jobs" list. Each job object
    includes:
        - "title":        plain-text job title
        - "content":      full HTML job description (available because we pass
                          ?content=true in the endpoint URL)
        - "location":     a nested dict with a "name" key for the display name
        - "absolute_url": the direct link to the public posting on Greenhouse

    Notable Greenhouse differences from Lever/Ashby:
        - Description is HTML (needs strip_html), not plain text.
        - No workplace_type field — always returns an empty string here.
        - location is a dict, not a plain string.

    Args:
        data:    Parsed JSON response from the Greenhouse boards API.
        company: Display name of the company (for the output dict).

    Returns:
        List of matched job dicts in the standard output schema.
    """
    # Greenhouse wraps jobs in a top-level dict; guard against unexpected shapes.
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    results = []

    for j in jobs:
        title = j.get("title", "")

        # Skip postings whose title doesn't match our role keywords.
        if not _matches_keywords(title):
            continue

        # "content" is the raw HTML job description; strip_html converts it to
        # plain text so downstream scoring works without HTML parser dependencies.
        html = j.get("content", "") or ""
        desc = strip_html(html)

        # location is a dict like {"name": "Remote, Canada"} — extract the
        # display string, or fall back to a plain string if the shape differs.
        loc_raw = j.get("location", {})
        location = loc_raw.get("name", "") if isinstance(loc_raw, dict) else str(loc_raw)

        results.append({
            "company": company,
            "ats": "greenhouse",
            "title": title,
            "location": location,
            # Greenhouse does not expose a workplace type in its public API.
            "workplace_type": "",
            # Truncate long descriptions to avoid bloating the JSON output file.
            "description": desc[:DESCRIPTION_MAX_CHARS],
            "url": j.get("absolute_url", ""),
            # Flag short descriptions — they signal the ATS served a stub JD
            # and we need Chrome to fetch the real content.
            "needs_chrome_fallback": len(desc) < DESCRIPTION_FALLBACK_THRESHOLD,
        })

    return results


def _parse_lever(data: dict | list, company: str) -> list[dict]:
    """Parse a Lever API response and return keyword-matched job dicts.

    Lever returns a top-level JSON array (not a dict). Each element includes:
        - "text":              plain-text job title  (Lever calls it "text", not "title")
        - "descriptionPlain":  plain-text job description  (no HTML stripping needed)
        - "categories":        a dict containing "location" and other metadata
        - "workplaceType":     explicit workplace type string (e.g. "remote", "hybrid")
        - "hostedUrl":         the direct link to the public posting on Lever

    Notable Lever differences from Greenhouse/Ashby:
        - The API returns a list at the top level, not a dict.
        - Title field is "text", not "title".
        - Description is already plain text — no HTML stripping needed.
        - Location is nested inside a "categories" dict.
        - workplace_type is explicit and reliable.

    Args:
        data:    Parsed JSON response from the Lever postings API.
        company: Display name of the company (for the output dict).

    Returns:
        List of matched job dicts in the standard output schema.
    """
    # Lever's endpoint returns a bare JSON array; guard against dict responses
    # (e.g. error payloads).
    jobs = data if isinstance(data, list) else []
    results = []

    for j in jobs:
        # Lever uses "text" for the job title — different from every other ATS.
        title = j.get("text", "")

        if not _matches_keywords(title):
            continue

        # "descriptionPlain" is already stripped of HTML by Lever's API.
        # Use "or ''" to normalise None to an empty string.
        desc = j.get("descriptionPlain", "") or ""

        # Location lives inside the nested "categories" dict.
        cats = j.get("categories", {})
        location = cats.get("location", "") if isinstance(cats, dict) else ""

        # "workplaceType" is a first-class field on Lever postings.
        workplace = j.get("workplaceType", "") or ""

        results.append({
            "company": company,
            "ats": "lever",
            "title": title,
            "location": location,
            # Normalise to lowercase for consistent downstream comparison.
            "workplace_type": workplace.lower(),
            "description": desc[:DESCRIPTION_MAX_CHARS],
            "url": j.get("hostedUrl", ""),
            "needs_chrome_fallback": len(desc) < DESCRIPTION_FALLBACK_THRESHOLD,
        })

    return results


def _parse_ashby(data: dict | list, company: str) -> list[dict]:
    """Parse an Ashby API response and return keyword-matched job dicts.

    Ashby returns a top-level dict with a "jobs" list. Each job object includes:
        - "title":           plain-text job title
        - "descriptionPlain": plain-text description (preferred; may be absent)
        - "descriptionHtml":  HTML fallback if plain text is unavailable
        - "location":        plain-text location string
        - "workplaceType":   workplace type string (may be absent)
        - "isRemote":        boolean flag — if True and workplaceType is blank,
                             we infer workplace_type = "remote"
        - "jobUrl":          the direct link to the public posting on Ashby

    Notable Ashby differences from Greenhouse/Lever:
        - Plain-text description is the primary field, with HTML as fallback.
        - Has an explicit isRemote boolean separate from workplaceType.
        - location is a plain string, not a nested dict.

    Args:
        data:    Parsed JSON response from the Ashby job board API.
        company: Display name of the company (for the output dict).

    Returns:
        List of matched job dicts in the standard output schema.
    """
    # Ashby wraps jobs in a top-level dict; guard against unexpected shapes.
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    results = []

    for j in jobs:
        title = j.get("title", "")

        if not _matches_keywords(title):
            continue

        # Prefer the plain-text description. Fall back to stripping the HTML
        # version if the plain-text field is absent or empty.
        desc = j.get("descriptionPlain", "") or ""
        if not desc:
            html = j.get("descriptionHtml", "") or ""
            desc = strip_html(html)

        # location is a plain string on Ashby (no nesting required).
        loc = j.get("location", "") or ""

        workplace = j.get("workplaceType", "") or ""

        # Ashby sometimes omits workplaceType but sets the isRemote boolean.
        # If workplaceType is blank and isRemote is True, infer "remote".
        if j.get("isRemote"):
            workplace = workplace or "remote"

        results.append({
            "company": company,
            "ats": "ashby",
            "title": title,
            "location": loc,
            "workplace_type": workplace.lower(),
            "description": desc[:DESCRIPTION_MAX_CHARS],
            "url": j.get("jobUrl", ""),
            "needs_chrome_fallback": len(desc) < DESCRIPTION_FALLBACK_THRESHOLD,
        })

    return results


# Dispatch table: maps ATS platform name → its parser function.
# sweep_company uses this to avoid a chain of if/elif checks.
PARSERS = {
    "greenhouse": _parse_greenhouse,
    "lever":      _parse_lever,
    "ashby":      _parse_ashby,
}

# ---------------------------------------------------------------------------
# Per-company sweep
# ---------------------------------------------------------------------------

def sweep_company(company: dict) -> dict:
    """Fetch and filter one company's ATS board via its public API.

    This function is designed to be called from a ThreadPoolExecutor — it is
    stateless (reads only from its argument dict and module-level constants)
    and never mutates shared state, so it is safe to run concurrently with
    other sweep_company calls without locks.

    Args:
        company: A dict as returned by parse_targets(), containing at minimum:
                 "name", "ats", "slug", and "careers_url".

    Returns:
        A dict with:
            "company"    — company display name
            "results"    — list of matched job dicts (may be empty)
            "error"      — error message string if the API call failed, else None
            "zero_match" — True if the API call succeeded but no roles matched
                           (False if there was an error — errors are tracked
                            separately so they don't inflate the zero-match list)
    """
    name = company["name"]
    ats  = company["ats"]
    slug = company["slug"]

    # Build the API endpoint URL by substituting the company's slug into the
    # template for its ATS platform.
    url  = ENDPOINTS[ats].format(slug=slug)

    print(f"  🔍 {name} ({ats.capitalize()} / {slug})...", file=sys.stderr)

    try:
        # fetch_json (imported from http_client) handles retries and back-off
        # internally; it raises RuntimeError if all retries fail.
        data = fetch_json(url)
    except RuntimeError as e:
        print(f"  ❌ {name}: {e}", file=sys.stderr)
        # Return a non-zero_match error result so the caller can distinguish
        # "API failed" from "API succeeded but no relevant roles found".
        return {"company": name, "results": [], "error": str(e), "zero_match": False}

    # Select the parser for this ATS and extract matching roles.
    parser = PARSERS[ats]
    results = parser(data, name)

    if results:
        # Count how many matched roles have descriptions too short to be useful —
        # these will need Chrome to fetch the full JD before scoring can run.
        fallback_count = sum(1 for r in results if r["needs_chrome_fallback"])
        fb_note = f" ({fallback_count} need Chrome JD fallback)" if fallback_count else ""
        print(f"     → {len(results)} matching role(s){fb_note}", file=sys.stderr)
    else:
        print(f"     → no matching roles", file=sys.stderr)

    return {
        "company": name,
        "results": results,
        "error": None,
        # zero_match=True when the API responded fine but no roles passed the
        # keyword filter — useful for spotting companies that changed their
        # hiring focus or have a dry pipeline right now.
        "zero_match": len(results) == 0,
    }

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Concurrent ATS sweep for job-search skill")
    parser.add_argument("--output", default="/tmp/ats_results.json",
                        help="Path to write JSON output (default: /tmp/ats_results.json)")
    parser.add_argument("--companies", default="",
                        help="Comma-separated company name substrings to sweep (default: all eligible)")
    parser.add_argument("--ignore-recheck", action="store_true",
                        help="Ignore Re-check After dates and sweep all companies")
    parser.add_argument("--workers", type=int, default=8,
                        help="Max concurrent API calls (default: 8)")
    args = parser.parse_args()

    project_root = get_project_root()
    all_companies = parse_targets(project_root)

    today = date.today()

    # If --companies was given, split on commas and normalise to lowercase so
    # matching is case-insensitive (e.g. "neo,koho" matches "Neo" and "KOHO").
    filter_names = [n.strip().lower() for n in args.companies.split(",") if n.strip()]

    # Narrow the company list to those whose names contain any of the filter strings.
    if filter_names:
        all_companies = [
            c for c in all_companies
            if any(f in c["name"].lower() for f in filter_names)
        ]
        if not all_companies:
            print(f"❌ No ATS-API companies matched: {args.companies}", file=sys.stderr)
            sys.exit(1)

    # Re-check After gating: each company in targets.md can have a date that
    # says "don't sweep again until at least this date" — used to avoid hammering
    # boards that we know have no new roles yet. Companies without a date, or
    # whose date has passed, are added to the eligible list.
    # --ignore-recheck bypasses this gate entirely (useful for debugging or
    # when the user wants a fresh full sweep regardless of dates).
    skipped = []
    eligible = []
    for c in all_companies:
        if not args.ignore_recheck and c["recheck_after"] and c["recheck_after"] > today:
            # Recheck date is in the future — skip this company today.
            skipped.append(c["name"])
        else:
            eligible.append(c)

    if skipped:
        print(f"  ⏭️  Skipping {len(skipped)} companies (Re-check After not reached): "
              f"{', '.join(skipped)}", file=sys.stderr)

    # If nothing is eligible, write an empty result file and exit cleanly.
    # This avoids confusing error states when all companies are on recheck cooldown.
    if not eligible:
        print("  ℹ️  No companies eligible to sweep today.", file=sys.stderr)
        output = {
            "run_date": today.isoformat(),
            "companies_attempted": 0,
            "companies_skipped_recheck": len(skipped),
            "results": [],
            "zero_match_companies": [],
            "error_companies": [],
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        # Print the machine-readable summary to stdout for SKILL.md to capture.
        print(json.dumps({"candidate_count": 0, "output_path": args.output}))
        return

    print(f"\n🔎 Sweeping {len(eligible)} ATS-API companies "
          f"(workers={args.workers})...\n", file=sys.stderr)

    all_results = []
    zero_match  = []
    errors      = []

    # ThreadPoolExecutor runs sweep_company() calls concurrently, up to
    # `args.workers` at a time. This is safe because sweep_company is stateless:
    # each call only touches its own local variables and the (read-only) module
    # constants. The dict comprehension `{executor.submit(...): c}` maps each
    # Future back to the company dict it was created for (useful for debugging,
    # though here we only use the Future result).
    # as_completed() yields each Future as it finishes, regardless of submission
    # order — so results trickle in as soon as each API call returns.
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(sweep_company, c): c for c in eligible}
        for future in as_completed(futures):
            outcome = future.result()
            all_results.extend(outcome["results"])
            if outcome["error"]:
                errors.append({"company": outcome["company"], "error": outcome["error"]})
            elif outcome["zero_match"]:
                zero_match.append(outcome["company"])

    print(f"\n  ✅ Total matching roles: {len(all_results)}", file=sys.stderr)
    print(f"  ℹ️  Zero-match companies: {len(zero_match)}", file=sys.stderr)
    if errors:
        print(f"  ❌ Errors: {len(errors)}", file=sys.stderr)

    # Count how many results will need Chrome to fetch the complete JD.
    needs_fallback = sum(1 for r in all_results if r["needs_chrome_fallback"])
    if needs_fallback:
        print(f"  ⚠️  {needs_fallback} role(s) need Chrome JD fallback (description < {DESCRIPTION_FALLBACK_THRESHOLD} chars)",
              file=sys.stderr)

    output = {
        "run_date": today.isoformat(),
        "companies_attempted": len(eligible),
        "companies_skipped_recheck": len(skipped),
        "results": all_results,
        # Sort for stable ordering — makes diffs across runs easier to read.
        "zero_match_companies": sorted(zero_match),
        "error_companies": errors,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  💾 Results written to {args.output}", file=sys.stderr)

    # Print a compact machine-readable JSON summary to stdout.
    # SKILL.md captures this line (not the stderr progress output) to learn
    # how many candidates were found and where the full results file lives.
    print(json.dumps({
        "candidate_count": len(all_results),
        "output_path": args.output,
        "companies_attempted": len(eligible),
        "companies_skipped_recheck": len(skipped),
        "zero_match_companies": len(zero_match),
        "needs_chrome_fallback": needs_fallback,
        "errors": len(errors),
    }))


if __name__ == "__main__":
    main()
