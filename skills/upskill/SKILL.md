---
name: upskill
description: "Analyses match reports to identify skill gaps and produce a prioritised heatmap. Optionally generates a web-searched learning plan. Trigger on: '/upskill', '/upskill --plan', 'what skills am I missing', 'skill gaps', 'what should I learn', or '/upskill <URL or JD text>' for a single role."
---

## Step 0 — Detect Mode and Options

**Mode:**
- `/upskill` → **aggregate mode**: analyses all match reports in `job-outputs/reports/`
- `/upskill <URL or pasted JD>` → **targeted mode**: analyses a single job posting

**Options:**
- `--plan` → also run Step 5 (learning plan with web-searched resources)
- Without `--plan` → skip Step 5; heatmap only

If the user says "with learning plan" anywhere in the trigger, treat it as `--plan`.

Store the mode and plan flag before proceeding.

---

## Step 1 — Load Data

### Both modes
Read `profile/master-resume.md` to establish the candidate's current skill baseline.
Extract all skills, tools, technologies, domain knowledge, and methods mentioned anywhere
in the resume. This is the set used to diff against in Step 2.

### Aggregate mode
1. Read `job-outputs/jobs.csv`.
2. Check `job-outputs/upskill/` for the most recent previous aggregate report
   (`report-YYYY-MM-DD.md`) — if one exists, load it for the diff in Step 6.

**Backfill missing `Top_Skills`:** For any row where `Top_Skills` is blank and a
corresponding match report exists in `job-outputs/reports/`:
- Read the match report and extract the top 3 skills most emphasized in the JD
  (same logic as the filter skill uses at scout time).
- Write the extracted skills back into the `Top_Skills` column for that row in
  `jobs.csv`. Use pipe-separated format (e.g. `dbt | Snowflake | SQL`).
- Do this for all such rows before proceeding. This is a one-time repair that makes
  future runs faster.

After backfill, the working dataset for Step 2 is the `Top_Skills` column across all
rows in `jobs.csv` that have a `Match_Score` (i.e. a match report was run).

### Targeted mode
- If a URL was provided: fetch the job posting via web search or web_fetch.
- If JD text was pasted: use it directly.
- Extract: job title, company, required skills, preferred skills, responsibilities,
  domain context.
- No CSV or match report data is used in targeted mode.

---

## Step 2 — Hard Skill Diff

Extract required and preferred skills from each source, then remove anything already
present in the candidate's profile.

### Aggregate mode

Using the `Top_Skills` column from `jobs.csv` (backfilled in Step 1):

1. Parse each row's `Top_Skills` into individual skill tokens.
2. Count how many rows mention each skill (raw frequency).
3. Remove any skill that is already present in the candidate profile
   (`profile/master-resume.md`). Be generous — if the profile mentions a skill in any
   form (e.g. "Python" covers "Python scripting"), remove it.

Rank remaining skills by frequency descending. This is the **hard skill gap list**.

Note: unlike the previous report-parsing approach, this method does not distinguish
❌ Gap from ⚠️ Partial — `Top_Skills` is a demand signal (what the JD wants), and the
gap is inferred from absence in the profile. This is sufficient for heatmap prioritisation.

### Targeted mode

Extract the explicit required and preferred skills from the fetched or pasted posting.
List required skill gaps before preferred skill gaps, then sort alphabetically within
each group. No fit weighting — equal weight for all gaps.

Diff against the candidate profile and remove anything already present.

---

## Step 3 — LLM Synthesis

Reason holistically about gaps the hard skill diff would miss. Consider:

- **Domain knowledge gaps**: Does the candidate lack familiarity with the industry,
  domain, or problem space the jobs operate in?
- **Soft skill gaps**: Do the postings emphasise ways of working, communication styles,
  or leadership expectations the profile doesn't address?
- **Tooling and process gaps**: Frameworks, cloud services, methodologies (e.g. MLOps
  practices, CI/CD, data governance frameworks) that appear across jobs but are absent
  from the profile.
- **Credential gaps**: If multiple postings list a certification as preferred or
  required, flag it.

Tag each synthesised gap as one of: `[domain]`, `[soft]`, `[tooling]`, or `[credential]`.

Do not duplicate gaps already captured in Step 2.

In targeted mode, treat all synthesised gaps as arising from a single posting.

---

## Step 4 — Gap Heatmap

**Always print the heatmap before anything else.** Do not proceed to Step 5 or 6
until the heatmap is shown.

Combine Step 2 and Step 3 results into a single prioritised table. Assign priority:

| Priority | Criteria |
|----------|----------|
| **Critical** | Hard skills with high frequency/weight scores, or domain gaps appearing across most reports |
| **High** | Hard skills with moderate scores, or soft/tooling gaps appearing consistently |
| **Medium** | Lower-frequency hard skills, or synthesised gaps from fewer roles |
| **Low** | One-off mentions or minor nice-to-haves |

In targeted mode: required skill gaps → Critical or High; preferred skill gaps →
Medium; inferred LLM synthesis gaps → Medium or Low.

**Output format:**

