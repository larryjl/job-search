---
name: job-scout
description: "Finds live job listings via ATS platforms and company career pages. Five entry points: /job-scout (asks which mode to run), /scout-ats (keyword search across Lever/Greenhouse/Ashby, no slug), /scout-company or /scout-com (full sweep of all target companies, routed by ATS type), /scout-company companies:[list] (named sweep, same routing), /paste-batch (score pasted JDs directly, no web search or Chrome), /scout-link (scrape a live LinkedIn search results page via Chrome). For broad Canadian market search via Adzuna API, use /scout-adzuna (see skills/scout-adzuna/SKILL.md)."
---

# Job Scout

Five entry points — all converge on the same filter and output pipeline after JD discovery. Does NOT search broad job boards (Indeed, Workopolis, Randstad). For Adzuna broad market search, use `/scout-adzuna` (see `skills/scout-adzuna/SKILL.md`).

**Pipeline entry points by mode:**
- `/scout-ats` → Steps 2 → 3 → 4+
- `/scout-company` (ats-api and browser-only) → Step 3 → 4+
- `/paste-batch` → Step 3 (P1–P2) → 4+ (Steps 2, 3 search/Chrome do not apply)
- `/scout-link` → see `skills/scout-link/SKILL.md`

---

## Step 0 — Load Context

Silently load before any searching:

**A. Targets** from `profile/targets.md` (roles, location, salary, visa, preferences)

**B. Company list + ATS routing** (`/scout-company` and named companies only):
- `/scout-company` → load all companies from `company-ranking.md` in ranked order (Tier 1 → 4, row order within tier); exclude `## Excluded / Deprioritized`.
- Named run → load named subset from `profile/target-companies.md`.
- For each company in the run, read `profile/target-companies.md`: ATS platform, Careers URL, routing type (section: `### ATS-API` → ats-api; `### Browser-Only` → browser-only; `### Unknown` → Auto-Detection first), Re-check After date. If date not yet reached → skip company silently. Preserve rank order through the entire pipeline.

**C. Scout cache** (`/scout-company`, `/scout-ats`):
Read `scout-cache.md` before any searching begins.
- `/scout-company`: last run < 3 days ago AND current company list is a subset of last run → ask: "Last scout ran [N days] ago. Use cache or run fresh? (cache / fresh)". Current run includes new companies → run fresh for new ones; use cache for overlapping. No prompt. 3+ days ago → run fresh automatically.
- `/scout-ats`: use jobs.csv and the Hard-Excluded URL Cache for dedup at Step O2. No cache-age prompt; always run fresh.

---

## Step 1 — Entry Point Detection

### `/job-scout`
Ask: "Which scout mode?
- `scout-ats` — open ATS keyword search (Lever, Greenhouse, Ashby)
- `scout-company` — full company sweep from targets list
- `scout-adzuna` — broad Canadian market via Adzuna API (see `skills/scout-adzuna/SKILL.md`)
- `paste-batch` — score pasted JDs directly
- `scout-link` — scrape LinkedIn search results via Chrome"

### `/scout-ats`
Announce: `🔍 Starting open search: Lever, Greenhouse, Ashby`
Run Open Search steps O1–O4. Do not sweep browser-only companies.
If Chrome not connected: "⚠️ Claude in Chrome is not connected — open search postings cannot be verified. Continue without Chrome (unverified URLs only)? (yes / connect first)"

