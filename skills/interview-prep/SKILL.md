---
name: interview-prep
description: "Generates a complete, role-specific interview preparation kit. Produces: top 10 interview questions by type, a full STAR+R story bank (6-8 stories with coaching tips), a recommended case study, red-flag Q&A, and 5 smart questions to ask the interviewer. Loads existing match report context if available. Trigger on: 'prep me for this interview', 'interview questions for this role', 'help me prepare', '/interview-prep', or when a JD is shared with intent to prepare for an interview."
---

# Interview Prep Skill

## Overview

This skill generates a complete, role-specific interview preparation kit using the
master resume and LinkedIn profile already uploaded in this project. It never asks
for the resume. It reads the JD, maps it to the candidate's actual experience, and
produces practise-ready outputs — not generic advice.

---

## Step 1 — Input Detection

Check what has been provided:
- **Full JD pasted** → proceed immediately
- **Job title + company only** → ask: "Can you paste the job description? Even a
  partial one helps me target the questions accurately."
- **Table row from /linkedin-jobs** → extract Job Title, Company, Description from
  that row and treat as the JD input
- **"/interview-prep" with no job** → ask: "Which role are you prepping for? Paste the JD
  and I'll build your full prep kit."

### Match Report Loading

Before deriving anything from the resume, check `job-outputs/reports/` for an existing
match report for this company + role:

```
job-outputs/reports/match_report_[company]_[role]_[date].md
```

**Globbing:** use case-insensitive matching when searching — historic match reports (pre-2026-04-29) use mixed-case company names. In Python: lowercase both the search target and the candidate filenames before comparing, or use `pathlib.Path.glob` combined with `re.IGNORECASE` filtering.

- **If found** → use the Read tool to load the full markdown into context. The report has these named sections you can extract by header:
  - `## Block A` (or `## Snapshot`) — role summary
  - `## Block B` (or `## Profile Match`) — strengths, gaps, requirements coverage
  - `## Block C` (or `## Positioning`) — recommended framing and language
  - `## Block D` (or `## Competitive Landscape`) — who else is applying, differentiation strategy
  - `## Block E` (or `## ATS Keywords` / `## Personalisation`) — keyword list
  - `## Block F` (or `## Compensation`) — salary anchors

  Find each `## Block X` heading and read until the next `## ` heading. Use Block B's gap analysis to sharpen red-flag questions, Block C's positioning language in STAR story framing, and Block B's requirements mapping to select which achievements to surface. If a section header isn't found (older reports vary), pass the full report through and extract what you can.

  Do not re-derive what the match report already contains — build on top of it.
- **If not found** → derive everything fresh from the master resume. Tell the user: "No match report found — running interview-prep from resume only. Run `/job-match` first for a richer prep kit."

---

## Step 2 — Analyse the Role

Silently extract before generating any output:

**Role signals:**
- Seniority level (junior / mid / senior / lead / director)
- Primary function: builder / consultant / manager / individual contributor
- Top 5 responsibilities by emphasis in the JD
- Hard skills required (tools, platforms, languages, certifications)
- Soft skills emphasised (leadership, communication, cross-functional, etc.)
- Industry / domain context

**Archetype classification** — classify the role into one of these (or hybrid of two):

| Archetype | Signals |
|-----------|---------|
| **Builder** | "build", "ship", "engineer", "develop", "hands-on", "0 to 1" |
| **Consultant / Advisor** | "client-facing", "stakeholder", "advise", "solutions", "pre-sales" |
| **Product** | "discovery", "roadmap", "prioritisation", "metrics", "user research" |
| **Operator / Ops** | "process", "scale", "efficiency", "systems", "cross-functional" |
| **Manager / Lead** | "team", "reports", "hiring", "performance", "strategic direction" |
| **Specialist / Expert** | deep domain: legal, finance, data, security, design, compliance |

Store the archetype — it determines which question types to emphasise and how to
frame STAR stories.

**Candidate match:**
From the master resume in this project, identify:
- Most relevant role(s) for this position
- 3–5 concrete achievements that map to the top JD responsibilities
- Any tools, certifications, or domain experience that directly matches
- Visible gaps (be honest — they will come up in the interview)

---

