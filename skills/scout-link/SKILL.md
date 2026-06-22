---
name: scout-link
description: "Scrapes a live LinkedIn search results page via Chrome. Clicks each card, extracts the JD from the right panel, and produces a ranked output table. Requires Claude in Chrome and an active LinkedIn login. Processes one page at a time (25 cards); auto-advances if all cards are duplicates."
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
- Right-panel render is checked per-card in Step 4 (step 6b) after the mandatory wait — do not check it here.

**No workarounds.** Do not attempt alternative URL patterns, direct `/jobs/view/` navigation, `read_page`, `web_fetch`, or processing partial card metadata. Stop cleanly and let the user re-run.

**Mode:** Default is `preferences`. Set `SCOUT_LINK_MODE = preferences` unless the user explicitly specifies `top-applicant` in their command. Do not prompt the user to choose.

**URL input:**
- No URL given, or `linkedin.com/jobs` given → navigate to `https://www.linkedin.com/jobs/`, wait 3s for render, then:
  - **Verify starting URL:** Confirm the current URL is `https://www.linkedin.com/jobs/` (or `linkedin.com/jobs/`). If it has resolved to a job posting URL (`/jobs/view/...`) or a search results URL, navigate back to `https://www.linkedin.com/jobs/` and wait again before proceeding.
  - Both sections render asynchronously via JS and will not appear in page text immediately even if visible in the viewport. The 3s wait above is the primary render gate — do not call `get_page_text` before it completes. Scroll behaviour per section is handled in the branches below.
  - Branch on `SCOUT_LINK_MODE`:

  **`top-applicant`:**
  - Scroll down 2–3 ticks and wait 3s to bring the section into view.
  - Call `get_page_text` and confirm **"Jobs where you'd be a top applicant"** appears. If not: scroll further, wait 3s, retry. If still not found after two attempts: output `⚠️ "Jobs where you'd be a top applicant" section not visible. This section requires a LinkedIn Premium account and an active profile. Re-run scout-link when the section is visible.` and stop.
  - Use `javascript_tool` to click the "Show all" link scoped to that section:
    ```js
    const h2 = Array.from(document.querySelectorAll('h2')).find(el => el.textContent.trim().includes("top applicant"));
    let found = null;
    if (h2) {
      let el = h2;
      for (let i = 0; i < 10; i++) {
        el = el.parentElement;
        if (!el) break;
        const target = Array.from(el.querySelectorAll('a, button, div[role="button"]'))
          .find(e => e.textContent.trim() === 'Show all' || e.textContent.trim().startsWith('Show all'));
        if (target) { target.click(); found = 'clicked'; break; }
      }
    }
    found || 'not found'
    ```
    Wait 3s for results to load.
  - **Verify landing URL:** Confirm the URL now contains `origin=QUALIFICATION_LANDING`. If it does not, or if `javascript_tool` returned `'not found'`, scroll down 3 ticks, wait 3s, then try clicking the visible "Show all →" button by coordinate (screenshot first to locate it). If still failing, stop and output `⚠️ Could not navigate to top applicant results. Re-run scout-link when LinkedIn renders normally.`

  **`preferences` (default):**
  - Call `get_page_text` and confirm **"Jobs based on your preferences"** appears. If not: wait 3s and retry once. If still not found after two attempts: output `⚠️ "Jobs based on your preferences" section not visible. Re-run scout-link when the section is visible.` and stop.
  - Use `javascript_tool` to click the "Show all" link scoped to that section:
    ```js
    const h2 = Array.from(document.querySelectorAll('h2')).find(el => el.textContent.trim().includes("your preferences"));
    let found = null;
    if (h2) {
      let el = h2;
      for (let i = 0; i < 10; i++) {
        el = el.parentElement;
        if (!el) break;
        const target = Array.from(el.querySelectorAll('a, button, div[role="button"]'))
          .find(e => e.textContent.trim() === 'Show all' || e.textContent.trim().startsWith('Show all'));
        if (target) { target.click(); found = 'clicked'; break; }
      }
    }
    found || 'not found'
    ```
    Wait 3s for results to load.
  - **Verify landing URL:** Confirm the URL has changed from `https://www.linkedin.com/jobs/` to a search results URL (any URL containing `/jobs/search/` or a `?` query string). If it has not changed, or if `javascript_tool` returned `'not found'`, scroll down 3 ticks, wait 3s, then try clicking the visible "Show all →" button by coordinate (screenshot first to locate it). If still failing, stop and output `⚠️ Could not navigate to preferences results. Re-run scout-link when LinkedIn renders normally.`