### `/scout-company` — Full company sweep
Announce: `🔍 Starting company sweep: [N] ats-api + [N] browser-only (Tier 1–2 only) + [N] unknown (detection pending)`
Load all companies from `company-ranking.md` in rank order; route each by section in `profile/target-companies.md`. Run ats-api companies first (all tiers), then browser-only.
**Browser-only scope cap:** In a full `/scout-company` run, only sweep browser-only companies in Tier 1 and Tier 2. Tier 3 and Tier 4 browser-only companies are skipped — note at the end of the run: `ℹ️ Browser-only Tier 3–4 skipped (run /scout-company companies:[list] to sweep individually)`. Named runs (`/scout-company companies:[list]`) sweep all named companies regardless of tier.
If Claude in Chrome not connected and browser-only or partial-access companies exist: proceed with ats-api companies first, then apply the **Claude in Chrome unavailable** fallback (see B1) for browser-only and partial-access companies — web search signal check only, no scoring.
If Claude in Chrome not connected and ats-api companies only: proceed. JD content fallback via Chrome is unavailable — any ATS-API role with an empty or unvalidated JD will be marked ⚠️ Unverified and not scored (see Step 5 JD validation gate).

### `/scout-company companies: [list]` — Named sweep
Check each company's section in `profile/target-companies.md`: `### ATS-API` → ats-api; `### Browser-Only` → browser-only; `### Unknown` or not present → Auto-Detection first. Run ats-api companies first, then browser-only.

### `/scout-adzuna`
Read and execute `skills/scout-adzuna/SKILL.md` exactly.

### `/paste-batch`
Announce: `📋 Paste batch mode — no web search or Chrome required.`
Run P1–P2; enter shared pipeline at Step 4.

### `/scout-link`
Read and execute `skills/scout-link/SKILL.md` exactly.

---

## Step 2 — Domain Access Gating

Check `.claude/config/domains.md` under `## job-scout` before accessing any domain via Chrome or web fetch. For unapproved domains: output `🔒 Domain access request: [domain]`, ask permission. Approved → add to whitelist, proceed. Denied → skip.

Domains needed (open-search): `jobs.lever.co`, `boards.greenhouse.io`, `job-boards.greenhouse.io`, `jobs.ashbyhq.com`
Domains needed (browser-only): `apply.workable.com`, `*.myworkdayjobs.com`, company career-page hostnames, portal hostnames

---

## Step 3 — Mode-Dependent Job Search

### ATS-API Path — Direct ATS API (Company Sweep)

Used for: `/scout-company` and ats-api companies in named runs.

ATS APIs return live, structured data directly from the source — no stale Google-indexed URLs, no Chrome needed for liveness. Chrome is only used as a fallback if the JD content field is missing or truncated.

All three APIs (Greenhouse, Lever, Ashby) are public and unauthenticated. For endpoints, field names, and the `curl | python3` pattern, see **`ats-api-reference.md`** in this skill folder.

**Implementation script:** `skills/job-scout/ats_sweep.py` — run this for bulk ATS API fetching. It imports shared utilities from `skills/lib/` (project_paths, filename_builder, extractors).

##### ATS-API Steps

**A1 — Resolve slug for each company**

1. Check `profile/target-companies.md` ATS column and Careers URL for a known slug
2. If unknown: guess from company name (lowercase, hyphens) → probe the API endpoint (200 = valid)
3. If probe fails: try 1–2 name variations → if all fail, run ATS Auto-Detection (A3)
4. If Auto-Detection finds a non-Lever/Greenhouse/Ashby platform → escalate to browser-only

**A2 — Call ATS API**

Use the `curl -s | python3` pattern from `ats-api-reference.md`. Filter titles (case-insensitive): `data analyst`, `data engineer`, `analytics engineer`, `analytics manager`, `integration analyst`, `business analyst`, `data integration`, `data migration`, `systems analyst`.

Any posting returned by the API is confirmed live — no Chrome needed for liveness.

**JD content fallback:** If JD field is empty or < 200 chars: navigate to posting URL in Claude in Chrome → `get_page_text`. If Claude in Chrome unavailable → mark ⚠️ Unverified; do not score (see Step 5 JD validation gate).

**A3 — ATS detection for unknown companies**

Run the full detection sequence from **`ats-auto-detection.md`** in this skill folder. That file covers D1–D7, write-back to `profile/target-companies.md`, and announce format.

