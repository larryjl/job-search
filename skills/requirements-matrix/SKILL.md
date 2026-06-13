---
name: requirements-matrix
description: >
  Generates a formatted requirement response matrix (.docx) that responds to each mandatory and scored requirement in a government or enterprise RFP/RFQ, using evidence from the candidate's master resume. Use this skill whenever the user shares a job posting or RFP with numbered mandatory or scored requirements (e.g. M1, M2, S1, S2), or asks to "build a matrix", "respond to the requirements", "create a requirement response", or "write up my responses to the criteria". Also trigger when the user says things like "help me address the requirements" or "put together my requirement responses" — even if they don't use the word "matrix". This skill is especially important for government contract bids, RFQ submissions, and procurement responses where requirements are scored individually.
---

# Requirements Matrix Skill

Generates a professionally formatted requirement response matrix that maps the candidate's experience directly to each mandatory and scored requirement in a government or enterprise RFP/RFQ.

---

## What This Skill Produces

A `.docx` document structured as:
- **Title block**: role title, organisation, document type, candidate name, date
- **Mandatory Requirements** section: one response per requirement, labeled M1, M2, etc.
- **Scored Requirements** section: one response per requirement, labeled S1, S2, etc.

Each response: a one-line verdict ("Met." or "Partially met." or "Not met — see note."), followed by point-form evidence drawn directly from the master resume.

Output saved to: `job-outputs/matrices/matrix_[Organisation]_[Role]_[YYYY-MM-DD].docx`

---

## Step 1 — Read Inputs

Read:
- `profile/master-resume.md` — the candidate's primary source of evidence
- The job posting / RFQ (pasted text, uploaded file, or URL)

Extract from the job posting:
- Organisation name and role title
- Every mandatory requirement (M1, M2, ...) with exact wording and stated minimum (e.g. "7+ years")
- Every scored requirement (S1, S2, ...) with exact wording and stated minimum

If requirements are not explicitly numbered, number them yourself (M1, M2..., S1, S2...) in the order they appear.

---

## Step 2 — Analyse Each Requirement

For each requirement, before writing anything:

1. **Identify the core ask** — what is the evaluator actually checking for? Strip away bureaucratic language and get to the substance.
2. **Find matching evidence** in the master resume — specific roles, dates, outcomes, and context.
3. **Count years** honestly — only count periods where the candidate was actively doing the work. Do not count career gaps, parental leave, or full-time study as experience unless it was directly relevant professional development.
4. **Identify any shortfalls** — if the stated minimum isn't cleanly met, note it and plan how to frame it honestly without obscuring it.

Government evaluators score these systematically. Honesty paired with a strong bridge is more effective than overclaiming — evaluators are experienced at spotting inflated claims.

---

## Step 3 — Draft Each Response

### Response format

**For each requirement:**

```
[Requirement label and exact wording from RFQ — bold]

Met. [or: Partially met. / Not met — see note.]  [one sentence summary of the match]

• [Role, Organisation (dates)]: [specific evidence — what was done, outcome if quantifiable]
• [Role, Organisation (dates)]: [specific evidence]
• ...
```

**Ordering within each requirement:**
- Roles ordered most recent to oldest
- Within a role, sub-points ordered most relevant to least relevant for that specific requirement

**Writing discipline:**
- Point form only — no paragraphs inside requirement responses
- Each bullet: role + organisation + dates first, then the evidence. This makes it scannable for evaluators.
- Be specific: name tools, scale, outcomes, regulatory frameworks (e.g. Health Information Act), team size where relevant
- No em dashes — use semicolons or colons instead
- No AI-signal words (see banned words in `skills/_shared/formatting.md`)
- Do not pad thin responses with generic claims — a short honest response is stronger than a long vague one

### Handling the 10-year / years-of-experience requirements

When a requirement states a years minimum that the candidate doesn't cleanly meet:
- Open with a timeline framing: "Career in [domain] spanning [start]–[end], including [N] years of [specific work]."
- Separate early foundational experience from core delivery experience if the distinction is real and honest
- Note any relevant professional development periods that fill calendar gaps — frame as IM/IT professional development, not a gap
- Do not claim more years than are defensible — evaluators verify

