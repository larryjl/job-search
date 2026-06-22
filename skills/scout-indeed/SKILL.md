---
name: scout-indeed
description: "Scrapes Indeed Canada job search results via Chrome. Extracts all job keys from the search results page in one pass, then visits each viewjob page to extract the full JD and structured metadata. Runs filter scoring inline. Requires Claude in Chrome and an active Indeed login."
---

# Scout Indeed

Scrapes Indeed Canada job listings via Chrome. Requires Claude in Chrome and an active Indeed login.

**Trigger phrases:** `/scout-indeed`, "scout indeed", "scrape indeed jobs", or any request to pull jobs from Indeed.

---

## Step 0 — Load Context

Silently load before starting:
- `profile/targets.md`
- `profile/skills-inventory.md`
- `.claude/memory/scout-cache.md` (for dedup)
- `job-outputs/jobs.csv` (for dedup)

---

## Step 1 — Setup Check

**Chrome check:** If Claude in Chrome is not connected → stop and output:
```
⚠️ Claude in Chrome is required for scout-indeed. Connect the extension and re-run.
```

**Login check:** Navigate to `https://ca.indeed.com/` and call `get_page_text`. If the page shows a sign-in prompt and no job content → output:
```
⚠️ Indeed login required. Log in to Indeed in Chrome and re-run /scout-indeed.
```
and stop.

---

## Step 2 — Build Search Passes

Scout-indeed runs two search passes by default, then deduplicates by `jk` across passes. This covers the full target role list without query bloat or noise.

**Default passes:**

| Pass | `q` param | Pages |
|------|-----------|-------|
| 1 | `%22data+analyst%22+OR+%22business+analyst%22+OR+%22analytics+engineer%22` | 1–2 |
| 2 | `%22data+engineer%22+OR+%22data+architect%22+OR+%22data+migration%22` | 1 only |

**Why two passes:** Testing showed that running >3 quoted OR terms degrades Indeed's relevance ranking and surfaces unrelated roles (Geologist, Environmental Engineer, Hearing Aid Specialist). Splitting into two focused passes keeps results clean. The core results overlap (~5 jks appear in both passes) — dedup handles this.

**Full default URLs:**
```
Pass 1, page 1: https://ca.indeed.com/jobs?q=%22data+analyst%22+OR+%22business+analyst%22+OR+%22analytics+engineer%22&l=Calgary%2C+AB&fromage=14
Pass 1, page 2: https://ca.indeed.com/jobs?q=%22data+analyst%22+OR+%22business+analyst%22+OR+%22analytics+engineer%22&l=Calgary%2C+AB&fromage=14&start=10
Pass 2, page 1: https://ca.indeed.com/jobs?q=%22data+engineer%22+OR+%22data+architect%22+OR+%22data+migration%22&l=Calgary%2C+AB&fromage=14
```

**Overrides:**
- User provides a custom URL → use it as-is for a single pass, skip defaults
- User specifies `--pass1` or `--pass2` → run only that pass
- User specifies a page number N → set `start=(N-1)*10` on whichever pass is active

**Location param:** Always `l=Calgary%2C+AB`. The `sc=0kf%3Aattr(DSQF7)%3B` remote facet filter is intentionally omitted — testing showed it narrows results too aggressively. Remote roles still surface via Indeed's relevance ranking and are caught by the `jobLocationType` field in JSON-LD.

For each pass, navigate to the URL and wait 2s for render.

**Render check (per page):**
```js
document.querySelectorAll('[data-testid="slider_item"]').length
```
If 0 → wait 2s and retry once. If still 0 → skip this page with a note; continue to next.

Announce: `🔍 Pass [N], page [P] loaded.`

---

## Step 3 — Scrape Card List

Extract all job keys and card metadata from the search results page in a single JS call:

```js
const cards = Array.from(document.querySelectorAll('[data-testid="slider_item"]'));
cards.map(c => {
  const jk = c.querySelector('a[data-jk]')?.getAttribute('data-jk') || null;
  const title = c.querySelector('h3')?.innerText?.trim() || '';
  const company = c.querySelector('[data-testid="company-name"]')?.innerText?.trim() || '';
  const loc = c.querySelector('[data-testid="text-location"]')?.innerText?.trim() || '';
  const salary = c.querySelector('[data-testid="attribute_snippet_testid"]')?.innerText?.trim() || '';
  const isNew = c.innerText?.includes('New\n') || false;
  return { jk, title, company, loc, salary, isNew };
}).filter(c => c.jk)
```

Store result as `CARD_LIST`. Announce: `📋 Found [N] job cards on this page.`

**Note on blocked first card:** Occasionally the first card's link contains tracking parameters that cause the Chrome MCP to block attribute reads. If a card returns `jk=null`, skip it silently — it will not appear in the output. This is a Chrome MCP restriction, not an Indeed issue.

---

## Step 4 — Card-Level Smart Skip

Before visiting any viewjob page, apply these checks to each card using the `CARD_LIST` data. Any check failing → mark as skipped; do not visit the viewjob page.

**Cross-pass dedup:** If `jk` is already in `SEEN_JKS` (seen on a prior page or pass this session) → skip silently; do not log.

**CSV dedup:** Check `job-outputs/jobs.csv` `Posting_URL` column for `https://ca.indeed.com/viewjob?jk={jk}` (case-insensitive):
- Status `closed` or `skipped` → drop silently
- Any other status → flag `⚠️ already applied`; skip viewjob visit; include in output table with cached Filter Score if available

**Title blocklist** (case-insensitive substring match — skip if any term appears in the title):
- Software Engineer
- Software Developer
- Data Scientist
- PowerBuilder
- GIS
- SAP
- Full Stack
- Backend
- Frontend

**Location blocklist** (inferred from the card `loc` field):
- Location is **outside Canada entirely** (e.g. US city, international) → skip
- Everything else → **allow through to viewjob**, including: Calgary AB, other Alberta cities, Toronto, Mississauga, "Canada", blank, or any ambiguous location

**Why:** Work type is not available at the card level — Indeed does not expose remote/hybrid/on-site in card data. A Toronto or "Canada" posting may be fully remote and therefore eligible. The only safe card-level location skip is roles that are definitively outside Canada.

**Note:** All location qualification (Calgary on-site ✅, Alberta hybrid ✅, remote anywhere in Canada ✅, non-Alberta on-site ❌, non-Alberta hybrid ❌) is determined post-JD-extraction in Step 4a, not here.

Log skipped cards inline: `⏭️ [N] card(s) skipped (cross-pass dupe, CSV dedup, title, or location).`

---

## Step 5 — Visit Viewjob Pages and Extract JDs

For each card not skipped in Step 4, in order:

1. Navigate to `https://ca.indeed.com/viewjob?jk={jk}` (no other params needed).

2. Wait 2s for render. Verify page loaded:
   ```js
   document.querySelector('#jobDescriptionText')?.innerText?.length
   ```
   If 0 or null → wait 2s and retry once. If still empty → log `⚠️ [Company] — [Title] (jk: {jk}) → JD not loaded; skipping` and proceed to next card.

3. **Extract structured metadata from JSON-LD** (one call, no DOM hunting):
   ```js
   const s = Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
     .find(s => s.textContent.includes('JobPosting'));
   const d = s ? JSON.parse(s.textContent) : null;
   d ? {
     title: d.title,
     company: d.hiringOrganization?.name,
     datePosted: d.datePosted,
     remote: d.jobLocationType,          // "TELECOMMUTE" = remote
     city: d.jobLocation?.address?.addressLocality,
     region: d.jobLocation?.address?.addressRegion,
     salaryMin: d.baseSalary?.value?.minValue,
     salaryMax: d.baseSalary?.value?.maxValue,
     salaryUnit: d.baseSalary?.value?.unitText,
     employmentType: d.employmentType
   } : null
   ```
   Store as `JD_META`. If `null` → fall back to card metadata from `CARD_LIST` for title/company/location.

4. **Age check:** Parse `JD_META.datePosted` as an ISO date. If posted > 14 days before today (Mountain Time) → log `⛔ age-skip — [Company] — [Title] (posted {date})` and proceed to next card. Do not run filter.

