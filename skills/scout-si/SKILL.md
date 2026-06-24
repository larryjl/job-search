---
name: scout-si
description: "Automated end-to-end SI Systems job sweep. Opens portal.sisystems.com search results, reviews each job card, hard-blocks clear mismatches on title alone, opens the full JD for the rest, runs the filter score (≥6/10 threshold), runs job-match quick for eligible jobs, and applies directly through the portal form when job-match recommends it — answering all form questions honestly from skills-inventory.md. Trigger on: 'scout-si', 'scout si', 'scout si systems', 'sweep si systems', 'run si systems', 'check si systems jobs', or any request to process or apply to SI Systems job listings."
---

# SI Systems Scout Skill

Automates the full SI Systems job review-and-apply pipeline in a single run. Works through the portal job list card by card, filtering aggressively so only genuinely good fits get an application.

---

## Prerequisites — Read These Files First

Before touching the browser, read:

1. `profile/master-resume.md` — candidate background
2. `profile/skills-inventory.md` — hard proficiency constraints
3. `profile/targets.md` — target roles, seniority, salary floor, preferred industries
4. `skills/filter/SKILL.md` — full scoring rubric and hard-block rules
5. `.claude/config/domains.md` — approved domains (portal.sisystems.com should already be approved)

Keep these in working memory throughout — you'll use them for every job.

---

## Browser Method

**Always use Claude in Chrome (`mcp__Claude_in_Chrome__*` tools) for all portal interaction.** Never use computer-use screen capture or pixel-clicking for this skill. Specifically:

- Use `tabs_context_mcp` (with `createIfEmpty: true`) to get a tab ID, then `navigate` to load pages
- Use `read_page` (accessibility tree) to read card data, form fields, and page state — this is the primary way to read job cards without clicking
- Use `find` + `form_input` / `javascript_tool` for clicks, dropdowns, and form fills
- Use `get_page_text` only as a fallback when `read_page` is insufficient

---

## Phase 0 — Auto-Login

Run this phase before navigating to the job search page. If already logged in, skip to Phase 1.

1. Call `tabs_context_mcp` (createIfEmpty: true) to get a tab ID.
2. `navigate` to `https://portal.sisystems.com` and wait 3 seconds for Angular to load.
3. Call `read_page` to check login state:
   - If your name is visible in the header → already logged in, skip to Phase 1.
   - If a login/email form is present → proceed with steps below.

### Step 0.1: Check for Autofill, Then Fill if Needed

Chrome's password manager autofills the email and password fields automatically on this portal. Check field state before filling:

1. Call `read_page` (filter: interactive) to inspect the email and password fields.
2. If both fields are already populated → do not use `form_input`. Proceed directly to clicking "Sign in".
3. If either field is empty → use `find` + `form_input` to fill only the empty field(s) with the account email (`leelawrencej@gmail.com`) and/or password from the saved credential.
4. Use `find` to locate the "Sign in" button and click it. Wait 3 seconds.

### Step 0.2: Handle Verification Code (if prompted)

After clicking "Sign in", the portal may show a verification step on the same page (MSAL / Microsoft Azure B2C). The flow is:

1. A "Send verification code" button appears with the email address pre-filled. Use `find` to locate the button with exact text "Send verification code" and click it. Wait 5 seconds for the email to arrive.
2. **Search Gmail** using `mcp__c403b25a-b59b-4370-997a-b95459ce1c1c__search_threads` with query:
   ```
   from:msonlineservicesteam@microsoftonline.com subject:"S.i. Systems account email verification code" newer_than:5m
   ```
3. Pick the most recent thread (highest `date`). If no thread found, wait 5 seconds and retry once. If still nothing, tell the user: "Verification email not found in Gmail — please enter the code manually and let me know when done."
4. Call `get_thread` with the thread ID (use `FULL_CONTENT` format). Extract the 6-digit numeric verification code from the snippet or body — it appears as "Your code is: NNNNNN".
5. The verification code input field appears on the same page (no navigation needed). Use `find` to locate it, then `form_input` to enter the 6-digit code. Click the "Verify code" button.
6. Wait 3 seconds. The page shows "E-mail address verified. You can now continue." and the "Continue" button becomes active. Use `find` to locate "Continue" and click it.
7. Wait 4 seconds, then confirm login succeeded — the tab URL should change to `portal.sisystems.com/#/portal/profile/view` or similar, and your name should be visible in the portal header.
8. If login failed, tell the user: "Login failed after entering the verification code — please check the portal and let me know when you're logged in."

### Step 0.4: Mid-Run Re-Login

If the portal redirects to a login page mid-run (MSAL token expiry), run Phase 0 again from Step 0.1. Resume from the card you were processing once login is confirmed.

