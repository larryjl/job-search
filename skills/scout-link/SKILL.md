---
name: scout-link
description: "Scrapes a live LinkedIn search results page via Chrome. Harvests each card's job ID by clicking the card and reading the URL's currentJobId (the DOM no longer exposes IDs as attributes post-RSC-migration), then fetches JDs via the Voyager jobPostings API. Both clicking and the JD fetch work with the tab backgrounded, so it runs unattended. Produces a ranked output table. Requires Claude in Chrome and an active LinkedIn login. Processes one page at a time (25 cards); auto-advances if all cards are duplicates."
---

# Scout Link

Scrapes a live LinkedIn search results page via Chrome. Requires Claude in Chrome and an active LinkedIn login.

**Trigger phrases:** `/scout-link`, "scout linkedin", "scrape linkedin jobs", or any request to pull jobs from a LinkedIn search page.

---

## Step 0 — Load Context

Silently load before starting:
- `profile/targets.md`
- `profile/skills-inventory.md`

---

## Step 1 — Setup and Navigation

**Chrome check:** If Claude in Chrome is not connected → stop and output:
```
⚠️ Claude in Chrome is required for scout-link. Connect the extension and re-run.
```

**Degraded render check (initial navigation only):** After navigating to the jobs page, confirm the page has loaded:
- `document.body.innerText.length` must be > 3000 chars. If < 3000 → stop and output: `⚠️ LinkedIn page not fully loading (< 3000 chars). Re-run scout-link when LinkedIn renders normally.`

**No workarounds.** Do not attempt alternative URL patterns, `read_page`, `web_fetch`, or processing partial card metadata. Stop cleanly and let the user re-run.

**Mode:** Default is `preferences`. Set `SCOUT_LINK_MODE = preferences` unless the user explicitly specifies `top-applicant` in their command. Do not prompt the user to choose.

**URL input:**
- No URL given, or `linkedin.com/jobs` given → navigate to `https://www.linkedin.com/jobs/`, wait 3s for render, then:
  - **Verify starting URL:** Confirm the current URL is `https://www.linkedin.com/jobs/` (or `linkedin.com/jobs/`). If it has resolved to a job posting URL (`/jobs/view/...`) or a search results URL, navigate back to `https://www.linkedin.com/jobs/` and wait again before proceeding.
  - Both sections render asynchronously via JS and will not appear in page text immediately even if visible in the viewport. The 3s wait above is the primary render gate — do not call `get_page_text` to verify section presence before it completes. Scroll behaviour per section is handled in the branches below.
  - Branch on `SCOUT_LINK_MODE`:

  **`top-applicant`:**
  - Scroll down 2–3 ticks and wait 3s to bring the section into view.
  - Call `get_page_text` and confirm **"Jobs where you'd be a top applicant"** appears. If not: scroll further, wait 3s, retry. If still not found after two attempts: output `⚠️ "Jobs where you'd be a top applicant" section not visible. This section requires a LinkedIn Premium account and an active profile. Re-run scout-link when the section is visible.` and stop.
  - Use `javascript_tool` to click the "Show all" link scoped to that section:
    Run `js/click_show_all_top_applicant.js` via `javascript_tool`
    Wait 3s for results to load.
  - **Verify landing URL:** Confirm the URL now contains `origin=QUALIFICATION_LANDING`. If it does not, or if `javascript_tool` returned `'not found'`, scroll down 3 ticks, wait 3s, then try clicking the visible "Show all →" button by coordinate (screenshot first to locate it). If still failing, stop and output `⚠️ Could not navigate to top applicant results. Re-run scout-link when LinkedIn renders normally.`

  **`preferences` (default):**
  - Call `get_page_text` and confirm **"Jobs based on your preferences"** appears. If not: wait 3s and retry once. If still not found after two attempts: output `⚠️ "Jobs based on your preferences" section not visible. Re-run scout-link when the section is visible.` and stop.
  - Use `javascript_tool` to click the "Show all" link scoped to that section:
    Run `js/click_show_all_preferences.js` via `javascript_tool`
    Wait 3s for results to load.
  - **Verify landing URL:** Confirm the URL has changed from `https://www.linkedin.com/jobs/` to a search results URL. Post-RSC-migration this is `/jobs/search-results/` (the old `/jobs/search/` path is no longer used); accept any URL containing `/jobs/search-results/`, `/jobs/search/`, or a `?` query string with `origin=PREFERENCES_LANDING`. If it has not changed, or if `javascript_tool` returned `'not found'`, scroll down 3 ticks, wait 3s, then try clicking the visible "Show all →" button by coordinate (screenshot first to locate it). If still failing, stop and output `⚠️ Could not navigate to preferences results. Re-run scout-link when LinkedIn renders normally.`

