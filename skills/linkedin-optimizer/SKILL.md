---
name: linkedin-optimizer
description: "Rewrites and optimises the candidate's LinkedIn profile sections to attract inbound recruiter messages for a target role. Produces rewritten headline, About section, and experience bullet points tailored to a target role or inferred from the master resume. Trigger on: '/linkedin-optimizer', 'optimise my LinkedIn', 'rewrite my LinkedIn profile', 'help me attract recruiters', 'fix my LinkedIn headline', or any request to improve LinkedIn presence for job searching."
---

# LinkedIn Profile Optimizer

## Overview

This skill rewrites the candidate's LinkedIn profile sections to pull inbound
recruiter messages rather than requiring the candidate to chase jobs manually.
It uses the master resume and LinkedIn profile already uploaded in this project.
Never ask for the resume. Output is clean, copy-ready text for each section.

---

## Step 1 — Input Detection

### What's needed:
- **Target role** — the type of role the candidate is targeting (e.g. "Product Manager at a fintech startup", "Senior AI Engineer", "Director of Marketing")
- **Current LinkedIn content** — ideally the candidate pastes their current headline and About section so the optimizer can see what exists and how far it needs to move

### Input handling:
- **Target role + current content provided** → proceed immediately
- **Target role only, no current content** → proceed using the master resume to infer current positioning; note that rewritten sections will be based on the resume, not their existing LinkedIn copy
- **No target role specified** → infer the most likely target from the most recent role in the master resume. Announce: "I'll optimise for [inferred role] — let me know if you're targeting something different."
- **"/linkedin-optimizer" with nothing** → ask one question only: "What type of role are you targeting? (e.g. 'Senior Product Manager at a tech company')"

---

## Step 2 — Profile Audit

Silently analyse before writing anything:

**From the master resume:**
- Most recent title and seniority level
- Top 3–5 career achievements with numbers where available
- Primary skills and tools the candidate actually has
- Industries and domains they've worked in
- Unique angles: founder experience, consulting background, cross-functional breadth, niche expertise

**From current LinkedIn content (if provided):**
- Current headline — is it a job title or does it communicate value?
- About section — does it lead with value or with biography?
- Does it use keywords a recruiter searching for [TARGET ROLE] would use?
- Is there a clear call to action at the end of the About section?

**Target role research:**
Identify the top 10 keywords and phrases recruiters use when searching for [TARGET ROLE] on LinkedIn. These are the terms that must appear in the headline and About section to surface in recruiter searches.

---

## Step 3 — Rewrite the Profile Sections

### Section 1 — Headline (220 characters max)

**Rules:**
- Do NOT just use the job title — that's what everyone does
- Lead with the value delivered, not the job title held
- Include the target role keyword so LinkedIn's algorithm surfaces you in recruiter searches
- Format: [Value/Outcome] | [Role keyword] | [Differentiator or industry]
- Include 2–3 searchable keywords naturally — recruiters search these exact phrases

**Bad headline example (do not produce this):**
"Product Manager at TechCorp | Agile | Scrum"

**Good headline approach:**
"Building AI-powered products that ship on time | Product Manager | B2B SaaS & Fintech"

Produce 2 headline options — let the candidate choose:
```
Option A: [headline]  — [one sentence on the strategic angle it takes]
Option B: [headline]  — [one sentence on the alternative angle]
```

---

### Section 2 — About Section (2,600 characters max — aim for 1,800–2,200)

**Structure — 4 paragraphs:**

**Para 1 — The Hook (2–3 sentences)**
- Open with a problem you solve or a value you deliver — not "I am a Product Manager with 8 years of experience"
- Make it immediately clear who you are for and what you do for them
- Include 1–2 target role keywords naturally

**Para 2 — Your Proof (3–4 sentences)**
- 2–3 concrete achievements from the master resume with numbers
- Frame each achievement in terms of business outcome, not job duty
- Use language that mirrors what recruiters for [TARGET ROLE] want to see

**Para 3 — Your Unique Angle (2–3 sentences)**
- What makes this candidate different from the 500 other people with the same title?
- Founder experience, cross-industry breadth, niche domain expertise, technical + business hybrid, etc.
- Pull from the master resume — don't invent

