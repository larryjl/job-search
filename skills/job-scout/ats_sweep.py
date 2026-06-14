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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../lib'))
from project_paths import get_project_root
from http_client import fetch_json_curl as fetch_json
from extractors import strip_html

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_TIMEOUT = 20
API_MAX_RETRIES = 2        # lighter than adzuna — one retry is usually enough
API_RETRY_DELAY_BASE = 2   # seconds; actual delay = base * 2^attempt (exponential backoff)
DESCRIPTION_MAX_CHARS = 3000
DESCRIPTION_FALLBACK_THRESHOLD = 200  # chars — below this, flag needs_chrome_fallback

ROLE_KEYWORDS = [
    "data analyst",
    "data engineer",
    "analytics engineer",
    "analytics manager",
    "integration analyst",
    "integration engineer",
]

# ATS endpoint templates
ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever":      "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby":      "https://api.ashbyhq.com/posting-api/job-board/{slug}",
}

# ---------------------------------------------------------------------------
# targets.md parser
# ---------------------------------------------------------------------------

def parse_targets(project_root: str) -> list[dict]:
    """
    Parse the ### ATS-API section of targets.md.
    Returns a list of company dicts:
        {
            "name": str,
            "ats": "greenhouse"|"lever"|"ashby",
            "slug": str,           # extracted from careers URL
            "careers_url": str,
            "recheck_after": date | None,
        }
    """
    targets_path = os.path.join(project_root, ".claude", "memory", "targets.md")
    with open(targets_path, encoding="utf-8") as f:
        content = f.read()

    # Find the ### ATS-API section.
    # Stop at the next exactly-### heading (not ####) or end of file.
    start_m = re.search(r"^### ATS-API", content, re.MULTILINE)
    if not start_m:
        raise ValueError("Could not find '### ATS-API' section in targets.md")
    end_m = re.search(r"^### (?!#)", content[start_m.end():], re.MULTILINE)
    ats_block = (
        content[start_m.start() : start_m.end() + end_m.start()]
        if end_m
        else content[start_m.start():]
    )

    companies = []
    # Each company line: - Name | desc | ATS | url | city | notes | last_checked | recheck_after
    for line in ats_block.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        parts = [p.strip() for p in line[2:].split("|")]
        if len(parts) < 4:
            continue

        name_raw = parts[0]
        ats_raw  = parts[2].lower() if len(parts) > 2 else ""
        url_raw  = parts[3] if len(parts) > 3 else ""
        recheck_raw = parts[7].strip() if len(parts) > 7 else ""

        # Normalise ATS name
        if "greenhouse" in ats_raw:
            ats = "greenhouse"
        elif "lever" in ats_raw:
            ats = "lever"
        elif "ashby" in ats_raw:
            ats = "ashby"
        else:
            continue  # not an ATS-API company

        # Extract slug from careers URL
        slug = _extract_slug(url_raw, ats)
        if not slug:
            print(f"  ⚠️  Could not extract slug for {name_raw} ({url_raw}) — skipping",
                  file=sys.stderr)
            continue

        # Parse recheck_after date
        recheck_after = None
        if recheck_raw:
            try:
                recheck_after = datetime.strptime(recheck_raw, "%Y-%m-%d").date()
            except ValueError:
                pass

        # Clean company name (strip parenthetical domain hints)
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
    """Extract the company slug from a known ATS careers URL."""
    patterns = {
        "greenhouse": [
            r"job-boards\.greenhouse\.io/([^/?#\s]+)",
            r"boards\.greenhouse\.io/([^/?#\s]+)",
            r"boards-api\.greenhouse\.io/v1/boards/([^/?#\s]+)",
        ],
        "lever": [
            r"jobs\.lever\.co/([^/?#\s]+)",
        ],
        "ashby": [
            r"jobs\.ashbyhq\.com/([^/?#\s]+)",
        ],
    }
    for pattern in patterns.get(ats, []):
        m = re.search(pattern, url, re.IGNORECASE)
        if m:
            return m.group(1).rstrip("/")
    return None

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# ATS-specific parsers
# ---------------------------------------------------------------------------



def _matches_keywords(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in ROLE_KEYWORDS)


def _parse_greenhouse(data: dict | list, company: str) -> list[dict]:
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    results = []
    for j in jobs:
        title = j.get("title", "")
        if not _matches_keywords(title):
            continue
        html = j.get("content", "") or ""
        desc = strip_html(html)
        loc_raw = j.get("location", {})
        location = loc_raw.get("name", "") if isinstance(loc_raw, dict) else str(loc_raw)
        results.append({
            "company": company,
            "ats": "greenhouse",
            "title": title,
            "location": location,
            "workplace_type": "",
            "description": desc[:DESCRIPTION_MAX_CHARS],
            "url": j.get("absolute_url", ""),
            "needs_chrome_fallback": len(desc) < DESCRIPTION_FALLBACK_THRESHOLD,
        })
    return results