**Page offset (optional):** If the user specified a page number (e.g. "skip to page 3"), apply it after the full mode navigation above is complete and the search results URL is confirmed. Calculate the offset as `(N-1) * 25` and inject it into the current URL:
Run `js/navigate_to_offset.js` via `javascript_tool` (replace `[OFFSET]` with the calculated value)
Wait 3s for the page to render. The full mode navigation (clicking "Show all", verifying landing URL) always runs first — the offset is applied after the search context is established, never before.

**Login check:** After navigation, call `get_page_text`. If the page contains login/sign-in prompts and no job card content → output:
```
⚠️ LinkedIn login required. Log in to LinkedIn in Chrome and re-run /scout-link.
```
and stop.

---

## Step 2 — Parse Job Card List

> **LinkedIn RSC migration (verified 2026-06-21):** The job search results page is server-rendered via React Server Components. The card list no longer carries `data-occludable-job-id` (or any `data-job-id`) attributes, and the job IDs are not statically present in the DOM or anchor hrefs. Do not query `data-occludable-job-id` — it returns nothing. Each card IS a clickable `div[role="button"]`; **clicking a card updates the page URL's `currentJobId` parameter to that card's job ID**. We harvest IDs by clicking each card and reading `currentJobId` (Step 2b), then fetch the JD via the Voyager API (Step 4).
>
> **Unattended-safe (verified 2026-06-21):** The click-walk and the JD fetch both work when the tab is backgrounded/hidden (`document.hidden === true`). Clicking updates the URL (a DOM/history operation, not a throttled render) and the JD comes from an authenticated `fetch()`. Neither needs tab focus — this is what makes the scheduled run work unattended. Do NOT add tab-focus prompts or visibility workarounds.

### Step 2a — Render and identify cards

**Scroll to render all cards:** Scroll the results panel to force all cards to render, then return to the top. Use `javascript_tool`:
Run `js/scroll_containers.js` via `javascript_tool`

**Card selector:** the job cards are `div[role="button"]` inside `<main>` whose text is a multi-line block (title / company / location). Filter to these:
Run `js/count_job_cards.js` via `javascript_tool`
This count is `[N]` (expect up to 25). Per card, the text lines give `title` (first non-empty line), `company` (next), and `location` + `work_type` (infer Remote/Hybrid/On-site from the parenthetical). Ignore "Promoted" / "Viewed" / "Easy Apply" badge lines when parsing.

Announce: `📋 Found [N] job cards on this page.`

### Step 2b — Harvest job IDs by clicking each card

The job ID is required for the JD fetch (Step 4), the canonical URL, and CSV dedup. Click each card and read the resulting `currentJobId` from the URL. The click updates the URL asynchronously (~130ms typical, measured 68–174ms) — it does **not** load the JD, so a short poll is enough; do not use a multi-second wait. A full 25-card walk takes ~4s. Run the whole walk in **one** `javascript_tool` call (the loop must be a single async block so timing is consistent):

Run `js/harvest_job_ids.js` via `javascript_tool`

Then read the full pairs with a second call: `JSON.stringify(window.__cardWalk.results)`.

Build `CARD_LIST` from `window.__cardWalk.results` as `{ title, company, location, work_type, id }` per card (merge in location/work_type parsed from the card text lines).

**Integrity checks:**
- If `uniqueIds < total` (a duplicate ID appeared), the poll likely missed a change on one card. Re-run the walk once. If a duplicate persists, mark the **second** occurrence `⚠️ Unverified — ambiguous ID` rather than processing it twice.
- Any card with `id === null` after the walk → mark `⚠️ Unverified — could not resolve job ID`. Do NOT fetch a JD for it; do NOT guess an ID.
- Each `id` must be an 8+ digit number. Anything else → treat as null/Unverified.

Announce: `🔗 Resolved [uniqueIds]/[total] job IDs.`

---

## Step 3 — Card-Level Smart Skip (Pre-Fetch)

> **Ordering:** The click-walk in Step 2b harvests every card's ID in a single pass, so by the time you reach Step 3 each card in `CARD_LIST` already has its `id`, title, and company. Apply all skip checks below (card-skip cache, CSV URL match, CSV company+title match, title blocklist, location blocklist) here, before any JD fetch in Step 4. The CSV URL match uses the harvested `id`; the others use card text. Skipping a card here means "don't fetch its JD" — the click to harvest its ID already happened in 2b and is unavoidable.

