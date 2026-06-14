---
name: cover-letter-generator
description: "Generates a tailored, ATS-optimised cover letter matched to a specific job description. Trigger on: 'write a cover letter', 'generate a cover letter', 'cover letter for this job'."
---

## Step 1 — Input & Format Detection

- JD present → proceed immediately
- Job title + company only → ask: "Can you paste the full job description?"
- Table row → extract Title, Company, Location, Description

Output format: `.pdf` if user says "pdf", `.docx` otherwise (default).

## Step 2 — Analyse Silently

**Company signals:** name, industry, size, JD tone (formal/casual/values-driven), cultural keywords

**Role signals:** exact title, seniority, top 3 responsibilities (by emphasis + repetition)

**Primary problem:** Identify the single most important problem this hire is meant to solve. Look for the role's core purpose — not a list of duties, but the underlying business need. State it in one sentence before writing anything.

**ATS keywords:** check `job-outputs/reports/` for `match_report_[Company]_[Role]_*.md` first — if found, use Block E keyword list. Only extract from JD if no report exists. **Use case-insensitive globbing** (e.g. `glob.glob(pattern, case_sensitive=False)` or pre-lowercase both sides); historic match reports (pre-2026-04-29) use mixed case for company names.

**Candidate match:** from master resume — identify the ONE strongest experience story that maps directly to the primary problem. It must be specific: a real situation, a real action, a real outcome with numbers if they exist. Do not output this analysis.

## Step 3 — Write the Letter

**Read `skills/_shared/writing-style.md` before writing any content.** All tone, voice, banned language, and the interview backtrack test are defined there. Do not redefine them here.

**Structure — 3 paragraphs, max 250 words total:**

*Opening (2–3 sentences):*
- Name the primary problem this role is hired to solve, then connect the candidate's background to it directly
- Never: "I am writing to...", "I am excited to...", "Please find attached...", "With X years of experience..."
- Do: problem → candidate's direct relevance. Start in the middle of the story.
- Include 1–2 ATS keywords naturally

*Middle (proof — the one best story):*
- Tell ONE specific story from the candidate's experience that demonstrates they have solved this problem before
- Concrete situation + action + outcome. Numbers where they exist.
- 3–5 sentences. No bullet points. No second story diluting the first.
- Include 2–3 ATS keywords woven into the narrative

*Closing (2–3 sentences max):*
- What the candidate would focus on in the first 60–90 days, specific to this role
- One-line call to action — interest in a conversation, not eagerness
- No "I look forward to hearing from you" as a standalone closer

**Document structure:**
```
[Candidate Full Name]
[City, Province] | [Email] | [Phone] | [LinkedIn]

[Date — e.g. April 8, 2026]

[Hiring Manager if known]
[Company Name]

Re: [Exact Job Title] — [Company Name]

Dear [Hiring Manager / Hiring Team],

[Opening]

[Middle]

[Closing]

Sincerely,

[Candidate Full Name]
```

Pull all contact details from master resume. Use "Hiring Team" if no name — never "To Whom It May Concern."

## Step 3.5 — Reviewer Agent

Read `skills/_shared/reviewer-agent.md`. Spawn a `general-purpose` sub-agent using
the Cover Letter Reviewer Prompt. Pass the full JD text and the full draft letter
inline — do not reference files on disk for these.

Once the reviewer returns its numbered suggestions, apply each one using judgment:
- Missed keywords: weave into the middle paragraph where evidence exists
- Stretch framing: apply the safer reframe or remove the claim
- Tone and voice: fix per writing-style.md rules
- Opening strength: rewrite the opening if the reviewer flags it as weak

The revised draft is what gets used in Step 4. Never generate the file before
the reviewer pass is complete.

## Path Resolution

Resolve the project root at runtime in every script that writes a file:

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../lib'))
from project_paths import get_project_root

PROJECT_ROOT  = get_project_root()
COVER_LETTERS = os.path.join(PROJECT_ROOT, "job-outputs", "cover-letters")
os.makedirs(COVER_LETTERS, exist_ok=True)
```

Use `COVER_LETTERS` for all `doc.save()` and `soffice` `--outdir` calls. Never substitute a literal session path.

---

## Step 4 — Generate File

Serialize the letter content to `/tmp/cover_content.py`:

```python
content = {
    "re_line": "[Exact Job Title] — [Company Name]",
    "hiring_manager": "[Name or 'Hiring Team']",
    "opening": "[Opening paragraph text]",
    "middle": "[Middle paragraph text]",
    "closing": "[Closing paragraph text]",
    # contact_line is read from master-resume.md automatically if omitted
}
```

Then run:
```bash
python3 skills/cover-letter-generator/generate_cover_letter.py \
  --company "[normalised-company]" \
  --role "[normalised-role]" \
  --content-file /tmp/cover_content.py \
  --output-dir job-outputs/cover-letters/
```

The script handles: formatting (Arial, NAVY/BLACK, 1-inch margins), metadata, and PDF conversion. Prints `SAVED:/path` for each file. Present both `.docx` and `.pdf` links.

Formatting constraints still apply: max 1 page, 11pt minimum, 250-word body cap. If the letter content exceeds limits, tighten paragraphs before serializing.

## Step 5 — Post-output Summary

```
✅ Cover Letter — [Job Title] at [Company]
🎨 Tone: [Formal / Professional / Conversational]
🧩 Primary problem addressed: [one sentence]
💡 ATS keywords used: [comma-separated list]
📏 Word count: [N] words

Want adjustments? "sharpen the opening" / "tighten the story" / "different example" / "generate matching resume"
```

## Rules

- Never output letter as plain text in chat — file is the deliverable
- Never use filler openers; never use "To Whom It May Concern"
- Filename: `cover_letter_[Company]_[Role]_[YYYY-MM-DD].docx`
- No tables, skills sections, or elements not in the structure above
- Hard cap: 250 words body text (excludes header, salutation, sign-off). If over, cut — never shrink font.