**Page offset (optional):** If the user specified a page number (e.g. "skip to page 3"), apply it after the full mode navigation above is complete and the search results URL is confirmed. Calculate the offset as `(N-1) * 25` and inject it into the current URL:
```js
const url = new URL(window.location.href);
url.searchParams.set('start', [OFFSET]);
window.location.href = url.toString();
```
Wait 3s for the page to render. The full mode navigation (clicking "Show all", verifying landing URL) always runs first — the offset is applied after the search context is established, never before.

**Login check:** After navigation, call `get_page_text`. If the page contains login/sign-in prompts and no job card content → output:
```
⚠️ LinkedIn login required. Log in to LinkedIn in Chrome and re-run /scout-link.
```
and stop.

---

## Step 2 — Parse Job Card List

Call `get_page_text` on the search results page. Parse the left-panel job list — each card appears as a block of:
```
[Title]
[Company]
[Location] ([Work Type])
[Optional: salary, alumni info]
[Status line: Viewed / Saved / Be an early applicant / etc.]
```

Extract per card: `title`, `company`, `location`, `work_type` (On-site / Hybrid / Remote — infer from location string), `posted` (relative date string). Accept up to 25 cards from the visible list.

**Extract posting dates:** LinkedIn renders date as `"Posted X ago"` in each card's text (e.g. `"Posted 1 week ago"`, `"Posted 4 days ago"`, `"Posted 3 weeks ago"`, `"Posted 1 month ago"`). The string appears twice per card due to screen-reader markup — use the first match. Parse this from the `get_page_text` output already retrieved for card list parsing — no extra tool call needed. Store as `CARD_DATES` (a title → relative date string map). Convert the relative string to an approximate absolute date using today's date for the age check (e.g. "1 week ago" = today − 7d, "3 weeks ago" = today − 21d, "1 month ago" = today − 30d). Cards showing `"We won't recommend this job anymore."` instead of a date (previously dismissed) or Promoted cards with no date string have no detectable date — allow through.

Announce: `📋 Found [N] job cards on this page.`

---

## Step 3 — Card-Level Smart Skip

Before clicking any card, apply two checks. Either check failing → skip without clicking. If uncertain on either, click through.

**Age check** (card-level only, applied before title/location checks):
- Look up the card's title in `CARD_DATES`
- If a `datetime` value is found AND the posting date is > 14 days before today → skip with `⛔ age-skip`. Exactly 14 days ago ("2 weeks ago") passes — only strictly more than 14 days triggers the skip.
- If the title is absent from `CARD_DATES` (Promoted or no date shown) → allow through; do not filter

**Title blocklist** (case-insensitive substring match — skip if any term appears in the title):
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
- Any city other than Calgary + `(On-site)` → skip (e.g. "Edmonton, AB (On-site)", "Toronto, ON (On-site)")
- Any location outside Alberta + `(Hybrid)` → skip (e.g. "Toronto, ON (Hybrid)", "Vancouver, BC (Hybrid)")
- Alberta cities other than Calgary + `(Hybrid)` → allow (e.g. "Edmonton, AB (Hybrid)" is fine)
- Remote (any location) → allow
- No location or ambiguous → click through

Skipped cards are **included in the output table** (Step 8) with `⛔ age-skip`, `⛔ title-skip`, or `⛔ location-skip` in the Filter Score column.

**Queue title-skipped cards for dismiss confirmation:** For each **title-skip** card only, add it to a `DISMISS_QUEUE` list. Do not click any dismiss buttons during the run. The queue is presented to the user at the end of the run (Step 9) for confirmation before any dismissals happen.

**Age-skip and location-skip cards are NOT queued for dismissal** — dismissing these would negatively affect LinkedIn's recommendation algorithm. They are skipped silently without any dismiss action.

`DISMISS_QUEUE` entry format: `{ company, title, skip_reason }` (e.g. `{ "Dasro Consulting Inc.", "SAP Data Analyst", "title-skip" }`).

Announce: `⏭️ [N] card(s) skipped (age, title, or location) — [N] title-skip(s) queued for dismiss confirmation.`

---

## Step 4 — Click and Extract JDs

**Stay on the search results page throughout this entire step.** Do not navigate to `/jobs/view/[jobId]/` or any other URL. All JD extraction happens from the right panel of the search results page.