4a. **Post-JD location check** (for all non-Calgary cards): After extracting JD text and metadata, determine work type using this priority order:
   1. `jobsearch-CompanyInfoContainer` text on the viewjob page — check for "Hybrid work", "Remote", or "On-site" badge (most reliable):
      ```js
      document.querySelector('[data-testid="jobsearch-CompanyInfoContainer"]')?.innerText
      ```
   2. `JD_META.jobLocationType === "TELECOMMUTE"` → remote ✅
   3. JD text keywords: "remote", "hybrid", "work from home", "wfh" → remote/hybrid signal
   4. JD text keywords: "on-site", "onsite", "in-person", "in office", "at our [city]" with no remote/hybrid language → on-site signal

   **Then apply:**
   - Calgary, AB (any work type) → allow ✅
   - Alberta outside Calgary, hybrid or remote confirmed → allow ✅
   - Alberta outside Calgary, on-site confirmed or inferred → `⛔ location-skip — [Company] — [Title] (Alberta on-site, non-Calgary)`
   - Outside Alberta, remote confirmed → allow ✅
   - Outside Alberta, hybrid or on-site confirmed → `⛔ location-skip — [Company] — [Title] (non-Alberta, not remote)`
   - Outside Alberta, work type ambiguous → `⛔ location-skip — [Company] — [Title] (non-Alberta, work type unknown)` (conservative; outside Alberta requires confirmed remote to proceed)

   Do not run filter on location-skipped cards.

5. **Extract full JD text:**
   ```js
   document.querySelector('#jobDescriptionText')?.innerText
   ```
   Store as `JD_TEXT`.

6. **Log progress:** `✓ [Company] — [Title] (jk: {jk}) → JD extracted ({len} chars)`

7. **Run filter inline** per `skills/filter/SKILL.md` using `JD_TEXT` + `JD_META`. Produce Filter Score /10.

---

## Step 6 — Save Posting + Auto Job-Match

For every card that scored ≥ 6/10 in Step 5:

1. **Save the job posting** — run `skills/save-job-posting/SKILL.md` using `JD_TEXT` already extracted. Do not re-fetch. Confirm: `📎 Posting saved as [filename].`

2. **Run job-match quick mode** per `skills/job-match/SKILL.md` immediately after saving. Skip the auto-save step inside job-match (Step 0.5a) — the posting was already saved in step 1 above.

Process each qualifying card fully (save → match) before moving to the next card.

---

## Step 7 — Update Tracker

Log all scored roles to `job-outputs/jobs.csv`.

For every card that reached filter scoring:
- `Status`: `pending` if ≥ 6/10; `skipped` if below threshold
- `Filter_Score`: integer /10
- `Top_Skills`: top 3 skills most emphasized in JD, pipe-separated (e.g. `dbt | Snowflake | SQL`)
- `Posting_URL`: `https://ca.indeed.com/viewjob?jk={jk}`
- `Posted_Comp`: salary from `JD_META` if available (e.g. `80000-100000 CAD` or `38-66/hr CAD`)
- `Work_Type`: `Remote` if `JD_META.remote == "TELECOMMUTE"`; otherwise infer from card `loc` field or JD text (`Remote` / `Hybrid` / `On-site`)
- `Contract_Length`: `permanent` unless contract language present in JD
- `Notes`: skip reason for below-threshold rows; blank for ≥ 6/10
- `Source`: `scout-indeed`

For ⚠️ JD-failed cards: log with status `pending`, blank scores, Notes: `"⚠️ Unverified — JD not loaded"`

For ⛔ age-skip cards: log with status `skipped`, Notes: `"card-skipped — age-skip ({datePosted})"`

For title-skip / location-skip cards: log with status `skipped`, Notes: `"card-skipped — [title-skip / location-skip]"`

---

## Step 8 — Advance Through Passes and Pages

**Pass/page sequencing:**

```
Pass 1, page 1  →  Pass 1, page 2  →  Pass 2, page 1  →  done
```