---

## Phase 1 — Navigate to Search Results

1. Call `tabs_context_mcp` (createIfEmpty: true) to get a tab ID.
2. `navigate` to: `https://portal.sisystems.com/#/portal/jobs/searchJobs`
3. Wait 2 seconds for Angular to load, then call `read_page` to confirm you're logged in (your name visible in header). If not, run Phase 0.
4. Note the total result count from `read_page` (e.g. "Your 40 results are in"). This is your working set. **Never touch the filters** — they are always pre-set correctly. Do not read, check, adjust, or re-search based on filters.
6. **Build the seen-ID set:** Read `job-outputs/jobs.csv` and extract all `Job_ID` values where `Source = SI Systems portal` and `Status` is `applied` or `skipped`. Store this as your dedup set for the run.

---

## Phase 2 — Card-by-Card Review

Work through the job list from top to bottom. The list uses **infinite scroll** — scroll to the bottom first to load all available cards before starting card-by-card review:

Run `js/scroll_to_bottom.js` via `javascript_tool`

Wait 2 seconds, then check the DETAILS button count. If it increased, scroll again and wait. Repeat until the count stabilises. Only then start processing cards from index 0. This avoids missing cards that load below the initial viewport.

Extract all card titles and ages in one JS pass before clicking anything:

Run `js/extract_card_list.js` via `javascript_tool`

Use this to identify which cards to process (title hard-block and age check) before opening any DETAILS.

For each visible job card — Steps A and A1 can be determined from the pre-extracted card list without clicking DETAILS:

### Step A: Title Hard-Block Check

Read the card title. Hard-block **immediately** (no need to open the full JD) if the title clearly signals any of the following:

- Pure QA / testing / SDET role
- DevOps / infrastructure / cloud engineering (not BA or data)
- Finance analyst (accounting, FP&A, treasury — not data analytics)
- US-only role (US locations with no remote option visible)
- Director or VP level (target is Senior IC / Lead)
- Clinical / medical / nursing roles
- Legal / compliance officer roles
- Sales / marketing / customer success

When hard-blocking: note the job title in your running log, mark it "⛔ Hard-blocked (title)" — do **not** click DETAILS or APPLY.

If the title is ambiguous — or if it's a BA, data, analytics, systems analyst, or BI role — proceed to Step B.

### Step A1: Age Check

Read the **Posted:** field visible on the card (no need to open the JD).

Parse the value and skip if the posting is older than 14 days:

- `N days ago` where N > 14 → skip
- `1 week ago` (≈7 days) → proceed
- `2 weeks ago` or more → skip
- `N months ago` → skip
- `today`, `yesterday`, `N hours ago`, `N days ago` where N ≤ 14 → proceed

When skipping: log `⛔ Too old (posted: [value])` — do **not** click DETAILS.

**Early termination:** The list is sorted newest-first. Once you hit a card that fails the age check, all remaining cards are also too old — stop the run, note "Reached age cutoff — stopping early" in the run summary, and skip to Phase 5.

### Step A2: Pre-DETAILS Deduplication (best-effort)

The Job ID is **not visible on the card** — it only appears in the JD body after clicking DETAILS. True deduplication happens in Step B. However, if the card title exactly matches a role you already applied to or skipped in this run, skip it without opening DETAILS and note "⏭️ Already seen (title match)".

### Step B: Open Full JD

Click the DETAILS button for the job to open the inline JD panel. Two methods — try JS first; fall back to ref if the session redirects to login:

**Method 1 (preferred — simpler):** Use `javascript_tool` to click by index (replace N with the zero-based card index):

Run `js/click_details_by_index.js` via `javascript_tool`

**Method 2 (fallback):** Use `find` to locate the DETAILS button by title context, then `left_click` via ref.

If either method triggers an unexpected redirect to the login page, stop and ask the user to log back in. The cause may be MSAL token expiry or an anti-automation protection — do not retry the same method repeatedly. Once back in, resume from the card you were on.

Wait 2 seconds after clicking, then use `javascript_tool` (`document.body.innerText`) to read the full JD including location, contract length, and all requirements.

**Capture the URL** using `javascript_tool` (`window.location.href`) while on the DETAILS page — this is the `Posting_URL` to write to `jobs.csv`.

Read the JD via `javascript_tool` (`document.body.innerText`) in chunks to get the full text without truncation:

Run `js/read_jd_chunks.js` via `javascript_tool` (run each line separately and combine results)

**Deduplication check (Step B):** Extract the Job ID from the JD text immediately — it appears as `Job ID : NNNNNN`. Check it against the seen-ID set from Phase 1.
- If already in the set → click "BACK TO LISTING" immediately, log "⏭️ Already seen (ID: NNNNNN)", move to next card. Do not score.
- If not in the set → proceed to filter scoring.