def _parse_lever(data: dict | list, company: str) -> list[dict]:
    jobs = data if isinstance(data, list) else []
    results = []
    for j in jobs:
        title = j.get("text", "")
        if not _matches_keywords(title):
            continue
        desc = j.get("descriptionPlain", "") or ""
        cats = j.get("categories", {})
        location = cats.get("location", "") if isinstance(cats, dict) else ""
        workplace = j.get("workplaceType", "") or ""
        results.append({
            "company": company,
            "ats": "lever",
            "title": title,
            "location": location,
            "workplace_type": workplace.lower(),
            "description": desc[:DESCRIPTION_MAX_CHARS],
            "url": j.get("hostedUrl", ""),
            "needs_chrome_fallback": len(desc) < DESCRIPTION_FALLBACK_THRESHOLD,
        })
    return results


def _parse_ashby(data: dict | list, company: str) -> list[dict]:
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    results = []
    for j in jobs:
        title = j.get("title", "")
        if not _matches_keywords(title):
            continue
        desc = j.get("descriptionPlain", "") or ""
        if not desc:
            html = j.get("descriptionHtml", "") or ""
            desc = strip_html(html)
        loc = j.get("location", "") or ""
        workplace = j.get("workplaceType", "") or ""
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


PARSERS = {
    "greenhouse": _parse_greenhouse,
    "lever":      _parse_lever,
    "ashby":      _parse_ashby,
}

# ---------------------------------------------------------------------------
# Per-company sweep
# ---------------------------------------------------------------------------

def sweep_company(company: dict) -> dict:
    """
    Fetch and filter one company's ATS board.
    Returns:
        {"company": str, "results": [...], "error": str|None, "zero_match": bool}
    """
    name = company["name"]
    ats  = company["ats"]
    slug = company["slug"]
    url  = ENDPOINTS[ats].format(slug=slug)

    print(f"  🔍 {name} ({ats.capitalize()} / {slug})...", file=sys.stderr)

    try:
        data = fetch_json(url)
    except RuntimeError as e:
        print(f"  ❌ {name}: {e}", file=sys.stderr)
        return {"company": name, "results": [], "error": str(e), "zero_match": False}

    parser = PARSERS[ats]
    results = parser(data, name)

    if results:
        fallback_count = sum(1 for r in results if r["needs_chrome_fallback"])
        fb_note = f" ({fallback_count} need Chrome JD fallback)" if fallback_count else ""
        print(f"     → {len(results)} matching role(s){fb_note}", file=sys.stderr)
    else:
        print(f"     → no matching roles", file=sys.stderr)

    return {
        "company": name,
        "results": results,
        "error": None,
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
    filter_names = [n.strip().lower() for n in args.companies.split(",") if n.strip()]

    # Filter by --companies if provided
    if filter_names:
        all_companies = [
            c for c in all_companies
            if any(f in c["name"].lower() for f in filter_names)
        ]
        if not all_companies:
            print(f"❌ No ATS-API companies matched: {args.companies}", file=sys.stderr)
            sys.exit(1)

    # Apply Re-check After gating
    skipped = []
    eligible = []
    for c in all_companies:
        if not args.ignore_recheck and c["recheck_after"] and c["recheck_after"] > today:
            skipped.append(c["name"])
        else:
            eligible.append(c)

    if skipped:
        print(f"  ⏭️  Skipping {len(skipped)} companies (Re-check After not reached): "
              f"{', '.join(skipped)}", file=sys.stderr)

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
        print(json.dumps({"candidate_count": 0, "output_path": args.output}))
        return

    print(f"\n🔎 Sweeping {len(eligible)} ATS-API companies "
          f"(workers={args.workers})...\n", file=sys.stderr)

    all_results = []
    zero_match  = []
    errors      = []

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

    needs_fallback = sum(1 for r in all_results if r["needs_chrome_fallback"])
    if needs_fallback:
        print(f"  ⚠️  {needs_fallback} role(s) need Chrome JD fallback (description < {DESCRIPTION_FALLBACK_THRESHOLD} chars)",
              file=sys.stderr)

    output = {
        "run_date": today.isoformat(),
        "companies_attempted": len(eligible),
        "companies_skipped_recheck": len(skipped),
        "results": all_results,
        "zero_match_companies": sorted(zero_match),
        "error_companies": errors,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  💾 Results written to {args.output}", file=sys.stderr)

    # Clean summary to stdout for SKILL.md to capture
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
