---
name: job-match
description: "Job evaluation in two modes. The Match Score predicts callback likelihood for a cold portal application (on-paper resume-to-JD screening match) — not career fit, growth, or comp. Quick mode (/job-match): Role snapshot + top gaps + callback score + label — fast decision signal, no file save. Full mode (/job-match-full): all blocks including positioning strategy and ATS keywords, saves report + updates CSV. Comp research is a separate skill (/job-comp). Trigger on: '/job-match', '/job-match-full', 'evaluate this job', 'score this role', 'how do I match', 'will I hear back', or when a JD is shared for assessment."
---

## Step 0 — Input & Mode Detection

**Mode:**
- `job-match`,  `job-match-quick`, → **Quick mode** (Blocks A + B condensed + Score only; saves `.md` report + updates CSV)
- `job-match-full` → **Full mode** (Blocks A–D + Score; saves `.docx` report + updates CSV)

**Input:**
- JD pasted → proceed
- URL → fetch via web search, then proceed
- Table row → extract Title, Company, Location, Description, Work Type, Employment Type
- Nothing → ask: "Paste the job posting or share the URL."

**Archetype** (classify into one, or flag hybrid):

| Archetype | Key signals |
|-----------|-------------|
| Builder | build, ship, engineer, hands-on, 0-to-1, IC |
| Consultant | client, stakeholder, advise, solutions, pre-sales |
| Product | discovery, roadmap, OKRs, user research, PM |
| Operator | process, efficiency, systems, cross-functional, ops |
| Manager | direct reports, hiring, performance, P&L, director |
| Specialist | deep domain: AI/ML, data, legal, finance, security |

Archetype drives proof point selection, founder framing, and interview story priorities.

---

## Step 0.5a — Auto-Save Job Posting

Check `job-outputs/postings/` for an existing file for this Company + Role. If not found, save it using `save_job_posting.py`:

- **Pasted text or text extracted via Chrome (`get_page_text`):** `--input-type pasted` → saves as `.docx`
- **Non-LinkedIn URL:** use `url_to_pdf()` from `skills/lib/pdf_converter.py` → saves as `.pdf`
- **LinkedIn URL:** use `save_linkedin_posting.py` → saves as `.docx`

Never write a `.txt` file — all output must be `.docx` or `.pdf`.

This applies to **both Quick and Full mode**, and to all input types (pasted text, URL, table row).

---

## Step 0.5b — Load Skills Inventory

Before running any evaluation blocks, read `profile/skills-inventory.md`.

This file is a **hard constraint** on proficiency claims. When scoring:
- If a skill appears in the inventory, use the stated level — do not infer a higher level from resume project descriptions or job titles
- If a JD requires a level above what the inventory states, treat it as a gap regardless of how the resume reads
- If a skill is not in the inventory, infer level from resume context as normal (but note the uncertainty)

Level mapping to JD language:
| Inventory level | JD equivalent |
|----------------|---------------|
| Foundational | "exposure to", "familiarity with" |
| Working | "experience with", "working knowledge" |
| Proficient | "proficient in", "strong [skill]" |
| Advanced | "expert", "advanced", "5+ years" |

Apply this constraint in Block B (gap analysis) and the Required Skills & Tools dimension of the Match Score.

---

## Step 0.5c — Application Instructions Check

After saving the posting (Step 0.5a), scan the JD text for specific application instructions:

**Look for:**
- Email-based application (e.g. "send your resume to", "apply by emailing", "forward your CV to [email]")
- Portal-specific instructions (e.g. "only applications submitted through [specific portal] will be considered", "do not apply via LinkedIn — use our careers portal")
- Reference numbers required in subject line or application
- Cover letter specifically required (not just "recommended")
- Any instruction that deviates from standard ATS portal apply button

**If found:**
1. Extract the exact instruction text
2. Add to the `Notes` field in `jobs.csv` for this row: `Apply via: [instruction summary]` (semicolon-separated from existing notes)
3. Surface to the user immediately after Block A:

```
📬 Application Instructions
[Exact instruction text from JD]
```

**If no specific instructions found:** proceed silently — do not note this in CSV or output.

---

## Step 0.5 — Domain Access Gating (for URL input)

If the user provides a URL (not pasted JD text):

1. Check if the domain is listed under `## job-match` in `.claude/config/domains.md`
2. If **NOT approved**:
   - Output: `🔒 Domain access request: [domain]`
   - Ask: "Can I fetch the job posting from [domain]? (yes / no)"
   - If yes: Add to whitelist, fetch the page, proceed
   - If no: Ask user to paste the JD instead
3. If **approved**: Fetch silently and proceed

---

## Block A — Role Snapshot

*(Both modes)*

