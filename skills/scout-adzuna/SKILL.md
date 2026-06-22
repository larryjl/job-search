---
name: scout-adzuna
description: "Broad Canadian market job search via the Adzuna API. Two entry points: /scout-adzuna or /scout-adz (fetch and process up to 50 jobs from the Adzuna queue), /scout-adzuna drain (drain the full queue via sequential sub-agents, 50 items/batch)."
---

# Scout Adzuna

Broad Canadian market search via the Adzuna API. Does NOT search broad job boards (Indeed, Workopolis, Randstad) and does NOT sweep company ATS boards — use `/scout-company` for those.

**Pipeline entry points:**
- `/scout-adzuna` → Steps Z1–Z2 (fetch + queue), then immediately triggers drain via `adzuna-queue-drain.md`
- `/scout-adzuna drain` → skips fetch; reads and executes `adzuna-queue-drain.md` directly (use to resume an interrupted drain without re-fetching)

---

## Step 0 — Load Context

Silently load before any searching:

**A. Targets** from `profile/targets.md`

**B. Scout cache:**
Read `scout-cache.md` before any searching begins. Use the Verified Postings Cache and Dead/Hard-Excluded caches for dedup at Step Z4b — drop any URL already present. Always run fresh (no cache-age prompt for Adzuna mode).

---

## Step 1 — Entry Point Detection

### `/scout-adzuna` (alias: `/scout-adz`)
Announce: `🔍 Starting Adzuna broad search...`
Check prerequisites first (credentials + Chrome), then run Z1–Z2 to fetch and populate the queue, then trigger the drain (Z3).

### `/scout-adzuna drain`
Read and execute `skills/scout-adzuna/adzuna-queue-drain.md` exactly.

---

## Step 2 — Domain Access Gating

Check `.claude/config/domains.md` under `## scout-adzuna` before accessing any domain via Chrome or web fetch. For unapproved domains: output `🔒 Domain access request: [domain]`, ask permission. Approved → add to whitelist, proceed. Denied → skip.

Domains needed: `api.adzuna.com`, `www.adzuna.ca`, and any resolved source domains (company ATS or careers pages).

---

## Step 3 — Adzuna Path

Requires: Python 3, Adzuna credentials in `.claude/config/api-keys.md`, Claude in Chrome.

**Prerequisites:**

Credentials — check `.claude/config/api-keys.md` for `## Adzuna` with `app_id` and `app_key`. If missing:
```
⚠️ Adzuna credentials not found in .claude/config/api-keys.md.
Sign up free at https://developer.adzuna.com.
Add app_id and app_key under ## Adzuna, then re-run /scout-adzuna.
```

Chrome — if not connected, ask: "Results cannot be verified without Chrome. Continue without Chrome? (yes / connect first)"

**Call count:** Each `/scout-adzuna` run makes 12 API calls (6 terms × 2 locations).

---

**Z1 — Queue and staleness check**

Read `.claude/memory/raw-results-queue.json` → `adzuna` section.

Before processing, scan `adzuna.items` for entries where `run_date` is more than 3 days ago and `processed` is false. Flag these as expired:
```
⚠️ [N] queued item(s) expired (>3 days old) — dropped without processing: [Company — Title, ...]
```
Mark expired items `processed: true` with `expired: true`.

Count remaining unprocessed items after expiry:

- If `last_run` is null or more than 3 days ago → **fresh start**: reset `last_page` to 0, drop all items from `adzuna.items` where `run_date` is more than 14 days ago (or `run_date` is absent), retain the rest (processed or not) for pre-Chrome ID dedup, proceed to Z2.
- If unprocessed items remain → **skip Z2**: go directly to Z3 to process from the existing queue. Do not fetch a new page.
- If no unprocessed items remain and `last_run` is within 3 days → **fetch next page**: proceed to Z2.

---

**Z2 — Fetch next page into queue**

Increment `last_page` by 1. Run:

```bash
python3 <project_root>/skills/scout-adzuna/adzuna_search.py --output /tmp/adzuna_results.json --page <last_page>
```

12 searches: 6 role terms × 2 locations (Calgary, Canada remote), 50 results per call. Script deduplicates on Adzuna job ID, applies hard excludes (category whitelist, US location/auth signals), flattens and enriches results, and writes to `/tmp/adzuna_results.json`.

After reading the output file, announce:
```
📦 Raw: [N] | Deduped: [N] | Hard-excluded: [N] | Candidates: [N]
📄 Page [last_page] of ~[ceil(max(total_available across all searches) / 50)] — [max(total_available)] total Adzuna matches across all search terms
```
Use `max(search["total_available"] for search in searches)` as the best estimate of pool size (each term returns its own count; the max approximates the broadest reach). Omit the page line if all `total_available` values are 0 or null.