```
## Gap Heatmap — [YYYY-MM-DD]
Mode: Aggregate ([N] reports analysed) | Targeted: [Job Title] @ [Company]

| Priority | Skill / Area | Type | Source |
|----------|-------------|------|--------|
| Critical | [skill] | Hard | [N] reports, score [X] |
| High | [skill] | Tooling | LLM synthesis |
| Medium | [skill] | Hard | [N] reports, score [X] |
| Low | [skill] | Credential | LLM synthesis |
```

After printing the heatmap, if `--plan` was not specified, ask:
> "Want a learning plan for any of these gaps? Say **yes** or **/upskill --plan** to generate one."

If the user says yes at this point, proceed to Step 5 before saving.
Otherwise skip to Step 6.

---

## Step 5 — Learning Plan (only if --plan specified or confirmed)

For every **Critical** and **High** gap (and **Medium** gaps if fewer than 5 total
gaps exist), produce a learning entry.

### For each gap:

1. **Run a WebSearch** to find current, highly-rated study resources. Use queries like:
   - `"best [skill] course 2026 site:reddit.com OR coursera.org OR udemy.com"`
   - `"learn [skill] for [domain] 2026 recommendations"`
   Include the current year in every query to avoid stale results.

2. **Pick 2–3 resources**. Prefer:
   - Courses with hands-on labs over lecture-only content
   - Official documentation for tooling gaps
   - Books or structured curricula for domain knowledge gaps
   - For each resource: name, URL, and one-line reason why it fits

3. **Write a study direction** tailored to the candidate's existing background.
   Be specific about what to skip and where to start (e.g. "You already know SQL —
   skip the data modelling basics module, start at query optimisation").

4. **Estimate time to working proficiency** (e.g. "~20h"). Err toward more rather
   than less.

### Group by theme

Group entries under theme headings rather than listing alphabetically. Example themes:
Cloud & Infrastructure, Data Engineering, Analytics & BI, Domain Knowledge,
Certifications, Soft Skills & Leadership.

**Example entry format:**
```
### Cloud & Infrastructure

**dbt (data build tool)** `[Hard]` — ~15h
- [dbt Learn — Getting Started](https://courses.getdbt.com) — free, official, hands-on
- [dbt Fundamentals on dbt Learn](https://courses.getdbt.com/courses/fundamentals) — covers models, tests, and docs

Study direction: You already write SQL well — skip the relational database intro. Start
at models and materialisation strategies. Focus on ref() patterns and testing before
touching advanced features like macros.
```

**Never fabricate resources.** Only cite resources found via actual WebSearch results.
Do not invent course names, URLs, or authors.

---

## Step 6 — Save Report

Assemble the full report in this order:

```markdown
# Upskill Report — YYYY-MM-DD
**Mode:** Aggregate ([N] reports analysed) | Targeted: [Job Title] @ [Company]

---

## Since Last Report
<!-- Aggregate mode only. Omit entirely in targeted mode or if no previous report exists. -->
**Gaps closed** (skills added to profile since [previous date]):
- ...

**New gaps** (requirements appearing in reports since [previous date]):
- ...

---

## Gap Heatmap

| Priority | Skill / Area | Type | Source |
|----------|-------------|------|--------|
...

---

## Learning Plan
<!-- Only present if --plan was run. Omit section entirely otherwise. -->

### [Theme]

**[Skill]** `[Type]` — ~Xh
- [Resource](url) — reason

Study direction: ...

---
```

**Save location:**
- Aggregate: `job-outputs/upskill/report-YYYY-MM-DD.md`
- Targeted: `job-outputs/upskill/report-YYYY-MM-DD-[company]-[role].md`
  - Slugify: lowercase, spaces → hyphens, strip special characters
  - Example: `job-outputs/upskill/report-2026-05-21-telus-senior-data-analyst.md`

**Path resolution** — use this helper to locate the project root at runtime:

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../lib'))
from project_paths import get_project_root

UPSKILL_DIR = os.path.join(get_project_root(), "job-outputs", "upskill")
os.makedirs(UPSKILL_DIR, exist_ok=True)
```

**Since Last Report logic** (aggregate mode only): if a previous aggregate report was
loaded in Step 1, compute:
- **Gaps closed**: any skill in the previous report's heatmap now present in
  `profile/master-resume.md`
- **New gaps**: any skill in the current heatmap not in the previous report

If no previous report exists, omit the "Since Last Report" section from the saved report entirely.

After saving, confirm:
> "Report saved to `job-outputs/upskill/[filename].md`."

---

## Rules

- **CSV-first in aggregate mode.** Use `Top_Skills` from `jobs.csv` as the primary data
  source. Only read match reports when `Top_Skills` is blank for a row — then backfill
  the CSV and do not re-read that report on future runs.
- **Print the heatmap first.** Always show the heatmap before the learning plan or
  save step.
- **Never fabricate resources.** Learning plan resources must come from actual
  WebSearch results.
- **Be generous with profile matching.** If a skill appears in the candidate profile
  in any form, do not flag it as a gap.
- **Low-priority gaps:** list in the heatmap for completeness, but do not generate
  study resources for them in the learning plan.
- **Always save the report** — do not skip the save step even if the user seems
  satisfied with the heatmap output.