`read_page` / `get_page_text` are fallbacks but `innerText` is faster for long JDs.

**IMPORTANT — No API or URL workarounds:** Do not attempt to fetch job descriptions via the portal's internal API, XHR interception, or any other programmatic method outside of Claude in Chrome tools. The only permitted workflow is clicking DETAILS and reading the loaded page. Truncated descriptions from any other source are not sufficient for scoring.

### Step C: Run Filter Score

Using `filter.md`, score the role across the four dimensions (Role Match, Seniority Fit, Industry Relevance, Geography/Constraints). Check for hard-block conditions first (security clearance not held, explicitly US-only on-site, etc.).

Produce a score out of 10. Decision:
- **≥ 6/10** → proceed to Phase 3 (job-match)
- **4–5/10** → log as borderline, skip (do not apply without human override)
- **< 4/10** → log as skipped, note reason

Click **"BACK TO LISTING"** (use `find` → `left_click` ref) to return to the search results. Do not use browser back or the JOBS nav — the JOBS nav navigates to a fresh `searchJobs` page which discards the fully-loaded card list and requires re-scrolling to reload all cards.

---

## Phase 3 — Job-Match Quick

For each job that passed the filter (≥ 6/10):

Run job-match in **quick mode** using the JD you already have in context — no need to re-fetch. Follow the `skills/job-match/SKILL.md` evaluation exactly (Blocks A + B condensed + Score).

**Recommendation outcomes:**

| Match label | Action |
|-------------|--------|
| Very likely to hear back (≥85) | Apply — proceed to Phase 4 |
| Good odds (70–84) | Apply — proceed to Phase 4 |
| Long shot (55–69) | Apply if score ≥ 60 — proceed to Phase 4; skip if 55–59 |
| Unlikely to clear screening (<55) | Skip — log reason |

For Long shot roles that score 55–59, log as borderline in the run log but do not apply. The user can override after the run if they want.

---

## Phase 4 — Apply Through the Portal

For jobs where job-match recommends applying:

### Step 4.1: Navigate to the Application Form

From the inline DETAILS panel on the search results page, click APPLY — this lands on a **View Job** page (not the form yet). From the View Job page, confirm the job title matches what you evaluated, then click the **Apply** button to reach the actual application form. This is always a two-click sequence: APPLY from DETAILS panel → Apply from View Job page → form loads.

### Step 4.2: Fill the Application Form

The form typically has a "Priority Requirements" section with Yes/No dropdowns and free-text "Briefly describe (2–5 lines)" fields. Occasionally it uses "Years of Experience" + "Last Used Year" dropdowns instead.

**Answering principles:**
- Base every answer on `profile/skills-inventory.md` — this is the hard constraint on proficiency claims
- For Yes/No dropdowns: answer Yes only if the inventory shows Working level or above for that skill
- If the inventory shows Foundational for a required skill, answer No — but always fill in the description field with an honest, constructive statement of what you do have
- Use the writing style from `skills/_shared/writing-style.md`: first person, active voice, no AI-sounding constructions, no banned phrases
- Description field length: 2–4 sentences. Specific. Grounded in real roles from `profile/master-resume.md`
- Never exaggerate or claim experience not supported by the inventory
- **Filling dropdowns (PrimeNG SPAN-based — `form_input` does not work):** Use this pattern for every dropdown:
  1. Open the panel: `javascript_tool` → `document.querySelectorAll('p-dropdown')[N].querySelector('.p-dropdown-trigger').click()` — OR — `left_click` via ref on the trigger button. Both work equally; JS by index is simpler when you know the position.
  2. Wait 0.8 seconds for the panel to render.
  3. Use `find` to locate the specific option by its exact text (e.g. `"> 4 years option in open dropdown"`). The accessibility tree updates correctly after either open method.
  4. `left_click` the option ref to select it.
  5. Before opening the next dropdown, call `document.body.click()` via `javascript_tool` to close any open panel — multiple open panels cause `find` to return options from the wrong list.

- **Years of Experience options vary per question** — they are not always the same set. Always read the open panel items before selecting:

  Run `js/read_dropdown_options.js` via `javascript_tool`

  Options may be absolute values (`1 year`, `2 years`) or ranges (`2 - 4 years`, `> 4 years`, `> 10 years`) — read the actual list and pick the option that best fits the inventory level.

- **Last Used Year field is not always present** — some questions have only a text box, some add a Years dropdown only, some add both Years + Last Used Year. Check `document.querySelectorAll('p-dropdown').length` before trying to fill year dropdowns.