Read `/tmp/adzuna_results.json` (processed results — not raw API output). For each result, add to `adzuna.items` as:
```json
{
  "id": "...",
  "run_date": "<today>",
  "page": <last_page>,
  "processed": false,
  "title": "...",
  "company": "...",
  "location": "...",
  "salary_min": null,
  "salary_max": null,
  "salary_display": "...",
  "redirect_url": "...",
  "created": "...",
  "search_terms": ["data analyst", "business analyst"]
}
```

`search_terms` — deduplicated list of role terms (what keywords only, no location) that returned this job ID in this fetch. Populated by the script; written to the `Search Terms` column of the Verified Postings Cache in `scout-cache.md` for overlap analysis.

Skip items that already exist in `adzuna.items` with the same `id` (dedup on Adzuna `id` field — catches both duplicate results within this fetch across multiple search terms/locations, and jobs already processed in prior runs). Do NOT dedup on company+title — a repost or a second role with the same title at the same company will have a different `id` and must flow through. Announce: `📥 Added [N] new items to queue ([M] already present — skipped). Queue depth: [total unprocessed].`

Update queue file: set `last_page`, `last_run` to today.

---

**Z3 — Trigger drain**

After Z2 completes (queue populated), immediately read and execute `skills/scout-adzuna/adzuna-queue-drain.md` exactly. Do not pull or process items directly in the parent session — all processing happens in sub-agents spawned by the drain.

Output before handing off:
```
📥 Queue populated. Triggering drain...
```

The drain handles all remaining steps (Chrome verification, filter scoring, auto job-match, CSV writes, cache updates, ranked table output). Steps Z3b, Z4, and Z4b below are **sub-agent reference sections** — they are executed inside `adzuna-queue-batch.md`, not by the parent directly.

---

**Z3b — Pre-Chrome title + location filter** *(sub-agent only — executed in adzuna-queue-batch.md)*

Before spending Chrome calls, scan each item's queue fields. Three signals are reliable without Chrome:

**1. `title` field (fully reliable):** Drop immediately if the title unambiguously falls outside all target roles — e.g. Incident Handler, Customer Success Manager, SCADA Developer, ML Engineer, Data Scientist, Engineering Intern, Game Designer, Software Developer, Records Manager, VP/C-suite. When in doubt (e.g. bare "Analyst"), navigate and read the JD.

**2. `location` field (reliable for explicit cities):** The Adzuna `location` field is a city/region string (e.g. "Montréal, Québec", "Regent Park, City of Toronto", "Vancouver, Greater Vancouver"). Drop if the location is an explicit non-Calgary, non-Alberta Canadian city AND the title gives no remote signal. Do NOT drop on "Canada" or "Ontario" alone — work model is unknown without the JD.

**3. `salary_min`/`salary_max` fields (reliable when populated):** Drop if both values are present and `salary_max` is clearly below the CAD 80K floor. Skip this check if both fields are null — salary is often absent from the API response.

**`description` snippet is unreliable for pre-filter** — the truncated ~200-500 char API snippet rarely reveals work model or location constraints. Do not rely on it for location/remote decisions; navigate to the full JD instead.

Log pre-Chrome drops as: `ℹ️ [N] dropped pre-Chrome — title/location/salary hard exclude.`

**Near-duplicate detection:** If two items in the batch share the same company name and near-identical title (e.g. same title, adjacent Adzuna IDs), navigate to both but note the likely duplicate — score once and flag the second as `⚠️ Near-duplicate — same role, different ID`.

---

**Z4 — Chrome redirect resolution + liveness + JD** *(sub-agent only — executed in adzuna-queue-batch.md)*

Process each item **one at a time** — do not batch the Apply/redirect sequence across tabs. JD extraction in step 1 can be batched, but steps 2–4 must be serial per item.

**Step 1 — Navigate and extract JD**

`navigate` to `redirect_url` → wait 2–3s → `get_page_text` (extracts JD; page is still the Adzuna detail page at this point)

**Step 2 — Source liveness check**

- **EASY APPLY check first:** If the Adzuna listing shows an "EASY APPLY" label, the application stays on Adzuna and there is no source redirect. Mark as `⚠️ Source unverified — EASY APPLY (stays on Adzuna)` and skip to Step 3. Do not click Apply. **However:** the JD on the Adzuna page itself may still be complete — run `get_page_text` on the Adzuna page before skipping to Step 3 and use it for filter scoring. Auto job-match still runs if the JD is sufficient (≥200 chars of responsibilities/requirements) — the unverified flag does not block scoring.
- `find` "Apply for this job" button → `left_click` it → wait 3s (modal needs time to render)
- Adzuna fires an email alert modal with a "No, thanks" link and a "take me to the job" link. **Do not click these links directly** — they open in a new tab outside the MCP group. Instead, use `javascript_tool` to find the "take me to the job" link and force in-place navigation:
  ```js
  const link = Array.from(document.querySelectorAll('a')).find(a => a.textContent.includes('take me to the job'));
  if (link) { window.location.href = link.href; 'navigating' } else { 'no link found' }
  ```
  Wait 3s → `get_page_text` → note resolved URL.