Route to ats-api if Greenhouse/Lever/Ashby; escalate to browser-only otherwise.

**A4 — Dedup against jobs.csv**

For every posting URL found, check `job-outputs/jobs.csv` `Posting_URL` column (case-insensitive exact match) — skip silently if already tracked. Zero-match companies → update `profile/target-companies.md`: Last Checked = today, Re-check After = today + 3 days.

**A5 — Record new ATS discoveries**

If a slug or board URL was not in `profile/target-companies.md`, update the ATS column and Careers URL.

Progress format: `✓ Neo Financial (Ashby API) — 1 data role found` / `— Maple (Lever API): no open data roles` / `⚠️ Orennia: not on Lever/Greenhouse/Ashby — escalated to browser-only`

------

### Open Search Path — Site: Search + Chrome

Used for: `/scout-ats` only. Searches by role + location keywords without a company slug.

#### Open Search Steps

**O1 — Run site: queries**

Run all three queries:

```
site:jobs.lever.co "data analyst" OR "data engineer" OR "analytics engineer" OR "analytics manager" OR "integration analyst" OR "business analyst" OR "data integration" OR "data migration" OR "systems analyst" "Calgary" OR "Canada"

site:boards.greenhouse.io "data analyst" OR "data engineer" OR "analytics engineer" OR "analytics manager" OR "integration analyst" OR "business analyst" OR "data integration" OR "data migration" OR "systems analyst" "Calgary" OR "Canada"

site:jobs.ashbyhq.com "data analyst" OR "data engineer" OR "analytics engineer" OR "analytics manager" OR "integration analyst" OR "business analyst" OR "data integration" OR "data migration" OR "systems analyst" "Calgary" OR "Canada"
```

Collect all results. Deduplicate on exact URL. Announce: `📥 [N] URLs found.`

**O2 — Dedup against jobs.csv and scout-cache.md**

For each URL, check:

1. **`job-outputs/jobs.csv` `Posting_URL` column** — exact URL match (case-insensitive) → skip silently
2. **Hard-Excluded URL Cache** (`## Hard-Excluded URL Cache (Open Search)` in `scout-cache.md`) — exact URL match + TTL not expired → skip silently; TTL expired → re-verify

Write-back after run: live-but-excluded → Hard-Excluded URL Cache with today's date and 30-day TTL.

**O3 — Pre-Chrome Location Filter**

Scan each search result snippet before Chrome navigation to drop obvious hard excludes and save Chrome calls.

**Hard excludes — drop immediately:**
- Explicit US-only location in snippet (e.g. "New York, NY", "United States only")
- Explicit US work authorisation requirement in snippet
- On-site/hybrid outside Canada

**Flag but keep (proceed to Chrome):**
- Location unclear from snippet
- US-headquartered company with no explicit location signal

Only drop on clear, explicit signals. When in doubt, navigate — Step 4 catches the rest.

Note: `ℹ️ [N] result(s) dropped pre-Chrome — obvious location/auth hard exclude from snippet.`

**O4 — Chrome Liveness Verification + JD Extraction**

For each open search URL that passed deduplication and Step 3:

1. `navigate` to the posting URL
2. Wait 2–3 seconds for JS to render
3. `get_page_text`
4. Classify liveness:
- ✅ Live — posting page loaded with recognisable content; proceed to Step 5 JD validation gate before scoring
- ❌ Dead — 404 or closure language → drop; write a `closed` row to `job-outputs/jobs.csv` with the URL, company, role, source `job-scout`, and today's date. Leave `Contract_Length`, `Search_Terms`, and all other columns blank. Skip if a row already exists for that URL.
- ⚠️ Unverified — blocked or no recognisable content → include with flag; will fail JD validation gate at Step 5

------

### Browser-Only Path — Chrome Navigation

Used for: browser-only companies in `/scout-company` and named runs; ats-api companies escalated after slug detection fails. Requires Claude in Chrome.