**Card structure:** LinkedIn cards are `div[role="button"]` elements with `tabindex=0` — they have no aria-label and no job ID in the DOM. The job ID only becomes available in the URL **after** clicking. Do not use `find` to click cards — it matches on inner text and can click the wrong card when titles are similar (e.g. two "Data Engineer" roles). Use `javascript_tool` to target cards precisely by title + company text match, then `.click()` them directly.

For each card not skipped in 3, in order:

1. Use `javascript_tool` to find and click the correct card by matching both title AND company in the card's text content:
   ```js
   const cards = Array.from(document.querySelectorAll('div[role="button"][tabindex="0"]'))
     .filter(el => el.offsetParent !== null);
   const target = cards.find(el => {
     const t = el.textContent;
     return t.includes('[Title]') && t.includes('[Company]');
   });
   if (target) { target.click(); 'clicked' } else { 'not found' }
   ```
   Replace `[Title]` and `[Company]` with the exact strings from 2. If `'not found'`: scroll the left panel down 2 ticks, wait 1s, retry once. If still not found, log `⚠️ [Company] — [Title] → card not found in DOM; skipping`.
2. Wait 2–3s for the right panel to load.
3. **Verify the card loaded correctly:** Read `currentJobId` from the page URL (via `javascript_tool`: `new URL(window.location.href).searchParams.get('currentJobId')`). Store this as `EXPECTED_JOB_ID`. Also read the tab title — it should contain the expected company name and role title. If the tab title shows a different company or role than expected, do not record this ID — log `⚠️ [Company] — [Title] → ID mismatch in tab title; skipping` and proceed to next card. **Never record a job ID that was inferred, guessed, or constructed without clicking the card.**
4. Construct canonical URL: `https://www.linkedin.com/jobs/view/[jobId]/`
5. **Dedup check:** run checks in order, stopping at the first match:
   - **Card-skip cache:** check the `### scout-link card skips` table in `.claude/memory/scout-cache.md` for a row with matching company + title within the last 60 days → drop silently; proceed to next card.
   - **CSV URL match:** check `Posting_URL` column (case-insensitive exact match).
   - **CSV company+title match:** check for a CSV row with the same company name (case-insensitive) AND same role title (case-insensitive) where `Date` is within the last 30 days.

   For any CSV match found:
   - status `closed` or `skipped` → drop silently; proceed to next card.
   - Any other status → log `⚠️ [Company] — [Title] → already in CSV (status: [status], date: [date]); skipping` and proceed to next card. **Do not extract the JD, do not run the filter, do not append a new CSV row.**
5b. **All-duplicate check:** If every non-title-skipped card on the current page was a duplicate (already in CSV or cache) — i.e. zero new JDs were extracted and scored — automatically advance to the next page rather than stopping. Click the "Next" pagination link at the bottom of the results using `javascript_tool`:
```js
const next = Array.from(document.querySelectorAll('a, button')).find(el => el.textContent.trim() === 'Next');
if (next) { next.click(); 'clicked' } else { 'not found' }
```
Wait 3s for the new page to load, then restart from Step 2 on the new set of cards. Continue paginating until at least one new JD is found, or until LinkedIn shows no "Next" button (end of results), at which point announce: `📭 All pages exhausted — no new roles found.`
6. **Signal tab activity** — immediately after the card click, run:
   ```js
   window.focus();
   document.dispatchEvent(new Event('visibilitychange'));
   document.dispatchEvent(new MouseEvent('mousemove', { bubbles: true, clientX: 800, clientY: 400 }));
   'signaled'
   ```
   This signals to the browser that the tab is active and unthrottles deferred JS renders. Run this as a separate tool call before the wait below.
6a. **Wait 3s** as a separate tool call before touching the right panel — the panel renders asynchronously and must not be read immediately after the click. This wait is mandatory regardless of how fast prior steps completed.
6b. **Body length check:** Before attempting extraction, confirm the page has grown beyond the card-list baseline. Run:
    ```js
    document.body.innerText.length
    ```
    If the length is ≤ 4500 chars, the right panel has not injected content yet. Scroll the right side of the viewport down 2–3 ticks, wait 2s, and re-check once. If still ≤ 4500 after the retry, treat as a render failure — apply the same stop/ask logic as a null extraction result in step 8.
