# ATS Auto-Detection

Subroutine for determining which ATS platform a company uses and routing it to `ats-api` or `browser-only`.

**When to run:** Company has "Unknown" ATS, is missing a tier, or is being added during a named run. Also triggered as fallback A3 when slug probing fails.

**Input:** Company name (and optionally a guessed slug).
**Output:** Platform assignment + write-back to `profile/target-companies.md` only.

---

## Detection Sequence

**D1 — Lever:** `site:jobs.lever.co/[slug]` → ats-api if results. Try 1–2 slug variations before concluding "not Lever".

**D2 — Greenhouse:** `site:boards.greenhouse.io/[slug]` OR `site:job-boards.greenhouse.io/[slug]` → ats-api if results.

**D3 — Ashby:** `site:jobs.ashbyhq.com/[slug]` → ats-api if results.

**D4 — Workable:** `site:apply.workable.com/[slug]` → browser-only if results (no public API; requires Chrome).

**D5 — ApplyToJob:** `site:[companyslug].applytojob.com` → browser-only if results. No results → browser-only.

**D6 — Broad platform signal** (if D1–D5 all fail):
```
"[Company Name]" careers site:workforcenow.adp.com OR site:myworkdayjobs.com OR site:greenhouse.io OR site:lever.co OR site:ashbyhq.com OR site:taleo.net OR site:icims.com OR site:successfactors.com
```
- ADP WorkforceNow → browser-only (cid GUID required; do NOT attempt via web_fetch)
- Workday → browser-only (JS-rendered); record tenant subdomain
- Taleo / iCIMS / SuccessFactors / PeopleSoft → browser-only; note platform
- Greenhouse or Lever found → extract slug, re-run D1 or D2 to confirm

**D7 — Careers page signal** (if D1–D6 all fail):
```
"[Company Name]" careers jobs "data analyst" OR "data engineer"
```
- Indexed with fetchable URLs → ats-api, Custom (indexed)
- Exists but not indexed → browser-only, Custom (not indexed); note "browse directly"
- Nothing found → browser-only; note "no ATS found; check careers page manually"

---

## Write-Back

Move company in `profile/target-companies.md` from `### Unknown` to `### ATS-API` or `### Browser-Only`. Update: ATS column, Board URL, Notes (platform + date), Last Checked.

---

## Announce

```
🔎 ATS detected — [Company]: [Platform] → ats-api | target-companies.md updated (moved from Unknown)
🔎 ATS detected — [Company]: [Platform] → browser-only | target-companies.md updated (moved from Unknown)
⚠️ ATS not found — [Company]: no indexed board; assigned browser-only (Chrome browse)
```