**Claude in Chrome unavailable — browser-only and partial-access companies:**
If Claude in Chrome is not connected when browser-only or partial-access companies are due to be swept:
1. For each company, run a web search: `[Company Name] "data analyst" OR "data engineer" OR "analytics engineer" site:[careers domain]` as a signal check only
2. If results suggest possible data roles exist: mark company `⚠️ Claude in Chrome required — roles unverified` in output and scout-cache; log nothing to jobs.csv (no URL, no score)
3. If results confirm no data roles: update Last Checked and Re-check After in target-companies.md as normal; no jobs.csv row
4. Surface all `⚠️ Claude in Chrome required` companies in the Step 10 post-table summary under **Partially investigated**
5. Never score or log a pending row for a browser-only or partial-access company without Claude in Chrome

**B1 — Check profile/target-companies.md:** Known Careers URL → navigate there directly. Re-check After not yet reached → skip silently.

**Persistent access failures:** If a browser-only company cannot be accessed (portal error, SPA with no content, domain blocked) for 2 or more consecutive runs (check Notes in `profile/target-companies.md` for prior failure notes), do NOT skip silently. Append the company to a `⚠️ Persistent access failures` list and surface it in the Step 10 post-table summary:

```
⚠️ Persistent access failures (manual check needed):
- [Company] — [reason; N consecutive runs failed]
```

After surfacing, do not auto-skip on the next run — retry once, then re-flag if still failing.

**B2 — Navigate and render:** `navigate` to careers page; wait 2–3s for JS.

**B3 — Extract job listings:** The approach depends on posting volume:

**Default (small boards — review all):** Navigate to the listings page, extract all job titles via `get_page_text` or DOM, then filter out obviously irrelevant titles (administrative, clinical, trades, etc.) before clicking into each remaining role. Most browser-only companies fall into this category.

**High-volume boards (keyword search mode):** If a company's board has too many total postings to review exhaustively (rough threshold: >50 active roles), use keyword search instead of browsing all jobs. Use the same title terms as the ATS-API filter (Step A2): `data analyst`, `data engineer`, `analytics engineer`, `analytics manager`, `integration analyst`, `business analyst`, `data integration`, `data migration`, `systems analyst`. Companies in this category are noted in `profile/target-companies.md` with their specific search method. Currently: **Alberta Health Services** and its subboards (see AHS entry for exact Chrome MCP search steps).

Try in order for extraction: `get_page_text` → `find` with data role query → `screenshot` (fallback). If page uses a portal (PeopleSoft, Taleo, iCIMS, ADP): note the subdomain; navigate to listings page directly if URL is known; use `find` before clicking through.

**SPA search forms — filling and submitting correctly:** On AJAX-driven search forms, never use `type` + Enter to submit a keyword search. SPAs listen for specific JS events that keyboard simulation doesn't reliably fire — the visible field updates but the search doesn't execute. Instead: use `form_input` to set the field value, then explicitly click the Search/Submit button. This applies to any SPA with a keyword search form (confirmed on Oracle/SelectMinds boards; likely applies to other platforms too).

**SPA troubleshooting (if `get_page_text` returns a shell with no job listings):** Try in order:
1. **Check for embedded ATS:** Run `document.querySelectorAll('script[src], iframe')` and look for known ATS sources (Jobvite, Greenhouse, Lever, Ashby, iCIMS, Workday, SmartRecruiters, Jobvite). If found, extract the board URL and navigate there directly — this is faster and more reliable than scraping the SPA shell. (Example: Enverus careers page embeds a Jobvite iframe; navigating to `jobs.jobvite.com/enverus/jobs` bypasses the SPA entirely.)
2. **Click category/discipline tabs:** If it's a fully custom SPA with no embedded ATS, URL params likely do nothing — the search is client-side. Navigate the UI by clicking category or discipline tabs to trigger rendering. Read `get_page_text` after each click. (Example: Shopify's board requires clicking discipline tabs like "Data" to surface job listings.)
3. **Intercept the API:** After page load, call `read_network_requests` filtering for `job` or `api` to find JSON endpoints the SPA is calling. If a JSON endpoint is found, attempt to call it directly via `mcp__workspace__bash` curl — but note that some platforms (e.g. Oracle/SelectMinds) bind sessions to the browser and return "Invalid Access" on all external requests even with valid session cookies and CSRF tokens. If curl returns "Invalid Access", abandon this approach and fall back to DOM extraction in the browser.
4. **If all three fail:** Mark company as `⚠️ SPA — manual browse required` in targets.md Notes, set Re-check After = today + 14 days, and surface in the post-run summary.