For each card in `CARD_LIST`, apply the following checks in order before making any JD fetch. Either check failing → skip without fetching. If uncertain, allow through.

**Dedup check:** Run checks in order, stopping at first match:
- **Card-skip cache:** check `### scout-link card skips` table in `.claude/memory/scout-cache.md` for a row with matching company + title within the last 60 days → drop silently.
- **CSV URL match:** check `Posting_URL` column for any URL containing the job ID (e.g. a `Posting_URL` ending in `/view/[jobId]/`).
- **CSV company+title match:** check for a CSV row with the same company (case-insensitive) AND same role title (case-insensitive) where `Date` is within the last 30 days.

For any CSV match: status `closed` or `skipped` → drop silently. Any other status → log `⚠️ [Company] — [Title] → already in CSV (status: [status], date: [date]); skipping`.

**Title blocklist** (case-insensitive substring match on card title — skip if any term matches):
⚠️ Exception: "Developer" qualified by a data domain (SQL, ETL, BI, Data, Analytics) does NOT trigger the "Software Developer" block — e.g. "SQL Developer", "ETL Developer", "BI Developer" all pass.
- Software Engineer
- Software Developer
- Data Scientist
- PowerBuilder
- GIS
- SAP
- Full Stack
- Backend
- Frontend

**Location blocklist** (inferred from the card location string):
- Any city other than Calgary + `(On-site)` → skip
- Any location outside Alberta + `(Hybrid)` → skip
- Alberta cities other than Calgary + `(Hybrid)` → allow
- Remote (any location) → allow
- No location or ambiguous → allow through

Skipped cards are **included in the output table** (Step 8) with `⛔ title-skip` or `⛔ location-skip` in the Filter Score column.

**Queue title-skipped cards for dismiss confirmation:** For each **title-skip** card only, add it to a `DISMISS_QUEUE` list. Do not attempt any dismiss clicks during the run. The queue is presented to the user at the end of the run (Step 9) for confirmation before any dismissals happen.

**Location-skip cards are NOT queued for dismissal** — dismissing these would negatively affect LinkedIn's recommendation algorithm.

`DISMISS_QUEUE` entry format: `{ company, title, skip_reason }` (e.g. `{ "Dasro Consulting Inc.", "SAP Data Analyst", "title-skip" }`).

Announce: `⏭️ [N] card(s) skipped (title or location) — [N] title-skip(s) queued for dismiss confirmation.`

---

## Step 4 — API Fetch and Extract JDs

**Stay on the search results page throughout this entire step.** Do not navigate away.

For each card that passed Step 3, fetch the full job data via the Voyager API from within the page context. This call inherits the user's LinkedIn session cookies and requires no tab focus or DOM rendering.

**Read the CSRF token once** before the loop:
Run `js/extract_csrf.js` via `javascript_tool`

**Per-card API fetch:**
Run `js/fetch_job_posting.js` via `javascript_tool` (replace `[JOB_ID]` and `[CSRF]` with current values)

**Error handling:**
- Non-200 response → log `⚠️ API error [status] for [Company] — [Title] (ID: [jobId]); skipping` and proceed to next card.
- 401 → stop entire run immediately: `⛔ LinkedIn session expired. Log in to LinkedIn in Chrome and re-run /scout-link.`
- Rate limiting (429) → wait 5s and retry once. If still 429, stop and report.

**Age skip (post-fetch):** Convert `listedAt` (Unix ms) to a date. If `new Date(listedAt) < today − 14 days` (strictly more than 14 days old) → skip with `⛔ age-skip`. Exactly 14 days old passes. Add to card-skip cache (Step 7) but NOT to DISMISS_QUEUE.

**All-duplicate check:** If every card on the current page was a title-skip, location-skip, dedup, or age-skip — i.e. zero new JDs were extracted and scored — automatically advance to the next page. Prefer incrementing the `start` offset in the URL by 25 (most reliable post-RSC), falling back to a "Next" button click if present. Use `javascript_tool`:
Run `js/advance_to_next_page.js` via `javascript_tool`
Wait 3s, then restart from Step 2. Continue until at least one new JD is found or no "Next" button exists: `📭 All pages exhausted — no new roles found.`

**JD extraction:** Use `d?.description?.text` directly from the API response — no DOM selectors, no anchors, no chunking needed. If `desc` is null or empty → log `⚠️ [Company] — [Title] (ID: [jobId]) → no JD in API response; skipping`.

**Run filter** (from `skills/filter/SKILL.md`) on `desc` for each card with a non-empty JD before moving to the next card.

Construct canonical URL: `https://www.linkedin.com/jobs/view/[jobId]/`