After completing each page:
- **All-duplicate page:** If every non-skipped card was a dedup hit → advance automatically without asking.
- **Normal advance:** Announce `📄 Pass [N] page [P] done — [X] new roles found.` then proceed to next page/pass automatically. Only stop to ask if the user has specified a manual page or pass override.

**Cross-pass dedup:** Maintain a single `SEEN_JKS` set across all passes and pages. Any jk already in `SEEN_JKS` is skipped silently at the card-level check in Step 4 — do not visit its viewjob page again.

**End conditions:**
- All default passes and pages exhausted → proceed to output
- Indeed returns 0 cards on a page → skip to next pass (or finish if on last pass)
- User explicitly says stop mid-run

---

## Step 9 — Update Memory

Write to `scout-cache.md` only. Do not write to the Verified Postings Cache — jobs.csv is the source of truth for URL dedup.

**Scout Cache** (`## Scout Cache`) — prepend a new entry; never overwrite:

```
### Run: [YYYY-MM-DD] | Mode: Indeed (scout-indeed) | Passes: [N] | Total cards: [N] | Cross-pass dupes: [N] | Card-skipped: [N] | Age-skipped: [N] | JD retrieved: [N] | JD failed: [N]
Live results: [N] | Below threshold: [N] | Eligible (≥6): [N]
Pass 1 q: "data analyst" OR "business analyst" OR "analytics engineer" | pages: 1-2 | cards: [N]
Pass 2 q: "data engineer" OR "data architect" OR "data migration" | pages: 1 | cards: [N]
Notes: [any issues, login state, blocked cards, noise roles surfaced, etc.]
```

---

## Step 10 — Output Ranked Table

**Header block:**
```
─────────────────────────────────────────
🔍 Job Scout Results
Mode: Indeed (scout-indeed) | Passes: 2 | Pages: 3
Cards found: [N] | Cross-pass dupes: [N] | Card-skipped: [N] | Age-skipped: [N] | JD retrieved: [N] | JD failed: [N]
Live listings: [N] | Below threshold: [N]
Ranked by: Filter Score
─────────────────────────────────────────
```

**Ranked table:**

Show all cards regardless of score. Sort by Filter Score descending. Card-skipped, age-skipped, and JD-failed rows sorted to the bottom after all scored rows.

| # | Company | Role | Posted | Filter Score | Note | Match Score | Gaps | URL |
|---|---------|------|--------|--------------|------|-------------|------|-----|
| 1 | [Company] | [Title] | Jun 18 | 🟢 9/10 | [1–2 phrase reason for score] | 78 — Good odds | [top 2–3 gaps or —] | [link] |

**Table rules:**
- Always include `https://ca.indeed.com/viewjob?jk={jk}` as a markdown hyperlink
- `Posted`: format `JD_META.datePosted` as `Mon DD` (e.g. `Jun 18`); blank if unavailable
- Note: always populate — 1–2 phrases explaining the Filter Score for every row (e.g. "Exact title match; all required tools present", "Good role fit; missing dbt", "Title mismatch — PM role", "Requires secret clearance")
- Match Score: blank if job-match did not run (below threshold, JD failed, or skipped)
- Gaps: top 2–3 gaps from Block B of job-match; `—` if job-match did not run
- Score colour: 🟢 9–10 | 🟡 7–8 | 🟠 6 | 🔴 below 6
- ⚠️ Unverified and ⛔ skipped rows shown but noted

---

## Step 11 — Post-Table Summary

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

- Never fabricate listings or scores — score only from actual JD text; mark ⚠️ Unverified if JD unavailable
- Source field is mandatory in every CSV row — always `scout-indeed`
- Job_ID field: leave blank for all scout-indeed rows
- Canonical posting URL is always `https://ca.indeed.com/viewjob?jk={jk}` — never include `tk`, `from`, `vjs`, or other tracking params
- Do not run filter or job-match on age-skipped, title-skipped, or location-skipped cards
- If `JD_META` is null for a card, fall back to card metadata from `CARD_LIST` for CSV fields; mark Filter Score blank and Notes as `⚠️ Unverified`
