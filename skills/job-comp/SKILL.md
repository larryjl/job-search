---
name: job-comp
description: "Standalone compensation research skill. Researches Canadian market salary data for a role, outputs a Block F comp table + negotiation anchor, and appends it to the existing match report if one exists. Trigger on: '/job-comp', 'research comp', 'what's the salary range', 'what should I negotiate', 'comp research for this role'."
---

## Step 0 — Input

Identify the role to research. In order of priority:

1. **In-session context** — if a job-match was just run, use that role + company + location. Do not ask.
2. **Named role** — if the human says "/job-comp for [Role] at [Company]", use that.
3. **Nothing** — ask once: "Which role and company should I research comp for?"

Also read `profile/master-resume.md` to inform the negotiation anchor (seniority, years of experience, domain).

---

## Step 1 — Cache Check

Before any web search, check `.claude/memory/learnings.md` under `## Compensation Research`:

1. Find any entry where **role title is similar** (same or adjacent level) **and geography matches** (e.g., Calgary, Alberta, Canada Remote)
2. If a match exists and `Last updated` is **within 90 days** of today:
   - Output: `💾 Using cached comp data for [Role] — [Geography] (last updated [date])`
   - Skip web research; populate the Block F table from cache
   - Still derive the negotiation anchor from cached data + this specific JD's listed salary (if known)
3. If no match or cache is expired (>90 days): proceed to Step 2

---

## Step 2 — Domain Access Gating

Before searching, check approved domains under `## job-comp` in `.claude/config/domains.md`.

Planned research domains: `glassdoor.com`, `levels.fyi`, `linkedin.com`, `blind.com`, `indeed.com`, `ca.indeed.com`, `talent.com`, `payscale.com`

For each domain you plan to use:
1. If **NOT approved**:
   - Output: `🔒 Domain access request: [domain]`
   - Ask: "Can I search [domain] for salary data? (yes / no)"
   - If yes: Add to `## job-comp` section in `domains.md`, proceed
   - If no: Mark this source as skipped
2. If **approved**: Proceed silently

---

## Step 3 — Research

### Canadian Market Baseline (mandatory)

All figures are based on the **Canadian market** regardless of where the role is posted or the company is headquartered.

- All salary figures in CAD
- Search queries must include Canada/province context (e.g., "Senior Business Analyst salary Canada", "Product Manager salary Alberta Canada")
- If the role is explicitly US-only but candidate works from Canada: research Canadian equivalent market rate anyway
- If only USD data found: convert using approximate current exchange rate, flag clearly (e.g., "converted from USD at ~1.38 CAD/USD")
- Never report raw USD figures as the market range — always present CAD equivalent

Search approved domains only. Do not invent figures.

---

## Block F — Comp & Market Demand

| Data point | Finding | Source |
|------------|---------|--------|
| Market salary range (CAD) | $X – $Y CAD | |
| Company comp reputation | generous / average / below market | |
| Role demand trend | growing / stable / shrinking | |
| Company financial health | | |
| Listed salary | from JD or "Not disclosed" | JD |

**Negotiation anchor:** [specific CAD target based on Canadian market data + candidate seniority + JD listed salary if known]

---

## Step 4 — Cache Write-Back (mandatory after any web research)

After completing web research (skip if cache was used), append to `## Compensation Research` in `.claude/memory/learnings.md`:

```
[Role title] — [Geography/context]: [Min CAD] - [Max CAD] | Sources: [domains used] | Last updated: [YYYY-MM-DD]
```

- Log the role title generically enough to be reusable (e.g., "Senior Business Analyst — Calgary, AB" not the company's exact job title)
- If multiple geographies researched, log each as a separate line
- Confirm: `💾 Comp data cached for future runs.`

---

## Step 5 — Append to Match Report (if it exists)

Check `job-outputs/reports/` for an existing match report matching this company + role (case-insensitive glob: `match_report_[company]_[role]_*.md`).

**If a report exists:**
1. Open the file
2. Append Block F as the final section, after all existing content:

```markdown
---

## Block F — Comp & Market Demand

[paste the full Block F table and negotiation anchor]
```

3. Save the file
4. Confirm: `💾 Comp data appended to match_report_[company]_[role]_[date].md`

**If no report exists:**
- Output Block F in chat only
- Note: "No match report found for this role. Run /job-match-full first to create one."

---

## Step 6 — Update jobs.csv

If a row exists for this company + role in `job-outputs/jobs.csv`:
- Populate `Market_Min_CAD` and `Market_Max_CAD` from the researched market range (convert hourly to annual if needed: rate × 2080)
- Leave other fields unchanged
- Confirm: `✅ jobs.csv updated with comp targets.`

If no row exists: skip silently.

---

## After Completion

```
→ /tailor-resume  — tailored resume with comp-informed positioning
→ /cover-letter-generator     — cover letter with salary expectations angle
→ /interview-prep             — prep kit including comp negotiation talking points
```

---

## Rules

- Never fabricate salary data — say "no reliable data found" if unavailable
- Never report USD as the market range — always convert to CAD
- Only search approved domains; ask permission for new ones
- Block F is always the last section of the match report — append after all other content
- If cache is valid, use it; do not re-search within 90 days for the same role + geography
