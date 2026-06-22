---
name: tailored-resume
description: "Generates tailored resumes matched to a specific JD. Trigger on: '/tailored-resume', 'tailor my resume', 'create a resume for this role', or any request to adapt/rewrite a resume for a job. Also handles review-only mode: '/review-resume', 'review this resume', 'run the reviewer on this resume', or any request to critique/improve an existing tailored resume against a JD."
---

## Entry Point — Determine Mode

**Mode A — Draft mode (default):** No existing resume provided. Proceed to Step 1.

**Mode B — Review mode:** The user provides an existing resume AND a JD. Triggers include:
- "review this resume", "run the reviewer on this", "/review-resume"
- Uploading or referencing an existing resume file alongside a JD
- "improve my resume for [role]" when an existing resume is attached or named

In review mode:
1. **Resolve the resume text:**
   - If the user uploaded a `.docx` file: read it from `uploads/` using python-docx (`pip install python-docx --break-system-packages`) to extract plain text
   - If the user uploaded a `.pdf`: extract text with `pdftotext <file> -` (shell) or `pdfinfo` + `pdftotext`
   - If the user pasted plain text: use it directly
   - If the user named a file (e.g., "the Telus resume") or gave a company/role: glob `job-outputs/resumes/` case-insensitively to find the matching `.docx`, then extract its text with python-docx
2. **Resolve the JD:** follow Step 0a exactly — check `jobs.csv` → `Posting_File`, then glob `job-outputs/postings/`, then fall back to a user-supplied URL or pasted text. Never search the web for the posting.
3. **Skip to Step 4.5** (Reviewer Agent) — pass the resolved resume text as `[INSERT FULL RESUME TEXT]`
4. After the reviewer returns, apply feedback (same rules as draft mode Step 4.5), then continue from **Step 6** onward (strategic recommendations → generate files → post-save)

---

## Step 0 — Resolve JD and Match Report from Local Files

**Before any web fetch or search**, resolve the JD and match report from local files.

### 0a — Resolve JD

1. Check `jobs.csv` for a row matching this company + role (case-insensitive).
   - If found, read the `Posting_File` field. If non-empty, read the file from `job-outputs/postings/[Posting_File]` and use it as the JD. Done — do not fetch from the web.
2. If `Posting_File` is blank or no CSV row exists, glob `job-outputs/postings/` case-insensitively for `[company]*[role]*.pdf` or `[company]*[role]*.txt`. If a match is found, read it and use it as the JD. Done — do not fetch from the web.
3. Only if no local file is found: if the user supplied a URL or pasted text directly, use that. If a URL was given, note that you are fetching because no saved posting was found locally.
4. **Never search the web for a job posting.** If no local file exists and no URL or pasted text was provided, ask: "I couldn't find a saved posting for [Company] / [Role]. Please paste the JD or provide the posting URL."

### 0b — Load Match Report

Check `job-outputs/reports/` for an existing match report for this company + role (glob case-insensitively for `match_report_[company]_[role]_*.md` or `match_report_[company]_[role]_*.docx`).

**If found:**
- Read the report and extract:
  - **Gap analysis** (Block B): hard gaps, soft gaps, transferable skills flagged
  - **ATS keywords** (if full mode report): exact terms to incorporate
  - **Positioning notes**: any archetype framing, competitive landscape notes, or interview story priorities
  - **Match Score and label**: note for reference (do not display to user — use internally to calibrate emphasis)
- Use this as a primary input alongside the JD in Steps 1–3. The match report's gap analysis supersedes your own inferences where they conflict — it was produced from a more detailed evaluation.
- Silently note: `📋 Match report loaded: [filename]`

**If not found:** proceed silently with JD only.

---

## Step 1 — Analyse JD

**Application Instructions Check (run first, before extraction):**

Scan the JD for specific application instructions:
- Email-based application (e.g. "send your resume to", "apply by emailing", "forward your CV to [email]")
- Portal-specific requirements (e.g. "only applications via [portal] accepted", "do not apply via LinkedIn")
- Required reference numbers or subject line instructions
- Cover letter explicitly required (not just suggested)