- **If no modal appears** (posting redirects directly on first click): note the resolved URL and `get_page_text` — skip the JS step.
- **If no Apply button found**: mark `⚠️ Source unverified — Apply button absent`; skip to step 3.
- **Jobillico redirect:** If the resolved URL is a jobillico.com page, a cookie consent popup will appear. Click the consent/accept button before attempting `get_page_text` — otherwise the page content will be blocked.

**Step 3 — Classify resolved destination**

- **✅ Verified source-live:** Resolved URL is the company's own ATS or careers domain (Workday, Lever, Greenhouse, Ashby, Dayforce, BambooHR, or company careers page) and the page shows an active job posting or Apply CTA. Record the company URL as the canonical posting URL — use it in all downstream steps (cache, CSV) instead of the Adzuna URL.
- **❌ Dead (source-closed):** Resolved URL shows a closed/expired/404 page, "this job is no longer available", or ATS empty/error state. Drop from results; add to Dead URL Cache using the Adzuna `redirect_url`.
- **⚠️ Source unverified — third-party distributor:** Resolved URL is a job distribution aggregator (dejobs.org, recruitingsite.com, and similar) rather than the company's own domain or a known ATS. The job may still be live but the source is not authoritative. Keep in results with flag; use the distributor URL as canonical but note the limitation.
- **⚠️ Source unverified:** Redirects back to Adzuna, to another job board, or to a page requiring login. Keep in results with flag; use Adzuna URL as canonical.

**Step 4 — Capture expiry/deadline**

After `get_page_text` on the source page, scan for expiry or deadline language (e.g. "apply by", "closes", "expires", "end date", "posting end date"). If found, extract the date and add it to the Notes field in the CSV and the cache entry.

Log inline: `✓ [Company] — [Role] → ✅ Source-live | resolved: https://...` or `✗ [Company] — [Role] → ❌ Source-closed`

---

**Z4b — Verified Postings Cache dedup + jobs.csv deduplication** *(sub-agent only — executed in adzuna-queue-batch.md, runs after Z4 completes)*

For each item with a resolved URL, check Verified Postings Cache (resolved URL, date ≤ 3 days): dead → drop silently; verified with score → use cached score; unverified → keep. No match → proceed to check 2.

Source tag `scout-adzuna` is passed through to CSV writes and cache write-back inside each sub-agent batch.

*(End of Z4b — sub-agent returns to adzuna-queue-batch.md for CSV writes and cache updates.)*

---

## Step 4 — Deduplicate Already-Tracked Roles *(sub-agent only)*

Final deduplication checks against jobs.csv:
1. **URL match:** check `job-outputs/jobs.csv` `Posting_URL` column (case-insensitive exact match).
2. **Company and Title match:** check for a row with the same company name (case-insensitive) AND same role title (case-insensitive) where the CSV `Date` field is within the last 30 days.

For any match found: log a re-sighting note in scout-cache.md and drop.

Note: `ℹ️ [N] result(s) hidden — already tracked.`

---

## Step 5 — Run Filter Score *(sub-agent only)*

Run the filter (`skills/filter/SKILL.md`) on each listing.

---

## Step 6 — Auto Quick Job-Match *(sub-agent only)*

For every listing that scored **≥6/10** in Step 5, immediately run job-match-quick before moving to the next listing.

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

**After all listings are processed**, continue to Step 7 as normal. The ranked table in Step 9 should include the Match Score and Gaps for any listing where auto job-match ran:

| # | Company | Role | Filter Score | Note | Match Score | Gaps | URL |
|---|---------|------|--------------|------|-------------|------|-----|

---

## Step 7 — Update Tracker *(sub-agent only)*

**Log all scored roles to `job-outputs/jobs.csv`:**

For every listing that was scored by the filter:
- Status: `pending` if ≥6/10; `skipped` if below 6/10.
- Filter_Score: the /10 score. (Leave blank if JD was not retrieved.)
- Top_Skills: top 3 skills pipe-separated (e.g. `dbt | Snowflake | SQL`). These are the most emphasized in the requirements and responsibilities. (Leave blank if JD was not retrieved.)
- Posting_URL: canonical URL if available; blank if no URL
- Notes: skip reason for below-threshold rows (e.g. "Filter score 4/10 — seniority mismatch"); blank for ≥6/10
- Source: `scout-adzuna`