**B4 — Click into matching roles:** For each relevant title, click → `get_page_text` on new tab → close tab.

**PeopleSoft / new-tab portals:** Some portals (e.g. City of Calgary, `calgary.ca/careers.html`) list jobs as plain HTML links that open the JD in a new PeopleSoft tab (`recruiting.[domain].ca/psc/...?SiteId=X&JobOpeningId=Y`). **Privacy filter warning:** `getAttribute('href')` on these links returns `[BLOCKED: Cookie/query string data]` — do NOT try to read the href. Instead: (1) navigate to the listings page, (2) use `find` tool to locate the job title link by text and `left_click` its ref — PeopleSoft opens in a new tab automatically, (3) call `get_page_text` on the new tab to extract the full JD (Job ID is in the URL as `JobOpeningId=XXXXXX`), (4) close the PeopleSoft tab, (5) return to listings tab and repeat. Re-run `tabs_context_mcp` after each close to get the refreshed tab ID. Do NOT attempt to navigate directly to the PeopleSoft portal root.

**B5 — Record portal details:** Update `profile/target-companies.md` ATS column, Careers URL, and Notes with portal type and quirks.

**Dead postings (browser-only path):** If a posting page shows closed/expired/404 state, write a `closed` row to `job-outputs/jobs.csv` with the URL, company, role, source `job-scout`, and today's date. Leave `Contract_Length`, `Search_Terms`, and all other columns blank. Skip if a row already exists for that URL.

Progress format: `✓ City of Calgary (PeopleSoft) — 1 data role found` / `— Health Quality Alberta: no current openings` / `⚠️ WCB: domain permission denied; screenshot only`

Enter shared pipeline at Step 4.

------

### Paste Batch Path (`/paste-batch`)

No web search, no Chrome, no ATS API calls.

**Trigger phrases:** `/paste-batch`, "scan these jobs", "score these postings", "rank these job descriptions", "I have some jobs to paste", or any request to evaluate multiple pasted JDs.

**P1 — Collect JDs**

If content not yet pasted:
```
Paste your job descriptions below, separated by --- or any clear divider. Include the posting URL with each JD. Type done when finished.
```

Accept any reasonable separator. A single pasted JD is valid.

**Wait for done before scoring:** Do not parse or score any JD until the user types **done**. JDs may arrive across multiple messages — collect all of them silently, then run P2 and Step 4+ only after the user confirms. Acknowledge each incoming JD with a brief receipt (e.g. "Got it — paste the next one or type done.") but do not score.

**Source tag:** If the user specifies a source (e.g. `/paste-batch linkedin`), use it as the `Source` field for all postings. Otherwise use `paste-batch`. Individual JDs may override the batch source if clearly identifiable.

**P2 — Parse each JD**

Extract: `TITLE`, `COMPANY` (use "Unknown" if not found), `LOCATION`, `WORK_TYPE`, `EMPLOYMENT_TYPE`, `SALARY`, `REQUIREMENTS`, `RESPONSIBILITIES`, `URL`. Leave fields blank if not extractable — do not guess.

