# Adzuna Queue Batch — Sub-Agent Instructions

You are processing one batch of up to 50 unprocessed items from the Adzuna job queue. This is a sub-agent invocation. You have a single job: process the batch, write all results, and return a short status string. No summaries, no explanations beyond the status line.

---

## Project Root

`/path/to/job-search` (your local project root)

All paths below are relative to this root.

---

## Step 1 — Load Context

Read the following files before doing anything else:

- `CLAUDE.md` — master instructions
- `profile/targets.md` — location constraints, salary floor, role preferences
- `.claude/memory/learnings.md` — compensation cache, match patterns
- `.claude/memory/scout-cache.md` — verified postings cache (for dedup)
- `.claude/memory/raw-results-queue.json` — the queue (your primary input)
- `profile/master-resume.md` — required for job-match scoring
- `profile/skills-inventory.md` — required for job-match gap analysis
- `skills/filter/SKILL.md` — filter scoring rubric
- `skills/job-match/SKILL.md` — job-match execution rules
- `job-outputs/jobs.csv` — for deduplication and write-back

---

## Step 2 — Pull Your Batch

From `raw-results-queue.json` → `adzuna.items`, take the first 50 entries where `processed: false` (FIFO — preserve insertion order).

**Immediately** mark all 50 as `processed: true` in the queue file and write it back before doing any Chrome work. This prevents reprocessing if the session is interrupted.

Count and note: how many unprocessed remain after marking your batch (total unprocessed minus 50).

---

## Step 3 — Process Each Item

For each item in your batch, run the following sequence. Process items one at a time — do not batch Chrome calls across items.

### 3a — Dedup check
Check `job-outputs/jobs.csv` `Posting_URL` column for the `redirect_url` (case-insensitive). Also check `scout-cache.md` Verified Postings Cache.
- Status `closed` or `skipped` → drop silently
- Any other status → drop silently (already tracked)
- No match → proceed

### 3b — API description pre-screen
Read the `description` field (≤500 chars). Apply hard excludes from `targets.md`:
- Explicit US-only location or US work auth required → drop, note `❌ Hard exclude (description): [reason]`
- Role title clearly out of scope (Software Engineer, DevOps, GIS, SAP, etc.) → drop, note `❌ Hard exclude (title)`
- Salary clearly below floor if stated → drop, note `❌ Hard exclude (salary)`
- When in doubt → proceed to Chrome

### 3c — Chrome redirect resolution + full JD extraction
Follow steps Z4 Step 1–4 from `skills/scout-adzuna/SKILL.md` exactly:
1. `navigate` to `redirect_url` → wait 2–3s → `get_page_text` (extracts JD from Adzuna detail page)
2. Click "Apply for this job" → handle modal via `javascript_tool` → resolve canonical URL
3. Classify: ✅ Verified / ❌ Dead / ⚠️ Unverified (per Z4 Step 3 definitions)
4. Capture expiry/deadline if present

Dead → drop; add to Dead URL Cache in `scout-cache.md`.
Unverified → keep with flag; use Adzuna redirect_url as canonical.

### 3d — Full location filter
Apply Step 5 from `skills/scout-adzuna/SKILL.md` on the full JD text.
Hard exclude → drop with note.
Flags → keep, note in CSV Notes field.

### 3e — Filter score
Run `skills/filter/SKILL.md` on the full JD. Score /10.
- ✅ Verified → score and write
- ⚠️ Unverified → leave Filter_Score blank; Notes: `⚠️ Unverified — JD not retrieved; review and verify before proceeding`

### 3f — Write to jobs.csv
For every item that reached scoring (including below-threshold):
- Status: `pending` if ≥6/10; `skipped` if below
- Filter_Score, Top_Skills, Posting_URL (canonical), Work_Type, Contract_Length, Source: `scout-adzuna`
- Notes: skip reason if below threshold; location flags if any
- Skip if row already exists for same Posting_URL

For unverified: status `pending`, blank Filter_Score, Notes: `⚠️ Unverified — JD not retrieved; review and verify before proceeding`. Do NOT use `skipped` — skipped items are suppressed from review queues and the status command.

### 3g — Auto quick job-match (≥6/10 only)
For every item scoring ≥6/10, immediately run quick job-match per `skills/job-match/SKILL.md`:
- Use the full JD already extracted in 3c — do not re-fetch
- Step 0.5a saves the posting file automatically
- Step Final writes Match_Score and Match_Label to the existing `jobs.csv` row
- Do NOT output the match result to chat — run silently and write to CSV only
- Do NOT save a match report file (quick mode only)

### 3h — Update scout-cache.md
Append all processed items to `## Verified Postings Cache`:

| Company | Role | URL | Source | Status | Filter Score | Cached | Search Terms |

Also append dead URLs to `## Dead URL Cache`.

---

## Step 4 — Write Queue File

After all 50 items are processed, write the complete updated `raw-results-queue.json` back to disk (all items, with `processed` flags current). This is the source of truth — always write the full file.

---

## Step 5 — Append Scout Cache Run Entry

Prepend a new run block to `## Scout Cache` in `scout-cache.md`:

```
### Run: [YYYY-MM-DD] | Mode: Adzuna | Batch: queue-drain | Items: [N processed] | Queue remaining: [N]
Chrome verified: [N] | Dead dropped: [N] | Hard excluded (pre-Chrome): [N] | Unverified: [N] | Passed threshold (≥6/10): [N]
Auto job-match run: [N]
```

---

## Step 6 — Return Status

Return exactly this format and nothing else:

```
BATCH DONE. Processed: [N] | Passed threshold: [N] | Queue remaining: [N]
```

If queue remaining is 0, append ` | QUEUE EMPTY`.

---

## Rules

- Never fabricate scores — score only from actual JD text
- Never ask the user questions — make decisions per the skill rules
- Chrome is required — if unavailable, mark all items ⚠️ Unverified and write to CSV accordingly, then return status
- Write all files before returning status — do not return early
- Do not output match results, JD text, or intermediate scoring to chat
- If a file write fails, note it in the status line: `| WRITE ERROR: [file]`