For ⚠️ Unverified listings: log with status `pending`, blank Filter_Score, blank Top_Skills, and Notes: `"⚠️ Unverified — JD not retrieved"`.

---

## Step 8 — Update Memory *(sub-agent only)*

Skip A. Write B (Verified Postings Cache + Scout Cache run entry) and C (queue file).

**B. `scout-cache.md`:**

**Verified Postings Cache** (`## Verified Postings Cache`):

| Company | Role | URL | Source | Status | Filter Score | Cached | Search Terms |

- Append new rows; update existing rows on re-verification (match on URL); never delete rows
- ✅ Verified: URL + score + date. ❌ Dead: Dead status + date. ⚠️ Unverified: date, re-attempted next run.
- `Search Terms`: comma-separated role terms from `search_terms` (e.g. `data analyst, business analyst`).

**Scout Cache** (`## Scout Cache`) — prepend a new entry; never overwrite:

```
### Run: [YYYY-MM-DD] | Mode: Adzuna | Page: [N] | Searches: data analyst | data engineer | analytics engineer | analytics manager | business analyst | data integration | Locations: Calgary + Canada remote
New to queue: [N] | Processed this run: [N] | Queue remaining: [N] | Expired dropped: [N] | Chrome verified: [N] | Dead dropped: [N] | Unverified: [N]
```

**C. `raw-results-queue.json`:**

Write back the full updated queue file after each run. This is the source of truth for queue state — always write the complete file, not partial updates. Fields to ensure are current:
- `adzuna.last_page`, `adzuna.last_run`, `adzuna.items` (with `processed` flags updated)

---

## Step 9 — Output the Ranked Table *(drain parent only — executed in adzuna-queue-drain.md after all batches complete)*

**Header block:**
```
─────────────────────────────────────────
🔍 Job Scout Results
Mode: Adzuna
Searches: data analyst | data engineer | analytics engineer | analytics manager | business analyst | data integration | Locations: Calgary + Canada remote
Live listings: [N] | Location-excluded: [N] | Dead dropped: [N]
Ranked by: Filter Score
⚠️ Source: Adzuna API — postings not from tracked company boards.
─────────────────────────────────────────
```

**Ranked table:**

| # | Company | Role | Filter Score | Note | Match Score | Gaps | Location | URL |
|---|---------|------|--------------|------|-------------|------|----------|-----|
| 1 | [Company] | [Title] | 🟢 9/10 | [1–2 phrase reason for score] | 78 — Good odds | [top 2–3 gaps or —] | [City, Province / Remote / Hybrid — confirmed only] | [link] |

**Sorting:** sort by Filter Score descending; ties broken by location preference (Calgary first, Remote second, On-site last).

**Table rules:**
- Always include the direct posting URL as a markdown hyperlink
- ⚠️ Unverified results shown but noted
- Note: always populate — 1–2 phrases explaining the Filter Score for every row (e.g. "Exact title match; all required tools present", "Good role fit; missing dbt", "Title mismatch — PM role", "Requires secret clearance")
- Match Score: blank if auto job-match did not run (e.g. ⚠️ Unverified listings)
- Gaps: top 2–3 gaps from Block B of job-match; `—` if job-match did not run
- Location: city/province from the JD, plus work model (Remote / Hybrid / On-site) **only if explicitly stated in the JD**. Do not infer work model from city alone. If unconfirmed, just show the city/province (e.g. "Calgary, AB" not "Calgary, AB (remote unconfirmed)").
- Score colour: 🟢 9–10 | 🟡 7–8 | 🟠 6 | 🔴 below 6

---

## Step 10 — Post-table Summary *(drain parent only — executed in adzuna-queue-drain.md after all batches complete)*

```
─────────────────────────────────────────
📊 Scout Summary

Top pick:     [Job Title] at [Company] — [Score]/10
              [One sentence: why strongest match]

Worth a look: [Job Title] at [Company] — [Score]/10
              [One sentence: what makes it interesting]

Skip:         [N] roles scored below 6/10

─────────────────────────────────────────
```

---

## Output Rules

- Never search broad job boards
- Never include dead listings (404, closure language — dropped)
- Never fabricate listings or scores — score only from actual JD text; mark ⚠️ Unverified if JD unavailable
- Source field `scout-adzuna` is mandatory in every CSV row
- Job_ID field: leave blank for all scout-adzuna rows — only SI Systems portal rows use this field
- Adzuna liveness = Chrome after redirect resolution; never use the `adzuna.ca/details/...` URL as the final URL