- **URL:** Look for a URL in or immediately around the pasted JD text. If no URL is found for a JD, ask once before scoring that JD: "No URL found for **[Company] — [Title]**. Paste the posting URL (or type `skip` to proceed without one)." If skipped, proceed with a blank URL and note `⚠️ No URL`.
- Duplicate detection: same title + company → score once, note duplicate
- Not a JD: no title or responsibilities → flag; do not score

Enter shared pipeline at Step 4.

---

## Step 3b — Close-Date Check

**Before scoring any listing**, check if the posting has a stated close date. Always resolve "today" against the **user's local timezone (Mountain Time / MT)** before comparing to close dates.

- **Closes today (Apply By = today's MT date):** Still live — treat as normal. Log as `pending` in jobs.csv with `Notes: ⚠️ Closes today — urgent apply`. Surface in the ranked table with a 🔥 flag. **Never skip a listing because its close date matches today.**
- **Already closed (Apply By is a past date in MT):** Skip entirely. Do not log. Note in the scout-cache run entry: `[Role] at [Company] — expired [date], not logged`.
- **No close date stated:** Proceed normally.

This rule applies to **all entry points**: scout-ats, scout-company (ATS-API and browser-only), paste-batch, and scout-link.

## Step 4 — Deduplicate Already-Tracked Roles

Final deduplication checks against jobs.csv
1. **URL match:** check `job-outputs/jobs.csv` `Posting_URL` column (case-insensitive exact match).
2. **Company and Title match:** check for a row with the same company name (case-insensitive) AND same role title (case-insensitive) where the CSV `Date` field is within the last 30 days.

For any match found: log a re-sighting note in scout-cache.md and drop.

Note: `ℹ️ [N] result(s) hidden — already tracked.`

## Step 5 — Run Filter Score

**JD Validation Gate — run before scoring every listing, all paths:**

All three checks must pass. Any failure → mark ⚠️ Unverified, skip filter, proceed to Step 7 with blank Filter_Score and blank Top_Skills.

1. **Character floor:** JD text ≥ 200 chars. Fail if below.
2. **Structural markers:** All three must be present in the extracted text:
   - Job title
   - A description body (responsibilities or duties section)
   - An application CTA ("apply", "submit", "how to apply", or equivalent)
   If any are absent, fail.
3. **Completeness judgment:** Read the extracted text and assess: does this read like a complete job description, or is it a shell, a truncated snippet, a listing-page summary, or a page that failed to render? If it appears incomplete — missing requirements, missing responsibilities, cut off mid-sentence, or consisting only of a title and company blurb — fail.

All three must pass to proceed. A listing that passes all three is considered a **verified full JD** and may be scored.

**Per-company threshold overrides:** Before applying the default ≥6/10 pass threshold, check the company's entry in `profile/target-companies.md` for a `Threshold:` override line. If present, use that threshold instead of the default for this company only. (Example: Alberta Health Services has a ≥5/10 filter and ≥50/100 match threshold due to a referral contact.)

Run the filter (`skills/filter/SKILL.md`) on each listing that passes the validation gate.

---

## Step 6 — Auto Quick Job-Match

**This step is mandatory for every qualifying listing — no exceptions based on rank, score, or perceived priority.**

For every listing that scored **≥6/10** in Step 5, immediately run job-match-quick before moving to the next listing. Do not batch or defer. Do not skip lower-ranked listings because a higher-ranked one already ran. Process each qualifying listing in order, one at a time, before continuing.

**Enforcement checklist — run before proceeding to Step 7:**
After all listings are processed, explicitly verify:
1. Count listings with Filter_Score ≥ 6 from this run's results
2. Count listings where Match_Score was written to `jobs.csv` this session
3. If count (2) < count (1): identify the gap and run auto job-match for any missing listing now before continuing
4. Only proceed to Step 7 when both counts are equal (excluding ⚠️ Unverified and already-applied listings)

**How to run:**
- Use the JD already extracted in this session — do not re-fetch
- Run `job-match-quick` quick mode per `skills/job-match/SKILL.md` (Blocks A + B condensed + Match Score)
- Step 0.5a (save posting) runs as part of job-match
- Step Final of job-match writes Match_Score and Match_Label to `jobs.csv`

**Output format (inline, after each qualifying listing):**

```
⚡ Auto job-match: [Company] — [Role]
📎 Posting saved as `[filename]`
[Block A snapshot — compact]
[Block B — top 2–3 gaps only]
Match Score: [X]/100 — [Label]
Recommendation: [one sentence]
```

**Already-applied flag:** If the listing was flagged `⚠️ already applied` in deduplication, skip auto job-match — a match has already been run or a decision already made.

**Unverified listings:** Do not run auto job-match on ⚠️ Unverified listings — JD content is insufficient for reliable scoring.

**Session continuity:** Auto job-match is session-local — the JD text must be available in the current context window. If the run spans multiple sessions (e.g. context compaction occurred mid-sweep), auto job-match for earlier listings may not have run. At the start of Step 6, check: for any listing scored ≥6/10 that does not yet have a Match_Score in `jobs.csv`, run auto job-match now using the JD URL from the CSV row (re-fetch if needed). Note any catch-up matches in the scout-cache run entry.

**After all listings are processed and the enforcement checklist is satisfied**, continue to Step 7. The ranked table in Step 9 must include the Match Score and Gaps for every listing where auto job-match ran:

| # | Company | Role | Filter Score | Note | Match Score | Gaps | URL |
|---|---------|------|--------------|------|-------------|------|-----|

---

## Step 7 — Update Tracker

**Log all scored roles to `job-outputs/jobs.csv`:**

For every listing that was scored by the filter:
- Status: `pending` if ≥6/10; `skipped` if below 6/10.
- Filter_Score: the /10 score. (Leave blank if JD was not retrieved.)
- Top_Skills: top 3 skills pipe-separated (e.g. `dbt | Snowflake | SQL`). These are the most emphasized in the requirements and responsibilities. (Leave blank if JD was not retrieved.)
- Posting_URL: canonical URL if available; blank if no URL
- Notes: skip reason for below-threshold rows (e.g. "Filter score 4/10 — seniority mismatch"); blank for ≥6/10
- Source: the scout mode.
  - scout-ats
  - scout-company
  - paste-batch
  - Note: scout-link and scout-indeed write their own CSV rows per their own skill files (see `skills/scout-link/SKILL.md` Step 6 and `skills/scout-indeed/SKILL.md` Step 7).

For ⚠️ Unverified listings: log with status `pending`, blank Filter_Score, blank Top_Skills, and Notes: `"⚠️ Unverified — JD not retrieved"`.

---

## Step 8 — Update Memory

`/paste-batch` — skip A and B.
`/scout-ats` — skip A. Write B (Hard-Excluded URL Cache + Scout Cache run entry).
`/scout-link` — handled entirely by `skills/scout-link/SKILL.md`.
`/scout-indeed` — handled entirely by `skills/scout-indeed/SKILL.md`.

**A. `profile/target-companies.md`** (company-scout and named runs only):
- Every company swept: update Last Checked (today), ATS platform, Careers URL if changed
- Browser-only: also update Notes with portal type and navigation quirks if newly discovered
- Zero matches → set Re-check After to today + 3 days; data roles found → clear Re-check After
- **Browser-only companies:** Apply the same Re-check After rule regardless of ATS type. Every browser-only company swept this run gets Last Checked = today and Re-check After = today + 7 days if zero data roles found (browser-only boards change less frequently than APIs). Data roles found → clear Re-check After (set the field to blank/empty string — do not write a date).
- **Implementation note:** `target-companies.md` uses em-dashes and long lines that cause the Edit tool to fail on multi-line replacements. Always use a Python/bash script (string `.replace()` per line) for bulk Last Checked / Re-check After updates — never attempt a single multi-line Edit call for more than one row at a time.

**B. `scout-cache.md`:**

**Hard-Excluded URL Cache** (`## Hard-Excluded URL Cache (Open Search)`) — open search only:
- Live but hard-excluded URLs → append with today's date and 30-day TTL

**Scout Cache** (`## Scout Cache`) — all modes except `/paste-batch`. Prepend a new entry; never overwrite:

For `/scout-ats` and `/scout-company`:
```
### Run: [YYYY-MM-DD] | Mode: [Open search / Company sweep / Named] | ATS-API: [N] | Browser-Only: [N] | Unknown: [N]
Live results (Canada-eligible): [N] | Location-excluded: [N] | Dead dropped: [N] | Borderline (below threshold): [N]
Notes: [platform escalations, no-role companies, permission blocks, new portal discoveries, ATS changes]
```

---

## Step 9 — Output the Ranked Table

**Header block:**
```
─────────────────────────────────────────
🔍 Job Scout Results
Mode: [Open search / Company sweep / Named companies]
[ATS-API: [N] | Browser-Only: [N] | Unknown→detected: [N]]   ← omit for open search
Live listings: [N] | Location-excluded: [N] | Dead dropped: [N]
Ranked by: Filter Score
─────────────────────────────────────────
```

**Ranked table:**

| # | Company | Role | Filter Score | Note | Match Score | Gaps | URL |
|---|---------|------|--------------|------|-------------|------|-----|
| 1 | [Company] | [Title] | 🟢 9/10 | [1–2 phrase reason for score] | 78 — Good odds | [top 2–3 gaps or —] | [link] |

**Sorting:**
- `/scout-company`: sort by company rank from `company-ranking.md` (Tier 1 first, then row order within tier); Filter Score shown but does not affect sort
- All other modes: sort by Filter Score descending; ties broken by location preference (Calgary first, Remote second, On-site last)

**Table rules:**
- Always include the direct posting URL as a markdown hyperlink; paste batch with no URL → show `pasted`
- ⚠️ Unverified results shown but noted
- Note: always populate — 1–2 phrases explaining the Filter Score for every row (e.g. "Exact title match; all required tools present", "Good role fit; missing dbt", "Title mismatch — PM role", "Requires secret clearance")
- Match Score: blank if auto job-match did not run (e.g. ⚠️ Unverified listings)
- Gaps: top 2–3 gaps from Block B of job-match; `—` if job-match did not run
- Companies with no open data roles: `ℹ️ No matching roles: [list]` (discovery modes only)
- Score colour: 🟢 9–10 | 🟡 7–8 | 🟠 6 | 🔴 below 6

---

## Step 10 — Post-table Summary

```
─────────────────────────────────────────
📊 Scout Summary

Top pick:     [Job Title] at [Company] — [Score]/10
              [One sentence: why strongest match]

Worth a look: [Job Title] at [Company] — [Score]/10
              [One sentence: what makes it interesting]

Skip:         [N] roles scored below 6/10

Fully swept:       [Company], [Company], ... (ATS-API confirmed or Claude in Chrome navigation completed)
Partially investigated: [Company] — [reason, e.g. Claude in Chrome required — roles unverified], ...
                   (Omit section if none)
Skipped:           [Company] (Re-check After [date]), ... (Re-check After not yet reached)
                   (Omit section if none)

─────────────────────────────────────────
```

---

## Output Rules

- Never search broad job boards
- Never include dead listings (404, closure language, absent from API = dropped)
- Never fabricate listings or scores — score only from actual JD text; mark ⚠️ Partial JD or ⚠️ Unverified if JD unavailable
- Source field is mandatory in every CSV row — set per mode as defined in Step 7
- Job_ID field: leave blank for all job-scout rows — only SI Systems portal rows use this field
- `/paste-batch` — no web search, no Chrome; never fetch URLs unless the user explicitly provides one and asks
- ADP WorkforceNow → browser-only only; never attempt via web_fetch (requires JS-rendered cid GUID)