Log inline progress: `✓ [Company] — [Title] (ID: [jobId]) → JD extracted ([N] chars)` / `↩️ [Company] — [Title] → CSV dedup, skipping` / `⛔ [Company] — [Title] → age-skip` / `⚠️ [Company] — [Title] → API error or no JD`

---

## Step 5 — Save Posting + Auto Job-Match

For every card that scored ≥6/10 in 4:

1. **Save the job posting** — run `skills/save-job-posting/SKILL.md` using the JD already extracted in this session. Do not re-fetch. Confirm: `📎 Posting saved as [filename]`.
2. **Run job-match quick mode** per `skills/job-match/SKILL.md` immediately after saving. Skip the auto-save step inside job-match (Step 0.5a) — the posting was already saved in step 1 above.

Process each qualifying card fully (save → match) before moving to the next card. Do not batch.

---

## Step 6 — Update Tracker

Log all scored roles to `job-outputs/jobs.csv`.

> **⚠️ Write rows positionally — this is the #1 cause of tracker corruption.** The header has **exactly 22 columns**. Every appended row must have **exactly 22 fields (21 commas)** in the exact order below — including every empty field as an empty string (no spaces, no skipped commas). The field list further down explains each field's *meaning*; this template defines each field's *position*. Build the row from this template, do not assemble it freehand.
>
> **22-field column order (positional template):**
> ```
> Company,Role,Date,Status,Resume_Used,Posting_File,Posting_URL,Redirect_URL,Filter_Score,Top_Skills,Match_Score,Match_Label,Posted_Comp,Market_Min_CAD,Market_Max_CAD,Work_Type,Contract_Length,Notes,Source,Job_ID,Contacted,Search_Terms
> ```
> For scout-link, a typical scored row looks like (note the empty fields kept as bare commas):
> ```
> Company,"Role, with comma",2026-06-21,pending,,,https://www.linkedin.com/jobs/view/[jobId]/,,7,skill1 | skill2 | skill3,,,,,,Remote,permanent,,scout-link,,,
> ```
> **URL placement rule:** the canonical LinkedIn URL goes in **`Posting_URL`** (column 7). **`Redirect_URL`** (column 8) is **Adzuna-only** — always blank for scout-link rows. Never put the LinkedIn URL in `Redirect_URL`.
>
> **Quote any field containing a comma** (e.g. a Role or Notes with a comma) with double quotes, or it will split into extra fields and break the 22-field count.
>
> **Before saving, verify each new row:** count the fields = 22; confirm `Posting_URL` holds the `https://www.linkedin.com/jobs/view/...` URL and `Redirect_URL` is blank; confirm `Source` = `scout-link`. If any check fails, fix the row before writing — do not append a malformed row.

For every listing that was scored by the filter:
- `Status`: `pending` if ≥6/10; `skipped` if below 6/10.
- `Filter_Score`: the /10 score. Leave blank if JD was not retrieved.
- `Top_Skills`: top 3 skills most emphasized in the JD, pipe-separated (e.g. `dbt | Snowflake | SQL`). Leave blank if JD was not retrieved.
- `Posting_URL`: canonical LinkedIn URL (`https://www.linkedin.com/jobs/view/[jobId]/`), built from the harvested job ID. **Required for any card that was scored by the filter** — the URL is the dedup key that prevents re-scoring on future runs. Title-skip, location-skip, age-skip, and dedup-skip cards all have a harvested job ID but are not logged to jobs.csv at all (see Step 7) — so this field never needs a blank-for-skips exception.
- `Notes`: skip reason for below-threshold rows (e.g. "Filter score 4/10 — seniority mismatch"); blank for ≥6/10.
- `Source`: `scout-link`
- `Work_Type`: from card metadata (Remote / Hybrid / On-site).
- `Contract_Length`: `permanent` unless contract language is present in the JD.
- `Search_Terms`: blank for scout-link
- `Job_ID`: blank for scout-link
- `Redirect_URL`: blank for scout-link

For ⚠️ Unverified listings (JD not retrieved): log with status `pending`, blank `Filter_Score`, blank `Top_Skills`, and Notes: `"⚠️ Unverified — JD not retrieved"`.

For `⛔ age-skip` / `⛔ title-skip` / `⛔ location-skip` cards: do **not** log to `jobs.csv`. Write to the card-skip cache in `scout-cache.md` instead (see Step 7).

---

## Step 7 — Update Card-Skip Cache

Write all hard-blocked cards (age-skip, title-skip, location-skip) from this run to the `### scout-link card skips` section of `.claude/memory/scout-cache.md`. Prepend new entries — do not overwrite existing ones.