| Field | Value |
|-------|-------|
| Job Title | |
| Company | |
| Archetype | |
| Domain | |
| Seniority | junior / mid / senior / staff / lead / director / VP |
| Location | |
| Work Type | Remote / Hybrid / On-site |
| Employment | Full-time / Contract |
| Salary | listed range or "Not disclosed" |
| Team Size | if mentioned |

**TL;DR:** [One sentence — what this role is and who it's for]

---

## Block B — Profile Match

**Quick mode:** Surface the **top 2–3 hardest gaps** only. Skip the full requirement mapping.

| Gap | Hard blocker? | Mitigation |
|-----|--------------|------------|
| [gap] | Yes/No | reframe / project / course / cover letter angle |

**Full mode:** Map the **top 8–10 most important JD requirements** to resume evidence (skip minor or boilerplate requirements):

| JD Requirement | Match | Evidence |
|----------------|-------|----------|
| [requirement] | ✅ Strong / ⚠️ Partial / ❌ Gap | [specific role/achievement/skill] |

Archetype proof point priorities:
- Builder → delivery speed, shipped products, scale
- Consultant → client outcomes, stakeholder management, deal wins
- Product → metrics improved, roadmap decisions, discovery process
- Operator → efficiency gains, systems built, cross-functional influence
- Manager → team size, hiring, performance management
- Specialist → domain depth, certs, published work

**Full mode only — Gap table:**

| Gap | Hard blocker? | Adjacent experience | Mitigation |
|-----|--------------|---------------------|------------|
| [gap] | Yes/No | [what exists] | reframe / project / course / cover letter angle |

---

## Block C — Level & Positioning

*(Full mode only)*

**Seniority delta:** JD expects [X] | Candidate fits [Y] | Delta: [exact / slightly above / slightly below / significant gap]

**Positioning plan:**
- Founder framing: how to present founder/operator experience as advantage for this archetype
- Consulting framing: how fractional work maps to JD requirements
- Top 3 achievements to lead with (from resume, with suggested framing)
- 3–5 exact JD phrases to mirror in resume summary and cover letter

---

## Block D — Competitive Landscape

*(Full mode only)*

Answer three questions from the JD, company context, and role level. Keep each answer to 2–3 sentences.

**Who is the obvious-fit candidate?**
Describe the background a hiring manager would picture as the default strong applicant — their likely title, industry, years of experience, and key credentials. Be specific; "a senior data analyst with 5+ years in SaaS and a product analytics background" is more useful than "an experienced professional."

**What does this candidate offer that the obvious fit likely doesn't?**
Identify 1–2 genuine differentiators from the resume — cross-functional breadth, founder/operator experience, a domain combination, a specific achievement — that a more conventional applicant probably lacks.

**What does the obvious fit have that this candidate doesn't?**
Name the 1–2 most likely gaps relative to the default applicant — typically direct domain experience, a specific tool, or a credential. This is what the cover letter and positioning plan must bridge.

**Implication for application strategy:**
One sentence: given the above, what must the application lead with, and what must it address?

---

## Block E — Personalisation Plan

*(Full mode only)*

**Top 3 resume changes:**

| # | Section | Current | Proposed change | Why |
|---|---------|---------|-----------------|-----|
| 1–3 | | | | |

**ATS keywords (10):**
- Summary: [keywords]
- Experience: [keywords]
- Skills: [keywords]

---

## Match Score — Callback Likelihood

*(Both modes)*

**What this score predicts:** the likelihood the candidate's resume clears screening and earns a callback for a **cold portal application**, based on **on-paper resume-to-JD match**. It does NOT measure whether the job is a good career fit, a good growth bet, or well-compensated — those are deliberately excluded. It also does not model application source (a referral changes callback odds far more than any of these dimensions) or hard knockout questions (years/work-auth/clearance), which are assumed filtered out before this skill runs.

| Category | Score | Rationale |
|----------|-------|-----------|
| ATS Keyword Coverage | /30 | Do the JD's exact terms (titles, tools, methods, qualifications) appear verbatim on the resume? This is the first gate on a parsed portal application. |
| Required Skills & Tools | /25 | Are the JD's **required** (not preferred) skills/tools present on the resume at the required level? Inventory-gated per Step 0.5b. |
| Experience Level & Credentials | /25 | Is the candidate **at or above** the asked seniority, and do they hold any **required** degree/credential? |
| Title / Domain Adjacency | /10 | Does the candidate's most recent title and domain pattern-match the role, as a recruiter's 6-second scan would read it? |
| Preferred / Nice-to-Have | /10 | Pooled coverage of everything the JD marks as **preferred / nice-to-have / a plus** — skills, credentials, experience, or anything else clearly optional (not required). Tiebreaker weight only. |

**Total: [X] / 100**

**Dimension caps (applied to the individual dimension, never the total):**

- **Required Skills & Tools — tool gap cap.** If **one or more** required tools have no resume evidence **and** no closely-equivalent tool the candidate does have (e.g. Power BI ↔ Tableau, Postgres ↔ MySQL, Airflow ↔ Prefect count as substitutes; a genuinely absent dbt/Snowflake/Spark does not), cap this dimension at **10/25**. A required tool that is satisfied by a defensible substitute does NOT trigger the cap. Tools listed as preferred, nice-to-have, or "familiarity with" never trigger the cap (they belong in the Preferred dimension).
- **Experience Level & Credentials — credential cap.** If a **required** degree or credential is absent with no stated equivalent ("or equivalent experience" means no cap), cap this dimension at **10/25**. Being **below the asked seniority level is a graded soft penalty within this dimension — it does NOT cap.** Recruiters flex on level far more than on hard credentials. Being at or above the asked level earns full level points (see overqualified flag below).

**Preferred dimension scoring:** pool all clearly-optional JD items (preferred/nice-to-have/"a plus") regardless of type and score the /10 on overall coverage. Do not split by type. This bucket can never rescue a low Required Skills score — that is its purpose.

**Bands (callback likelihood):**
- 85–100 → 🟢 Very likely to hear back. Strong on-paper match across screening gates.
- 70–84 → 🟡 Good odds. One or two soft gaps to address in the resume/cover letter.
- 55–69 → 🟠 Long shot. A real screen-out risk exists (capped dimension or thin keyword coverage).
- <55 → 🔴 Unlikely to clear screening.

**Overqualified / downgrade flag:** If the candidate scores high on callback likelihood **because** the role is below their level or pay (clearly junior to their experience, or posted comp well below market for their level), append `⬇️ Likely callback, but below your level/pay` to the recommendation. The score stays high — this flag does not reduce it. It exists so high-callback downgrades can be filtered without distorting the screening signal.

**Recommendation:** [One honest sentence — likely to hear back or not, the key driver (which gate is strong or at risk), and the downgrade flag if applicable.]

---

## Step Final — Save Report

**Quick mode (MANDATORY):** Save the quick report (Blocks A + B condensed + Match Score) to:

```
job-outputs/reports/match_report_[Company]_[Role]_[YYYY-MM-DD].md
```

Use lowercase-hyphens for `[Company]` and `[Role]` (e.g. `match_report_telus_data-strategist_2026-05-06.md`). Resolve the project root via the `get_project_root()` helper. Save before showing follow-up commands. **Also update `jobs.csv`** — write `Match_Score` and `Match_Label` to the existing row (matched by Company + Role). If no row exists yet, append one with status `pending`. Do not overwrite any other fields that are already populated.

**Full mode (MANDATORY):** After producing all evaluation blocks (A–E), save the **complete full report** (every section, content block, and table — not a summary) as a `.docx` file to:

```
job-outputs/reports/match_report_[Company]_[Role]_[YYYY-MM-DD].docx
```

Use the `docx` skill to generate the file. Apply standard document formatting: title heading, section headings for each block, tables rendered as Word tables. Set docx metadata (author, last_modified_by) from the candidate name per the CLAUDE.md File Generation rules. Save before showing follow-up commands.

Also append (or update) the row in `job-outputs/jobs.csv` per the rules in CLAUDE.md `## Application Tracking`.

---

## Session Handoff (Quick → Full)

When full mode is triggered **after quick mode already ran in the same session** for the same role:

1. **Run all blocks fresh** — A, B (full requirement mapping + gap table), C, D, E, and Match Score
2. **Do not reuse or append** the quick mode output — the full report is a standalone document with more depth in every shared section
3. Save per the Step Final rules

The quick report (`.md`) remains on disk as a separate artifact. The full report (`.docx`) is built independently from the same JD and resume — not layered on top of the quick output.

If the JD or context has changed since the quick match, note the discrepancy before proceeding.

---

## Rules

- The Match Score answers **"will they call me back"**, not "is this a good job for me." Never let career-fit, growth, or comp reasoning leak into the score — those dimensions were deliberately removed. If a role is a great career move but a weak on-paper match, it scores low, and that is correct.
- Score the resume **as a screener would read it**: exact keyword presence, required must-haves met, level/credentials cleared, title pattern-match. Do not award points for potential, transferable promise, or "could learn it."
- A capped dimension is a screen-out signal — surface it plainly in the recommendation rather than smoothing it over with strong scores elsewhere.
- Below-level is a soft penalty, not a cap. Missing required tools (no substitute) and missing required credentials (no equivalent) ARE caps. Keep this distinction exact.
- Never fabricate salary data — say "no reliable data found" if unavailable
- Never inflate scores — honest gaps are more useful than inflated confidence
- Every recommendation must reference actual resume lines or JD language
- Respect domain whitelist — only search approved domains for comp research
- Quick mode is intentionally lean — resist adding extra blocks unless the mode is full