- Use `javascript_tool` to fill text areas (set `.value` and dispatch an `input` event), not `form_input`

**Em-dash sanitization:** Before filling any free-text field, scan your composed answer for em-dashes (—) and replace them with a colon or semicolon. The `type` tool will insert literal em-dashes which violate the writing-style rules. If the field is already filled with an em-dash (e.g. from a prior `type` call), fix it via `javascript_tool`: `ta.value = ta.value.replace(/—/g, ':'); ta.dispatchEvent(new Event('input', {bubbles:true}))`.

**Ambiguous questions — stop and ask:**
If a question asks about a skill, tool, or scenario not clearly covered by `skills-inventory.md` and you can't make a confident honest determination, **stop and surface it to the user**:

> "Pausing on [Job Title] — form question: '[exact question text]'. I'm not sure how to answer this honestly. How would you like me to respond?"

Wait for the user's answer before continuing.

### Step 4.3: Submit

After filling all fields, use `find` + `javascript_tool` to click "Preview My Application". Wait 3–4 seconds for the loading state to resolve to "Submit My Application" — the button label and target change during this loading window; clicking too early submits to the wrong endpoint and fails silently with no confirmation. Call `read_page` to confirm the button has changed, then click Submit.

Note the applicant number from the confirmation screen (read via `read_page`).

### Step 4.4: Navigate Back

The confirmation screen (post-submit) shows **"View More Jobs"** — use `find` → `left_click` ref to return to the search results from there.

Mid-run when returning from a JD view without applying, use **"BACK TO LISTING"** instead — "View More Jobs" only appears on the confirmation screen.

After returning to the search results, continue from the next unprocessed card index.

---

## Phase 5 — Run Log and CSV Update

After completing all cards (or reaching a session cap), produce a run summary:

```
## SI Systems Scout Run — [Date]

### Results

| Job ID | Title (truncated) | Filter | Match Score | Action | Notes |
|--------|-------------------|------------|-------------|--------|-------|
| 152XXX | Senior BA...      | 8/10       | 78 (Good odds) | ✅ Applied | Applicant #N |
| 152XXX | Intermediate DA.. | 5/10       | 65 (Long shot) | ⏭️ Skipped | Long shot |
| 152XXX | Senior DevOps...  | ⛔ Hard-blocked | — | ⛔ Skipped | Title: DevOps |
```

Then update `job-outputs/jobs.csv` for every job processed:
- Applied jobs: status = `applied`, populate Filter_Score, Top_Skills, Match_Score, Match_Label, Posting_URL, Work_Type, Contract_Length, Source = `SI Systems portal`, Job_ID = numeric job ID from the portal; leave Redirect_URL, Search_Terms, Contacted blank
- Skipped jobs (scored): status = `skipped`, populate Filter_Score, Top_Skills, Posting_URL, reason in Notes, Job_ID; leave Redirect_URL, Search_Terms, Contacted blank
- Skipped jobs (borderline long shot, 55–59): status = `skipped`, Notes = "Borderline long shot: [score]", Job_ID; leave Redirect_URL, Search_Terms, Contacted blank
- Hard-blocked: status = `skipped`, Notes = "Hard-blocked: [reason]", Job_ID; leave Redirect_URL, Search_Terms, Contacted blank
- Already-seen (dedup): do not add a new row — the existing row already has the Job_ID logged

---

## Session Management

**Pacing:** After every 3–4 applications, call `read_page` to verify you're still logged in and on the right page. The portal logs out after inactivity.

**If session expires mid-run:** Stop, tell the user "Session expired — please log back in to portal.sisystems.com and let me know when you're ready to continue." Note which job you were on so you can resume from there.

**Card loading:** The portal uses infinite scroll — there is no fixed result cap. Scroll to the bottom (Phase 2) to load all cards before processing. The count stabilises when repeated scrolls stop adding new DETAILS buttons.

**Duplicate check:** Before applying to any job, check `job-outputs/jobs.csv` for an existing row with the same SI Systems job ID or matching company + role. If already applied, skip and note "Already applied".

---

## Hard Constraints (Never Override Without Asking)

- Never claim a higher proficiency level than what `skills-inventory.md` states
- Never skip the 3–4 second wait between "Preview" and "Submit" — the button changes and submitting too early fails silently
- Never apply to a role that requires a security clearance not held (eligible ≠ held)
- Never apply to a role with a hard location block (e.g. US on-site only)
- Always stop and ask if a form question is ambiguous relative to the skills inventory
- Never attempt to fetch job descriptions via API calls, XHR interception, JavaScript injection, or any other programmatic method — always click DETAILS and wait for the full page to load
