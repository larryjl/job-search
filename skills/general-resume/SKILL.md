---
name: general-resume
description: "Generates a general-purpose resume optimised for a target role type and industry, without a specific job posting or company. Trigger on: '/general-resume', 'make a general resume for [role]', 'create a resume for [industry] [role] roles', or any request to build a resume without a specific company or job description."
---

## Step 0 — Resolve Inputs

**Role type and industry** are resolved in this order:

1. Check if the user specified them at invocation (e.g. `/general-resume Data Engineer, SaaS`).
2. If not specified → read `profile/master-resume.md` and `profile/targets.md`, then confirm:
   "Building a general resume for **[role(s)]** in **[industry/industries]** — does this sound right, or would you like to target a different combination?"
   Wait for confirmation or correction before proceeding.

**Store as variables for the rest of the skill:**
- `TARGET_ROLE` — e.g. `Senior Data Analyst`
- `TARGET_INDUSTRY` — e.g. `Healthcare / Health Tech`

---

## Step 1 — Research Archetype Requirements

Search for common job description patterns for `TARGET_ROLE` in `TARGET_INDUSTRY`.

**Domain gating:** Before any web search, check `.claude/config/domains.md`. Unapproved domains trigger a permission request. If approved, add to the appropriate skill section in `domains.md`.

**Search strategy (run in order; stop when you have enough signal):**
1. `"[TARGET_ROLE]" "[TARGET_INDUSTRY]" job requirements skills 2024 OR 2025`
2. `"[TARGET_ROLE]" job description common requirements site:linkedin.com OR site:indeed.com OR site:glassdoor.com`
3. If useful for positioning the Professional Summary seniority level: check the `## Compensation Research` section of `.claude/memory/learnings.md` before running a salary search.

**Synthesise into a Synthetic Archetype Profile:**

Build an internal (not shown to user) snapshot of what a strong posting for `TARGET_ROLE` in `TARGET_INDUSTRY` typically requires:
- Must-have qualifications (P1 — appear in majority of postings)
- Commonly desired skills (P2 — appear in 50%+ of postings)
- Industry-specific context and terminology
- Recurring ATS keywords (exact phrases that appear repeatedly)
- Seniority signals appropriate to the target level

This profile replaces the JD in all subsequent steps.

---

## Step 2 — Map Resume to Archetype

Using the Synthetic Archetype Profile and `profile/master-resume.md`:
- For each P1 requirement: find a direct match, transferable skill, or flag as gap.
- Note unique strengths to lead with in the summary.
- Identify industry-specific jargon to include or exclude based on whether the archetype is inside or outside that domain.

---

## Step 3 — Draft Resume

**Professional Summary (2–3 sentences):**
- Lead with discipline and experience level ("Senior data professional with 8 years…" not "Consultant with…")
- Reflect the archetype's industry context naturally — use the industry's language where it signals fit
- If master resume notes a parental/family leave gap, close with: "Returning to the field after caring for a new child."
- Remove industry-specific jargon if the target archetype is outside that domain

**Skills Section:**
- Single-line format: **Category:** skill1, skill2, skill3
- Only skills relevant to the archetype; use exact archetype terminology; only list skills you can substantiate from the master resume

**Experience:**
- List roles in reverse chronological order (most recent first)
- Within each role, order bullets from most archetype-relevant and strongest to least relevant and weakest
- Action verb + What + How/Why + Result/Impact; quantify everything
- Use archetype keywords naturally throughout
- Remove irrelevant content:
  - **Always remove:** data governance terminology if not in the archetype profile
  - **Always remove:** domain-specific jargon from other industries (e.g. platform names, product names, and technical terminology specific to the candidate's prior industry that are not relevant to the target archetype's domain) — strip these when the target archetype is in a different field.
  - **Ask user before removing:** other weak or irrelevant bullets that don't align with archetype requirements