**Para 4 — Call to Action (1–2 sentences)**
- What you're open to / looking for
- Soft invitation to connect or reach out
- Example: "If you're building [X type of product] and need someone who [Y], let's talk."

**About section rules:**
- Write in first person — LinkedIn is a human platform, not a resume
- Short paragraphs — max 4 lines each — LinkedIn collapses long blocks
- End with keywords — LinkedIn's algorithm reads the full section; the last paragraph is a good place for a natural keyword cluster
- No buzzwords: "passionate", "dynamic", "results-driven", "synergy" — all banned

---

### Section 3 — Experience Bullets (top 2 roles only)

For the 2 most recent roles in the master resume, rewrite 3–4 bullets each.

**Rules:**
- Lead with an action verb that signals seniority: Led, Architected, Launched, Drove, Grew, Reduced, Built
- Each bullet: [Action verb] + [What] + [How] + [Result/Impact with number]
- Mirror language from [TARGET ROLE] job descriptions — recruiters scan for these exact terms
- Quantify every bullet where the resume has numbers — if no number exists, add a scale indicator ("across 3 markets", "for a team of 12", "within 6 months")
- Never use: "Responsible for", "Helped with", "Assisted in", "Was involved in"

**Format each role as:**
```
[Company] · [Title] · [Dates]
• [bullet 1]
• [bullet 2]
• [bullet 3]
• [bullet 4 — optional]
```

---

### Section 4 — Skills Section (top 15 skills to pin)

LinkedIn allows pinning skills that appear first on the profile.
List the 15 most recruiter-searchable skills for [TARGET ROLE] that the
candidate actually has (based on the master resume).

Order them: most searched / most relevant to target role first.

```
Top 15 skills to pin (in order):
1. [skill]
2. [skill]
...
```

---

## Step 4 — Output Format

Output in this order with clear section headers:

```
─────────────────────────────────────────
🔗 LinkedIn Profile Optimization
Target Role: [role] | Based on: master resume + [current content if provided]
─────────────────────────────────────────

## HEADLINE
Option A: [headline text]
→ [one-line strategic note]

Option B: [headline text]
→ [one-line strategic note]

─────────────────────────────────────────

## ABOUT SECTION
[Full rewritten About section — copy-ready]

Character count: ~[N] / 2,600

─────────────────────────────────────────

## EXPERIENCE BULLETS

### [Most Recent Role Title] · [Company] · [Dates]
• [bullet]
• [bullet]
• [bullet]
• [bullet]

### [Second Role Title] · [Company] · [Dates]
• [bullet]
• [bullet]
• [bullet]

─────────────────────────────────────────

## SKILLS TO PIN (top 15 — in order)
1. [skill]  2. [skill]  3. [skill]  4. [skill]  5. [skill]
6. [skill]  7. [skill]  8. [skill]  9. [skill]  10. [skill]
11. [skill]  12. [skill]  13. [skill]  14. [skill]  15. [skill]

─────────────────────────────────────────

## KEYWORD COVERAGE
Keywords injected for recruiter search visibility:
[comma-separated list of the target role keywords woven into the above sections]

─────────────────────────────────────────
```

---

## Step 5 — After Output

End with:

```
─────────────────────────────────────────
💡 Implementation tips:
• Update your headline first — it appears in every search result and notification
• Paste the About section exactly — do not reformat, LinkedIn strips markdown
• Pin skills manually: Profile → Skills → Edit → Pin the top 15 above
• Ask 3 colleagues to endorse your top 5 skills in the first week — signals legitimacy to the algorithm

Ready to apply? Run /job-scout to find roles that match your newly optimised profile.
─────────────────────────────────────────
```

---

## Output Rules

- **All content must come from the master resume** — never invent experience or achievements
- **Never ask for the resume** — it is in the project
- **Write in first person** — LinkedIn is a human platform
- **Every bullet must have a result** — use scale indicators if no specific metric exists
- **No buzzwords** — "passionate", "results-driven", "dynamic", "synergy", "leverage" are all banned
- **Output is copy-ready** — the candidate should be able to paste directly without editing
- **Headline options must be meaningfully different** — not just word swaps; each should reflect a different positioning strategy
