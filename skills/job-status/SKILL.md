---
name: status
description: "Fast session context reload. Reads learnings and application tracker, then outputs a formatted job search status summary with a recommended next action."
---

# /status Skill

## Purpose

Reload full session context instantly. Use at the start of any session, after a gap, before running a pipeline, or whenever you need a quick snapshot of where the job search stands.

## Execution Steps

1. Read `job-outputs/jobs.csv` (application tracker)
2. Output the status block below — no preamble, no commentary before the block

## Output Format

```
📊 [Total rows in CSV] jobs tracked | [Count of rows where status is NOT skipped/closed] active (pending, applied, interviewing, interviewed, withdrawn, offer)

📬 Applications ([N] total):

Pending Decision:
| # | Company | Role | Status | Filter Score | Match Score | Location | Date | Posting |
|---|---------|------|--------|--------------|-------------|----------|------|---------|
(only rows with status: pending — sorted by Filter Score descending)
Posting column: link to Posting_File as computer:// link if present; otherwise link to Posting_URL; otherwise blank

🏆 Top Matches (last 14 days):
| # | Company | Role | Match Score | Cold Outreach | Date | Posting |
|---|---------|------|-------------|---------------|------|---------|
(rows from any non-skipped/closed status with a Match_Score, where Date is within 14 days of today — sorted by Match_Score descending, top 10 max)
Cold Outreach column: check job-outputs/cover-letters/ for any file matching cold_outreach_[company]*. Show ✅ if found, blank if not.

⚡ Recommended next action: [one specific suggestion based on current state]
```

## Rules

- **Pending Decision** = only `pending` status. Never include `applied`, `interviewing`, `offer`, or `interviewed` in this table.
- If no pending rows exist, show: `Pending Decision: none`
- **Top Matches** = rows with a non-blank `Match_Score` and `Date` within the last 14 days (from today's date), any status except `skipped`/`closed`. Sort by `Match_Score` descending; show top 10. If no qualifying rows, show: `Top Matches (last 14 days): none`
- **Scoring columns:** Show `Match_Score` as `/100` where present; leave blank if not in CSV. Use same colour coding as job-scout: 🟢 ≥85 | 🟡 70–84 | 🟠 55–69 | 🔴 below 55. Do NOT show Filter_Score in the Top Matches table.
- **Cold Outreach column (Top Matches only):** glob `job-outputs/cover-letters/cold_outreach_[company-slug]*` — show ✅ if any file found, leave blank if none.
- **Posting column:** prefer `Posting_File` — render as `[📄 view](computer://{PROJECT_ROOT}/job-outputs/postings/[filename])` where `{PROJECT_ROOT}` is the absolute path to this project (read from `project_paths.get_project_root()` or infer from the location of `CLAUDE.md`). Fall back to `Posting_URL` as `[🔗 link](url)`. If neither present, leave blank.
- **Recommended next action** must focus on `pending` rows awaiting a decision, pipeline gaps, or upcoming deadlines — never suggest following up on `applied` or `interviewed` rows, and never suggest running `/tailor-resume` or applying to a role that already has status `applied`
- Recommended next action must be specific and actionable — not generic advice
- Do not show applied rows anywhere in the Pending Decision table — not as a separate section either. Key learnings, date heading, and targets section are also excluded.
- learnings.md is not needed — do not read it
- Do not ask any questions. Execute immediately and output the block.