**If found:**
1. Add to the `Notes` field in `jobs.csv` for this row: `Apply via: [instruction summary]` (semicolon-separated from existing notes)
2. Surface to the user before showing any resume content:

```
📬 Application Instructions
[Exact instruction text from JD]
```

**If not found:** proceed silently.

Extract and prioritise:
- Must-have qualifications, key skills, ATS keywords (repeated terms/phrases)
- Soft skills, domain knowledge, company values/cultural signals
- Priority tiers: P1 = deal-breakers, P2 = strongly desired, P3 = nice-to-have

## Step 2 — Map Resume to JD

For each requirement: find direct match, transferable skill, or flag gap. Note unique strengths to lead with.

## Step 3 — Draft Resume

**Professional Summary (2–3 sentences, 50–70 words total):**
- Tell a tight story, not a coverage list. Structure: sentence 1 = who the candidate is (discipline + level); sentence 2 = the specific thing they've done that matches the JD's core problem; sentence 3 = the context or scale that makes it credible (e.g., regulated environment, team size, scope).
- The one thing a hiring manager should walk away knowing after 5 seconds — build every sentence around that, not around comprehensiveness.
- No skill enumeration in the summary. If a skill matters, it belongs in the skills section and in bullets — not here.
- Only include topics explicitly in the JD — no inferred adjacent skills
- Remove industry-specific jargon if the target role is outside that industry (e.g., remove healthcare terminology for non-healthcare roles)
- No parental leave note or career gap explanation in the summary

**Skills Section:**
- Single-line format: **Category:** skill1, skill2, skill3
- Only skills relevant to JD; exact JD terminology; only skills you can substantiate

**Experience:**
- **Bracketed titles:** Role titles in the master resume may include a standardised descriptor in brackets (e.g. "Lead Data Analyst (Data Engineer)"). These brackets exist to map non-standard official titles to industry-standard job title vocabulary — they are not official titles. When tailoring, apply this decision rule:
  1. **Does the bracketed term appear in the JD, or is it the standard industry title for the target role?** If yes → keep it: format as "Official Title (Bracketed Title)".
  2. **Is the official title already a strong match for the target role (or better than the bracketed term)?** If yes → remove the brackets entirely; use only the official title.
  3. **Is the bracketed term from a different domain than the target role?** (e.g., target is a BA role but the bracket says "Data Engineer") → remove the brackets entirely.
  - Default to removal: if in doubt, the official title alone is cleaner than adding noise.
  - Never leave raw brackets in the final resume.
- List roles in reverse chronological order (most recent first)
- Within each role, order bullets from most JD-relevant and strongest to least relevant and weakest
- Action verb + What + How/Why + Result/Impact; quantify everything
- Use JD keywords naturally
- Remove irrelevant content:
  - **Always remove:** data governance terminology if not mentioned in JD
  - **Always remove:** domain-specific jargon from other industries (e.g., platform names, product names, and technical terminology specific to the candidate's prior industry that are not relevant to the target role's domain) — strip these from bullets when the target role is in a different field.
  - **Ask user before removing:** other weak or irrelevant points that don't align with JD requirements