## Step 3 — Generate the Prep Kit

Output in this exact order with these exact headers.

---

### 🎯 Interview Prep — [Job Title] at [Company]
**Archetype:** [detected] | **Seniority:** [detected] | **Focus:** [top theme from JD]

---

### Part 1 — Top 10 Interview Questions

Generate 10 questions the interviewer is most likely to ask, based on the JD.
Label every question with its type. Prioritise question types based on archetype:

- **Builder** → weight toward Technical + Situational
- **Consultant** → weight toward Behavioural + Situational
- **Product** → weight toward Behavioural + Case
- **Operator** → weight toward Situational + Behavioural
- **Manager** → weight toward Leadership + Behavioural
- **Specialist** → weight toward Technical + Behavioural

**Question type labels:**
- `[Behavioural]` — "Tell me about a time when..."
- `[Technical]` — role-specific knowledge or skill test
- `[Situational]` — "What would you do if..."
- `[Leadership]` — managing people, conflict, direction
- `[Culture Fit]` — values, ways of working, motivation
- `[Case]` — problem-solving, trade-off analysis

Format:

```
1. [Type] Question text here?
2. [Type] Question text here?
...
```

Do not add answer guidance here — answers come in Part 2.

---

### Part 2 — STAR+R Story Bank

Generate 6–8 STAR+R stories mapped to the JD's key requirements.
Pull all stories from actual experience in the master resume — no fabrication.
If a match report is loaded, use Block B's requirements mapping to select which
achievements to surface and which gaps to acknowledge.

**Why STAR+R matters:** Junior candidates describe what happened.
Senior candidates extract lessons. The Reflection is your seniority signal — never skip it.

**STAR+R format:**
- **S — Situation:** Context, stakes, environment — what was going on?
- **T — Task:** What were you specifically responsible for?
- **A — Action:** What did YOU do? (Not the team — use "I", not "we")
- **R — Result:** Quantified outcome where it exists in the resume. Use placeholders
  like `[X%]` or `[N users]` if the number exists in the resume but needs confirming.
- **Reflection:** What did this teach you? What would you do differently?

**Archetype story emphasis:**
- **Builder** → speed of delivery, technical decisions, shipping under constraints
- **Consultant** → client outcomes, difficult stakeholders, scoping under ambiguity
- **Product** → discovery insights, prioritisation trade-offs, metrics moved
- **Operator** → systems built, efficiency created, cross-functional influence
- **Manager** → hiring decisions, performance conversations, team culture
- **Specialist** → depth of expertise demonstrated, novel problem solved

Format each story as:

```
─────────────────────────────────────────
JD Requirement: [requirement this story addresses]

S: [2 sentences — context and stakes]
T: [1 sentence — your specific ownership]
A: [3–4 sentences — concrete actions, decisions, trade-offs you made]
R: [1–2 sentences — outcome with numbers if available]
★ Reflection: [What you learned or would do differently — 1–2 sentences]

💡 Tip: [One coaching note specific to this story and this role]
─────────────────────────────────────────
```

---

### Part 3 — Recommended Case Study

Which of the candidate's projects or roles to prepare as a full case study for this
role, and how to structure it:

**Project:** [name from resume]
**Why this one:** [why it maps best to this role]
**How to structure it:** [3–4 sentences — what to lead with, which metrics to
emphasise, how to tie it to the JD's core problem]

---

### Part 4 — Red-Flag Questions & How to Answer Them

Questions the interviewer may ask that could be uncomfortable, based on the JD,
the candidate's background, and any gaps identified in Block B of the match report
(or freshly derived from the resume if no match report exists).

| Question | Why It's Asked | How to Answer It |
|----------|---------------|-----------------|
| "Why did you leave / sell your company?" | Assessing risk, commitment, ambiguity tolerance | [Specific framing using candidate's actual situation] |
| "You've been independent for X years — can you work within a structure?" | Culture fit, coachability | [How to reframe operator independence as an asset] |
| "You don't have [specific gap] — how would you handle that?" | Testing self-awareness and learning agility | [Specific bridge using adjacent experience] |
| [Other role-specific red flags based on the JD and resume gaps] | | |

---

### Part 5 — Questions to Ask Them

5 smart questions the candidate should ask the interviewer. Rules:
- Specific to this JD and company — not generic
- Each signals a different dimension: strategic thinking, team dynamics,
  growth path, success metrics, company challenges
- None should be answerable by reading the job posting
- Avoid questions about salary/benefits at first interview unless it's a recruiter screen

Format:

```
1. [Question] — 💡 Why ask this: [one sentence on what it signals about you]
2. ...
```

---

### ⚡ Quick Prep Checklist


Output this block at the end:

```
Before the interview:
□ Research [Company Name] — recent news, funding, product launches
□ Review your STAR stories above out loud (not just in your head)
□ Prepare your "tell me about yourself" — 90 seconds, 3 acts: past / present / future
□ Know your numbers — be ready to quantify any achievement they probe on
□ Prepare for: "Why [Company]?" and "Why this role?" — make it specific

On the day:
□ Have the JD open for reference
□ Have your resume open — interviewers often read from it line by line
□ Take 3 seconds before answering behavioural questions — it signals confidence

After:
□ Send a follow-up note within 24 hours — one specific thing from the conversation
□ Run /mock if you want to practise live before the real interview
```

---

## Output Rules

- Never output generic interview advice — every question and story must be
  specific to this JD and this candidate's actual resume
- Never fabricate achievements — only use experience from the master resume
- Never ask for the resume — it is in the project
- If a match report exists for the role, always load and use it — do not ignore it
- The STAR+R stories are frameworks, not scripts — tell the candidate to
  personalise the wording in their own voice
- Red-flag questions must be specific to this candidate's actual background and the
  JD's real gaps — do not use generic placeholders
- Do not preview content in chat before saving — generate and save immediately
- Confirm completion with the file path and a one-line summary

## File Generation

Serialize the interview prep content to `/tmp/interview_content.py`:

```python
content = {
    "company": "[Display company name]",
    "role": "[Display role name]",
    "questions": [
        {
            "number": 1,
            "type": "Behavioural",        # or Technical / Situational / Role-specific
            "question": "[Question text]",
            "approach": "[How to approach this question]",
            "story": {
                "situation": "...",
                "task": "...",
                "action": "...",
                "result": "...",
                "reflection": "...",
            },
            "tip": "[Coaching tip]",
        },
    ],
    "red_flag_questions": [
        {
            "question": "[Red-flag question]",
            "why_asked": "[Reason interviewer asks this]",
            "how_to_answer": "[How to reframe or address it]",
        },
    ],
    "company_research": [
        "[Key fact about company]",
    ],
    "questions_to_ask": [
        "[Question to ask interviewer]",
    ],
}
```

Then run:
```bash
python3 skills/interview-prep/generate_interview_notes.py \
  --company "[normalised-company]" \
  --role "[normalised-role]" \
  --content-file /tmp/interview_content.py \
  --output-dir job-outputs/interview-notes/
```

The script produces a structured `.docx` with: question table (Part 1), STAR story bank (Part 2), company research (Part 3), red-flag questions table (Part 4), and questions to ask (Part 5). All formatting, metadata, and headings are handled by the script. Prints `SAVED:/path` on success.

---

## Interview Story Persistence

After generating the STAR+R story bank, save new stories to `.claude/memory/interview-stories.md`. Ask first: "Use saved stories / generate fresh / mix?"

**Story structure:**

```
## [Story Name] — [STAR Category]
**Best for:** [role/context where this lands hardest]
**Story:** [2–3 sentences, STAR format]
**Why it works:** [what resonates; what feedback validated it]
**Last refined:** [YYYY-MM-DD]
**Status:** active | archived
```

**STAR categories:** Leadership, Technical, Conflict, Growth, Execution, Scope Management, Stakeholder Alignment, Data/Analytics.

**Lifecycle:**
- Generation: seed from resume highlights; mark `active`
- Post-mock: update `Why it works`, refine wording, increment `Last refined`; mark `archived` if story no longer resonates
- Reuse: stories marked `active` are seeded into subsequent prep sessions automatically

---

## After Output

End with:

```
---
Ready to practise live? Run /mock-interview and I'll be your interviewer for [Job Title] at [Company].
Want the cover letter too? Run /cover with the same JD.
```