- **Junior role exclusion:** Omit clearly junior/entry-level roles (identify from the candidate's profile — typically roles with titles such as "clerk", "assistant", or similar entry-level designations) unless the typical years-of-experience bar for this role type cannot be met without them. If included, show only role title, employer, and dates — no bullets.

**Education:** degrees, relevant certifications; coursework only if early career

**Professional Development:**
- Credential name and date/status on one line (e.g. `[Certification Name] | [Year]`)
- Description (if any) on the next line (e.g. `[skills or topics covered]`)
- No description line for self-explanatory or status-only credentials
- Example:
  ```
  [Certification or Program Name] | [Year or Year Range]
  [Optional: brief description of skills covered]

  [Self-explanatory Certification] | [Year]

  [In-progress Certification] | In progress
  ```

**Optional sections** (only if relevant to archetype): Certifications, Publications, Awards, Projects

**ATS rules:** standard headings; no tables, graphics, headers, or footers; standard fonts; no acronyms unless they appear in the archetype keyword list

**Formatting:** read `skills/_shared/formatting.md` before generating — do not redefine font sizes, colours, or margins inline. Use `add_company_date_row()` helper. Font size: always `Pt(n)`, never twips. Use `keep_with_next()` on all headings and company/date rows.

---

## Step 4 — Writing Style

**Read `skills/_shared/writing-style.md` before writing any content.** All tone, voice, banned language, and the interview backtrack test are defined there. Do not redefine them here.

Bullet discipline: each bullet = one archetype-relevant fact. Cut or rewrite anything the archetype profile doesn't call for. If a bullet uses a semicolon to join two separate statements, split it into two bullets.

---

## Step 5 — Preview Gate (MANDATORY)

Show the full plain-text resume in a code block with all formatting rules applied. Ask:

"Does this look good? Type **yes** to save, or tell me what to change."

**Do not generate any file until confirmed.** Iterate until confirmed.

**Formatting rules to apply in preview:**
- Section headings in CAPS
- Company/date on one line (tab-spaced visually: `Company, Location` [TAB] `Date Range`)
- Professional Development: bold credentials, blank lines between items
- Bold all role titles and credential names
- Preserve bullet structure exactly as it will appear in the final document

---

## Step 6 — Strategic Observations (MANDATORY, before file generation)

After preview and before generating files, note:
- **Archetype strengths:** where this resume is well-positioned for the target role type
- **Gaps vs. archetype:** unmet common requirements + mitigation suggestions (reframe, course, project)
- Offer to iterate: adjust tone, add/remove sections, or produce an alternate version for a different seniority level or industry variant

Then ask: "Does this look good? Type **yes** to save, or tell me what to change."

---

## Step 7 — Generate Files

**Output naming convention:**
- Pattern: `resume_[role-type]_[industry]_[YYYY-MM-DD]`
- Role type and industry: lowercase with hyphens
- Examples:
  - `resume_senior-data-analyst_health-tech_2026-05-06.docx`
  - `resume_data-engineer_saas_2026-05-06.docx`
  - `resume_analytics-manager_public-sector_2026-05-06.docx`

Run banned-words check first (scan draft text against `skills/_shared/writing-style.md`). If hits found: rewrite silently, re-check, then proceed.

Serialize the reviewed resume content to `/tmp/resume_content.py` using this format:

```python
content = {
    "contact_line": "[City, Province | email | phone | linkedin]",
    "summary": "...",
    "skills": [
        {"category": "[Category]", "items": ["skill1", "skill2"]},
    ],
    "experience": [
        {
            "title": "[Job Title]",
            "company": "[Company Name]",
            "location": "[City, Province]",
            "dates": "[Start] – [End]",
            "bullets": ["[Bullet 1]", "[Bullet 2]"],
        },
    ],
    "education": [
        {
            "degree": "[Degree]",
            "institution": "[School]",
            "location": "[City, Province]",
            "dates": "[Year Range]",
            "details": [],
        }
    ],
    "prof_dev": [
        {"credential": "[Cert Name] | [Year]", "description": "[description or None]"},
    ],
    "optional_sections": [],
}
```

**Order bullets best-to-worst within each role** — the trim loop drops from the end.

Then run:
```bash
python3 skills/tailor-resume/generate_resume.py \
  --company "[role-type]" \
  --role "[industry]" \
  --content-file /tmp/resume_content.py \
  --output-dir job-outputs/resumes/general/
```

The script handles: formatting, metadata, PDF conversion, page-count check, and trim loop. Prints `SAVED:/path` for each file.

---

## Step 8 — Confirm (No Logging)

This skill does not log to `jobs.csv` and does not run `save-job-posting` (there is no specific posting to save).

Output confirmation:

"✅ General resume saved:
- `[filename].docx` → [link]
- `[filename].pdf` → [link]

This resume targets **[TARGET_ROLE]** roles in **[TARGET_INDUSTRY]**. Use `/tailor-resume` when you have a specific job posting to tailor from this base."