**Format:** one row per card:
```
| [YYYY-MM-DD] | [Company] | [Title] | [age-skip / title-skip / location-skip] |
```

**Table header** (add once if the section doesn't exist yet):
```
### scout-link card skips
| Date | Company | Title | Reason |
|------|---------|-------|--------|
```

**Pruning:** At the start of each scout-link run, remove any rows in this section older than 60 days before writing new entries.

**Dedup check (Step 3):** Before checking the CSV, check this cache. If the card's company + title appears in the cache with a date within the last 60 days → drop silently, do not fetch, do not score. This prevents re-processing cards that were already hard-blocked on a prior run.

---

## Step 8 — Output the Ranked Table

**Header block:**
```
─────────────────────────────────────────
🔍 Job Scout Results
Mode: LinkedIn (scout-link / [top-applicant|preferences])
Cards found: [N] | Card-skipped: [N] | Cached: [N] | JD retrieved: [N] | JD failed: [N] | Page [N] — for more results, pass a search URL with &start=[OFFSET]
Live listings: [N] | Location-excluded: [N] | Dead dropped: [N]
Ranked by: Filter Score
─────────────────────────────────────────
```

**Ranked table:**

Show all 25 cards regardless of score. Sort by Filter Score descending. Card-skipped rows (`⛔`) and JD-failed rows (`⚠️`) sorted to the bottom after all scored rows.

| # | Company | Role | Filter Score | Note | Match Score | Gaps | URL |
|---|---------|------|--------------|------|-------------|------|-----|
| 1 | [Company] | [Title] | 🟢 9/10 | [1–2 phrase reason for score] | 78 — Good odds | [top 2–3 gaps or —] | [link] |

**Table rules:**
- Always include the direct posting URL as a markdown hyperlink (`https://www.linkedin.com/jobs/view/[jobId]/`)
- ⚠️ Unverified results shown but noted
- Note: always populate — 1–2 phrases explaining the Filter Score for every row (e.g. "Exact title match; all required tools present", "Good role fit; missing dbt", "Title mismatch — PM role", "Requires secret clearance")
- Match Score: blank if auto job-match did not run (e.g. ⚠️ Unverified, card-skipped, or below threshold)
- Gaps: top 2–3 gaps from Block B of job-match; `—` if job-match did not run
- Score colour: 🟢 9–10 | 🟡 7–8 | 🟠 6 | 🔴 below 6

---

## Step 9 — Post-Table Summary

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

**Dismiss confirmation:** After the summary block, output the full `DISMISS_QUEUE` as a table and ask for confirmation before dismissing anything:

```
─────────────────────────────────────────
🗑️ Cards queued for dismissal ([N] total)
These will be dismissed from LinkedIn recommendations once confirmed.

| # | Company | Title | Reason |
|---|---------|-------|--------|
| 1 | [Company] | [Title] | title-skip |
...

Dismiss all? (yes / no / edit list)
─────────────────────────────────────────
```

On **yes**: execute the dismiss clicks for every card in the queue using the JS snippet below, one at a time. Log `✓ dismissed` or `⚠️ not found` per card. On **no**: skip all dismissals. On **edit list**: show the list again and let the user specify which numbers to keep or remove, then confirm again.

**Dismiss JS** (run once per card — replace `[Job Title]` and `[Company]` with exact strings):
Run `js/dismiss_card.js` via `javascript_tool` (replace `[Job Title]` and `[Company]` with exact strings)
Replace `[Job Title]` and `[Company]` with exact strings from Step 2. If `'not found'`, skip silently — do not let a failed dismiss block the run. **Never dismiss a card without confirming both the job title AND company name are present in the same DOM ancestor.**

---

## Output Rules

- Never fabricate listings or scores — score only from actual JD text; mark ⚠️ Unverified if JD unavailable
- Source field is mandatory in every CSV row — always `scout-link`
- Job_ID field: leave blank for all scout-link rows — only SI Systems portal rows use this field
- Do not navigate the browser to `/jobs/view/[jobId]/` at any point during the run — constructing it as a string for the CSV `Posting_URL` field is correct and expected. Note: clicking a card in Step 2b does NOT navigate there; it stays on the search-results page and only updates the `currentJobId` query param. That is expected and required.
- Job IDs are harvested by clicking each card and reading the URL's `currentJobId` (Step 2b) — the DOM no longer exposes them as attributes post-RSC-migration. Never infer, guess, or fabricate a job ID; if a card's ID cannot be harvested (null after the walk, or a duplicate collision), mark it ⚠️ Unverified rather than guessing.
- French postings: `description.text` from the API response may be in French — score it as-is; the filter still applies