6c. **Job ID consistency check:** Confirm the `currentJobId` in the URL still matches `EXPECTED_JOB_ID` (from step 3). If it has changed (another card loaded in the background), click the original card again and restart from step 6.
7. **Expand the full JD:** Click the "… more" button if present to ensure the full description is loaded. Use `javascript_tool`:
   ```js
   const btn = Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('… more') && el.offsetParent !== null);
   if (btn) { btn.click(); 'clicked' } else { 'not found' }
   ```
   Wait 1s after clicking. If `'not found'`, the JD may already be fully expanded — proceed to step 8.
7b. **Scroll the right panel** to ensure the full JD is rendered into the DOM. Use `javascript_tool`:
    ```js
    const panel = document.querySelector('.jobs-search__job-details, [class*="job-details"], [class*="jobs-unified-top-card"]');
    if (panel) { panel.scrollTop += 300; 'scrolled' } else { 'panel not found' }
    ```
    Wait 1s after scrolling.
8. **Extract JD via right-panel DOM** — do NOT use `get_page_text`. LinkedIn renders the right panel outside `<main>`, so `get_page_text` misses it. Target the right panel directly, then fall back to full body search.

   **Primary method — bounded extraction (preferred):** Use the natural end-of-JD anchor `"See how you compare"` to extract the full JD in a single call, avoiding tool-response truncation. This anchor is rendered by LinkedIn Premium and is reliably present for this account — treat it as the stable primary method, not an edge case:
   ```js
   const panel = document.querySelector('.jobs-search__job-details, [class*="job-details"]');
   const src = (panel && panel.innerText.length > 500) ? panel.innerText : document.body.innerText;
   const start = src.indexOf('About the job');
   const end = src.indexOf('See how you compare');
   (start >= 0 && end > start) ? src.substring(start, end)
     : (start >= 0 ? src.substring(start, start + 6000) : null)
   ```
   This returns the full JD text in one call for the majority of postings. If `null` (anchor not found), scroll the right panel down 2–3 ticks, wait 2s, and retry once.

   **Fallback method — fixed-window chunking (use if bounded extraction returns null or end anchor is absent):**
   ```js
   // Chunk 1
   const panel = document.querySelector('.jobs-search__job-details, [class*="job-details"]');
   const src = (panel && panel.innerText.length > 500) ? panel.innerText : document.body.innerText;
   const idx = src.indexOf('About the job');
   idx >= 0 ? src.substring(idx, idx + 6000) : null
   ```
   If 6000 chars truncates mid-sentence, fetch the next chunk:
   ```js
   // Chunk 2
   const panel = document.querySelector('.jobs-search__job-details, [class*="job-details"]');
   const src = (panel && panel.innerText.length > 500) ? panel.innerText : document.body.innerText;
   const idx = src.indexOf('About the job');
   idx >= 0 ? src.substring(idx + 6000, idx + 12000) : null
   ```
   Note: fixed-window chunking may still be cut off by the Chrome MCP tool's response limit. More testing needed before promoting this as the primary method — keep both approaches for now.
9. Check extracted text for job description content (responsibilities, requirements, or qualifications):
   - **Present and non-empty** → JD extracted; run filter inline (from `skills/filter/SKILL.md`) on this card's JD before moving to the next card
   - **Empty or null** → wait 3s and retry Step 6 once as a separate tool call.
     - Still empty after retry → **re-click the card** (click it again via `javascript_tool`) and wait 3s. This resolves lazy-render failures where LinkedIn delays injecting the right panel DOM. Re-check body length and extraction after the re-click.
     - Still empty after re-click → stop and ask: "JD not loading for [Company] — [Title] (ID: [jobId]). Right panel may not have rendered. How would you like to proceed? (skip this card / try again / stop scout)"
     - **Session-wide panel failure** (multiple consecutive native-LinkedIn cards returning null): do NOT reload the page. Instead, continue clicking remaining cards — the issue resolves itself as the page warms up. Cohere-pattern fix: re-clicking the same card after the page has been active longer often succeeds.
     - Do NOT navigate to `https://www.linkedin.com/jobs/view/[jobId]/` as a fallback — this leaves the search results page and breaks the card extraction flow.

**Do not navigate away from the search results page between cards.** Clicking a card updates the right panel in-place — the left card list remains intact and the next card can be clicked immediately after extraction.

Log inline progress: `✓ [Company] — [Title] (ID: [jobId]) → JD extracted` / `↩️ [Company] — [Title] → CSV dedup, skipping` / `⚠️ [Company] — [Title] → ID mismatch or JD not retrieved`

