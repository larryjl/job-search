# Skill: application-questions

Answer job application form questions concisely, using light company research and the candidate's resume.

---

## Trigger

User pastes one or more application questions, either standalone or alongside a job posting / company name.

---

## Pre-flight

1. Read `profile/master-resume.md`
2. Read `skills/_shared/writing-style.md`
3. Identify the company name from context (posting, CSV row, or user message). If absent, ask once.

---

## Steps

### Step 1 — Company research

Run a brief web search on the company (check `domains.md` first):
- What they do and who they serve
- Mission or stated values (from their website, not Glassdoor)
- Any recent notable work, product, or initiative relevant to the role

Cap research at 2–3 sources. Do not invent claims. If a fact cannot be verified, omit it.

### Step 2 — Draft each answer

For each question:
- Answer in ≤ 500 characters (hard limit — count before delivering)
- Pull from resume experience where relevant; tie to the company where it adds meaning
- Write in first person, active voice
- Match tone to the JD signal (default: confident and direct)

### Step 3 — Style scan

Run the post-generation scan from `writing-style.md` before delivering:
- No banned words or phrases
- No AI-sounding constructions
- No unnecessary adverbs
- No em-dashes
- No generic openers ("I am excited to...", "I am passionate about...")

### Step 4 — Deliver

Present each answer under its question as a labeled block:

```
**Q: [question text]**
[answer]
[character count] / 500
```

If any answer required a framing call that could fail the Interview Backtrack Test, note it with ⚠️ after that answer.

---

## Constraints

- Hard character limit: 500 per answer. If the draft exceeds this, cut — do not ask the user to approve an overlength answer.
- Do not include company claims that weren't verified in Step 1.
- Do not use the writing-style banned list as a checklist to recite — just fix violations silently before delivering.
- If the question is vague ("Why do you want to work here?"), default to mission alignment + one specific, verified company detail + one concrete candidate credential.