- **Junior role exclusion:** Omit roles that are clearly junior/entry-level (identify from the candidate's profile — typically roles with titles such as "clerk", "assistant", or similar entry-level designations) unless the JD specifies a minimum years-of-experience requirement that cannot be met without them. If including them is needed to satisfy a years-of-experience bar, include only the role title, employer, and dates — no bullets.

**Education:** degrees, relevant certs; coursework only if early career

**Professional Development:**
- List items in reverse chronological order (most recent year first; in-progress items go first)
- Credential name and date/status on one line (e.g. `[Certification Name] | [Year]`)
- Description (if any) on the next line (e.g. `[skills or topics covered]`)
- No description line for certifications that are self-explanatory or status-only (e.g. well-known vendor certs, in-progress certs)
- Example format:
  ```
  [Certification or Program Name] | [Year or Year Range]
  [Optional: brief description of skills covered]

  [Self-explanatory Certification] | [Year]

  [In-progress Certification] | In progress
  ```

**Optional sections** (only if relevant): Certifications, Publications, Awards, Projects

**ATS rules:** standard headings; no tables/graphics/headers/footers; standard fonts; no acronyms unless in JD

**Formatting:** read `skills/_shared/formatting.md` before generating — do not redefine font sizes, colours, or margins inline. Use `add_company_date_row()` helper. Font size: always `Pt(n)`, never twips. Use `keep_with_next()` on all headings and company/date rows.

## Step 4 — Writing Style

**Read `skills/_shared/writing-style.md` before writing any content.** All tone, voice, banned language, and the interview backtrack test are defined there. Do not redefine them here.

## Step 4.5 — Reviewer Agent

Read `skills/_shared/reviewer-agent.md`. Spawn a `general-purpose` sub-agent using
the Resume Reviewer Prompt. Pass the full JD text and the full draft resume text
inline — do not reference files on disk for these.

Once the reviewer returns its feedback, apply each item using judgment:
- Content quality audit (Section A): apply ✂ cuts and ✏ rewrites; show a brief
  summary of what changed
- Missed keywords: add to the most relevant existing bullet where evidence supports it
- Stretch framing: apply the safer reframe or remove the claim
- Tone and voice: fix per writing-style.md rules
- Bullet strength: rewrite or cut low-signal bullets as suggested

The revised draft is what gets generated in Step 7. Never generate files before the reviewer pass is complete.

## Step 5 — Preview

~~Skip — do not show preview. Proceed immediately to Step 6.~~

## Step 6 — Strategic Recommendations

After showing the preview, briefly note:
- **Gaps:** unmet requirements + mitigation (reframe, course, project)
- **Verify before submitting:** Flag any claims in the resume that might be overstated or hard to defend in an interview. Look for:
  - Ownership language ("led", "owned", "drove", "built") on work that was shared, supported, or partial — if the candidate was a contributor rather than the decision-maker, note it
  - Skill-level signals ("expert in", "deep experience with", "proficient") for tools or methods where the evidence is thin or dated — flag if the JD is likely to probe this in a technical screen
  - Metrics or impact claims that are approximate, inferred, or hard to source — note if they'll need to reconstruct the story
  - Scope inflation (e.g. "company-wide" or "cross-functional" when the actual reach was narrower)

## Step 7 — Generate Files

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
  --company "[normalised-company]" \
  --role "[normalised-role]" \
  --content-file /tmp/resume_content.py \
  --output-dir job-outputs/resumes/
```

The script handles: formatting, metadata, PDF conversion, page-count check, and trim loop (drops weakest bullets oldest-first until ≤ 2 pages). On success it prints `SAVED:/path` for each file. Present both `.docx` and `.pdf` links.

## Step 8 — Post-Save (automatic, no prompt)

1. Run save-job-posting on JD (skip if posting already exists for this company + role)
2. Update `job-outputs/jobs.csv` for this company + role:
   - **If a row already exists** (match on Company + Role, case-insensitive): update it in-place — set `Status` → `applied`, `Resume_Used` → the `.docx` filename, and `Posting_File` → the posting filename from save-job-posting. Do NOT append a new row. Do not overwrite other already-populated fields (e.g., `Filter_Score`, `Posting_URL`, `Top_Skills`).
   - **If no row exists**: append a new row with `Status` = `applied`, `Resume_Used` set to the `.docx` filename, and `Posting_File` set to the posting filename from save-job-posting.
3. Read the `Posting_URL` field from `jobs.csv` for this company + role row
4. Confirm: "✅ Posting saved + resume saved. Application logged as applied." — if `Posting_URL` is non-empty, append it on the next line: "🔗 Posting URL: [url]"