---

## Step 5 — Save Posting + Auto Job-Match

For every card that scored ≥6/10 in 4:

1. **Save the job posting** — run `skills/save-job-posting/SKILL.md` using the JD already extracted in this session. Do not re-fetch. Confirm: `📎 Posting saved as [filename]`.
2. **Run job-match quick mode** per `skills/job-match/SKILL.md` immediately after saving. Skip the auto-save step inside job-match (Step 0.5a) — the posting was already saved in step 1 above.

Process each qualifying card fully (save → match) before moving to the next card. Do not batch.

---

## Step 6 — Update Tracker

Log all scored roles to `job-outputs/jobs.csv`:

For every listing that was scored by the filter:
- `Status`: `pending` if ≥6/10; `skipped` if below 6/10.
- `Filter_Score`: the /10 score. Leave blank if JD was not retrieved.
- `Top_Skills`: top 3 skills most emphasized in the JD, comma-separated (e.g. `dbt, Snowflake, SQL`). Leave blank if JD was not retrieved.
- `Posting_URL`: canonical LinkedIn URL (`https://www.linkedin.com/jobs/view/[jobId]/`). **Required for any card that was scored by the filter** — the URL is the dedup key that prevents re-scoring on future runs. Leave blank only for cards that were hard-blocked before scoring (age-skip, title-skip, location-skip) — those don't need a URL since the block fires before the card is clicked.
- `Notes`: skip reason for below-threshold rows (e.g. "Filter score 4/10 — seniority mismatch"); blank for ≥6/10.
- `Source`: `scout-link`
- `Work_Type`: from card metadata (Remote / Hybrid / On-site).
- `Contract_Length`: `permanent` unless contract language is present in the JD.

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

**Dedup check (Step 4, Step 5):** Before checking the CSV, check this cache. If the card's company + title appears in the cache with a date within the last 60 days → drop silently, do not click, do not score. This prevents re-processing cards that were already hard-blocked on a prior run.

---

## Step 8 — Output the Ranked Table

**Header block:**
```
─────────────────────────────────────────
🔍 Job Scout Results
Mode: LinkedIn (scout-link / [top-applicant|preferences])
Cards found: [N] | Card-skipped: [N] | Cached: [N] | JD retrieved: [N] | JD failed: [N] | Page 1 only — for more results, pass a search URL with &start=25
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
| 1 | [Company] | [Title] | [title-skip / age-skip / location-skip] |
...

Dismiss all? (yes / no / edit list)
─────────────────────────────────────────
```

On **yes**: execute the dismiss clicks for every card in the queue using the JS snippet below, one at a time. Log `✓ dismissed` or `⚠️ not found` per card. On **no**: skip all dismissals. On **edit list**: show the list again and let the user specify which numbers to keep or remove, then confirm again.

**Dismiss JS** (run once per card — replace `[Job Title]` and `[Company]` with exact strings):
```js
// Use aria-label*= (contains) — LinkedIn adds trailing spaces to aria-labels.
// Always verify BOTH title AND company in the same ancestor before clicking.
const allBtns = Array.from(document.querySelectorAll('button[aria-label*="Dismiss [Job Title]"]'));
let dismissed = 'not found';
for (const btn of allBtns) {
  let el = btn;
  for (let i = 0; i < 12; i++) {
    el = el.parentElement;
    if (!el) break;
    if (el.textContent.includes('[Job Title]') && el.textContent.includes('[Company]')) {
      btn.click(); dismissed = 'dismissed'; break;
    }
  }
  if (dismissed === 'dismissed') break;
}
dismissed
```
Replace `[Job Title]` and `[Company]` with exact strings from Step 2. If `'not found'`, skip silently — do not let a failed dismiss block the run. **Never dismiss a card without confirming both the job title AND company name are present in the same DOM ancestor.**

---

## Output Rules

- Never fabricate listings or scores — score only from actual JD text; mark ⚠️ Unverified if JD unavailable
- Source field is mandatory in every CSV row — always `scout-link`
- Job_ID field: leave blank for all scout-link rows — only SI Systems portal rows use this field
- Do not navigate to `/jobs/view/[jobId]/` at any point during card extraction
- Never record a job ID that was inferred, guessed, or constructed without clicking the card
- French postings use the same English UI chrome — "About the job" anchor always applies; JD body may be French but navigation/headers stay English