---

## Step 4 — Preview Before Saving

Before generating any file, show a complete plain-text preview of the full matrix in a code block. After the preview, ask:

> "Does this look good? Type **yes** to save, or tell me what to change."

Do not generate any file until the user confirms. If changes are requested, revise and show the updated preview again. Repeat until confirmed.

---

## Step 5 — Generate the Document

Serialize the matrix content to `/tmp/matrix_content.py`:

```python
content = {
    "organisation": "[Display name, e.g. Government of Alberta]",
    "role": "[Display name, e.g. Senior Data Architect]",
    "mandatory": [
        {
            "label": "M1",
            "wording": "[Exact requirement wording from RFQ]",
            "verdict": "Met.",           # or "Partially met." or "Not met — see note."
            "summary": "[One-sentence summary of the match]",
            "bullets": [
                "[Role, Org (dates): specific evidence]",
            ],
        },
    ],
    "scored": [
        {
            "label": "S1",
            "wording": "[Exact requirement wording]",
            "verdict": "Met.",
            "summary": "[One-sentence summary]",
            "bullets": ["[evidence]"],
        },
    ],
}
```

Then run:
```bash
python3 skills/requirements-matrix/generate_matrix.py \
  --organisation "[normalised-org-slug]" \
  --role "[normalised-role-slug]" \
  --content-file /tmp/matrix_content.py \
  --output-dir job-outputs/matrices/
```

The script handles: title block, horizontal rules, section headings, requirement blocks with verdict + bullets, metadata, and formatting. Prints `SAVED:/path` on success. Validate the file opens cleanly before presenting.

---

## Step 6 — Post-Save

After saving:
1. Present link to the file
2. Log to `job-outputs/jobs.csv` if not already logged for this company + role

---

## Iterating After Review

If the user asks to:
- **Reorder items** — most recent to oldest is the default; edit the build script and regenerate
- **Add missing content** — cross-check matrix against master resume; add any evidence present in one but absent from the other
- **Trim redundancy** — identify bullets that make the same point twice across different requirements or within the same requirement; merge or remove
- **Change wording** — edit the build script content strings and regenerate

When regenerating, always re-validate the .docx after each run before delivering.

---

## Quality Checks

Before presenting the final files, verify:

- [ ] Every requirement from the RFQ has a response — none skipped
- [ ] Years claimed are honest and match actual resume dates
- [ ] Bullets are ordered most recent → oldest within each requirement
- [ ] No em dashes anywhere
- [ ] No banned AI-signal words (leveraged, streamlined, robust, spearheaded, etc.)
- [ ] Each bullet names the role, organisation, and dates — not just the evidence
- [ ] Shortfalls are acknowledged honestly, not papered over
- [ ] .docx opens and renders cleanly

---

## Example Response (S2 — Data Platform Design)

```
S2 — Demonstrated experience designing, building, and operating modern data
platforms that support enterprise reporting and analytics, including data warehouses
or lakehouses using layered architectures (e.g., curated ingestion, dimensional
models). (7+ years)

Met. 7+ years designing and operating enterprise data platforms using dimensional
modelling and layered ingestion architectures.

• [Most Recent Employer], [Role Title] ([Years]): [1–2 sentence summary of
  relevant data platform work; concrete scope and outcome].

• [Prior Employer], [Role Title] ([Years]): [1–2 sentence summary of
  relevant data platform work; concrete scope and outcome].

• [Earlier Employer], [Role Title] ([Year]): [1–2 sentence summary of
  relevant data platform work; concrete scope and outcome].

• [Earliest Employer], [Role Title] ([Years]): [1–2 sentence summary of
  relevant data platform work; concrete scope and outcome].
```

*(Replace bracketed placeholders with actual evidence drawn from `profile/master-resume.md`, ordered most recent → oldest.)*
