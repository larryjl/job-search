---
name: experience-discovery
description: "Surfaces undocumented real experience through structured conversational branching. Trigger on: '/experience-discovery', 'find hidden experience', 'discover experience', 'what experience am I missing', or when a user says they might have relevant experience not on their resume."
---

## Purpose

Identify real, lived experience the candidate has but hasn't documented — then offer to incorporate it into the master resume and/or the tailored resume in progress.

This skill does NOT rewrite bullets. It asks questions, captures what it finds, presents a summary, and asks where to add the new content.

---

## Step 0 — Load Inputs

**Required (at least one of):**
- Active JD in session — JD text present earlier in the current conversation (pasted, fetched via URL, or carried forward from a `/job-scout`, `/job-match`, or `/tailor-resume` run), OR
- Match report (from `/job-match-full`) in session or referenced by path, OR
- Explicit gap list from the user (pasted directly)

**Also read:** `profile/master-resume.md`

**"Tailored resume draft active" (used in Step 4):** `/tailor-resume` was run earlier in this session and a plain-text preview was shown — regardless of whether the file has been saved to disk yet. If `/tailor-resume` has not run in this session, no tailored draft is active.

**Path resolution (required before any file read/write):**
```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../lib'))
from project_paths import get_project_root
```

If no JD, match report, or gap list is available: "I need a job description, match report, or gap list to run discovery. Paste a JD or run `/job-match` first."

---

## Step 1 — Identify Gaps

**If a match report is available in session:** extract the Gap table from Block B directly — do not re-derive from the JD.

**If only a JD is available:** derive gaps by comparing JD requirements against `profile/master-resume.md`. Apply the same P1/P2/P3 priority tiers defined in `skills/tailor-resume/SKILL.md` Step 1 (P1 = deal-breakers, P2 = strongly desired, P3 = nice-to-have). Focus discovery on P1 and P2 gaps only.

**If a gap list was provided directly by the user:** treat all listed gaps as P1 — the user chose to list them, so assume they're all worth exploring. Skip any derivation step and build the queue from the list as-is.

**Build a discovery queue:** ordered list of gaps to explore, sorted by:
1. Hard blockers first
2. P1 gaps second
3. P2 gaps third
4. Omit P3 gaps — not worth discovery time

Cap the queue at **5 gaps** per session. If there are more than 5, surface only the highest-priority ones and note: "Focusing on the top 5 gaps — let me know if you want to explore others."

**Display the queue before starting:**

```
🔍 Experience Discovery — [Company] [Role]

I found [N] gaps worth exploring. I'll ask about each one — answer as much or as little as you like. Type **skip** to move past any question.

Gaps to explore:
1. [Gap] — [Hard blocker / P1 / P2]
2. ...

Ready? (yes / adjust list)
```

Wait for confirmation before starting.

---

## Step 2 — Branching Discovery

Work through the queue one gap at a time. For each gap:

**Show gap header:**
```
─────────────────────────────
Gap [N/Total]: [Gap Name]
[Hard blocker / P1 / P2]
─────────────────────────────
```

**Then apply the appropriate branching pattern:**

### Technical Skill Gap

```
INITIAL PROBE:
"I noticed the role requires [SKILL]. Have you worked with [SKILL] or [RELATED_AREA]?"

BRANCH A — Direct experience:
  → "Tell me more — what did you use it for?"
  → "What scale? [Relevant metric — users, volume, team size, etc.]?"
  → "Was this production or development/testing?"
  → "What specific challenges did you solve?"
  → "Any metrics on [performance / reliability / cost]?"

BRANCH B — Indirect involvement:
  → "What was your role in relation to the [SKILL] work?"
  → "Did you [action1], [action2], or [action3]?"
  → "What did you learn about [SKILL] from that?"
  → Assess: is the involvement substantial enough to mention?

BRANCH C — Adjacent technology:
  → "Tell me about your [ADJACENT_TECH] experience."
  → "Did you do [relevant_activity]?"
  → Assess: close enough to frame as related expertise?

BRANCH D — Personal / learning:
  → "Any personal projects, courses, or self-learning?"
  → "What did you build or deploy?"
  → "How recent was this?"
  → Assess: include only if recent and substantive

BRANCH E — Complete no:
  → "Any other [broader_category] work?"
  → If no: move to next gap, flag for cover letter
```

### Soft Skill / Leadership Gap

```
INITIAL PROBE:
"This role emphasises [SOFT_SKILL]. Tell me about a time you've [demonstrated_that_skill]."

BRANCH A — Strong example:
  → "What teams or stakeholders were involved?"
  → "What was the challenge?"
  → "How did you drive the outcome?"
  → "What was the result? Any metrics?"

BRANCH B — Vague or uncertain:
  → "Let me ask differently — have you ever [reframed_question]?"
  → "What was the situation?"
  → "How many stakeholders? What made it hard?"

BRANCH C — Project-specific:
  → "What was your role vs. others on the team?"
  → "Who did you coordinate with outside your team?"
  → "How did you ensure alignment?"

BRANCH D — Volunteer / side work:
  → "What was the scope and timeline?"
  → "What skills from that are relevant here?"
  → "Any measurable outcomes?"
```

### Recent Work Probe (run last, after specific gaps)

After exhausting the gap queue, always close with:

```
"Last question — what have you been working on in the last 6 months that isn't on your resume yet? Even small improvements, new tools, or learning counts."

BRANCH A — Describes a project:
  → "What was your role?"
  → "What technologies or methods?"
  → "What problem were you solving?"
  → "What was the impact?"
  → Check: does this address any remaining gap?

BRANCH B — Mentions multiple things:
  → "Let's go through each. Starting with [first]..."
  → Prioritize by gap relevance

BRANCH C — "Nothing new":
  → "What about process improvements, mentoring, or new tools you've picked up?"
  → "Anything that might seem too small to mention?"
```

### Branching Principles

- **Start broad, go narrow.** Initial probe is open-ended; follow-ups drill based on what they share.
- **Listen and branch dynamically.** Promising answer → explore deeper. "No" → try adjacent or move on. Unclear → rephrase.
- **Cross-reference.** "Earlier you mentioned [X] — does that relate here too?"
- **Move on gracefully.** After 2–3 attempts with nothing → "Okay, let's move on — I'll flag that one for the cover letter."
- **Never fabricate.** Only capture what the user actually said. Do not embellish or assume details.

---

## Step 3 — Discovery Summary

After the queue is complete, present a summary:

```
✅ Discovery Complete

Here's what we found:

CAPTURED EXPERIENCE:
┌─────────────────────────────────────────────────────────────────┐
│ Gap: [Gap Name]                                                  │
│ What you said: "[brief quote or paraphrase]"                     │
│ Suggested bullet: "[Action verb + What + How + Result/metric]"   │
│ Confidence: Direct / Transferable / Adjacent                     │
└─────────────────────────────────────────────────────────────────┘
[repeat for each captured item]

STILL UNADDRESSED:
• [Gap] — no usable experience found. Mitigation: [cover letter angle / course / project].

Nothing was found for [N] gap(s). Those remain as noted gaps.
```

**Confidence levels:**
- **Direct** — candidate used the skill explicitly; strong evidence
- **Transferable** — adjacent experience that maps credibly to the requirement
- **Adjacent** — related but indirect; frame carefully, don't overstate

---

## Step 4 — Offer to Add

Ask:

```
Where would you like to add these findings?

A) Master resume only (profile/master-resume.md)
B) Current tailored resume in progress only
C) Both master resume and current tailored resume
D) Show me the bullets first — I'll decide after

(Type A / B / C / D, or "skip" to end without saving)
```

**If D:** Show each suggested bullet in a code block. After review, ask again: "Add to (A) master, (B) tailored, (C) both, or **skip** to discard?"

**If A or C — master resume:**
- Locate the most appropriate role entry in `profile/master-resume.md` (match by employer, timeframe, or role type)
- Append the new bullet(s) to that role's bullet list
- If no clear role fits (e.g., personal project, recent learning): add a brief `## Additional Experience` or `## Projects` section at the bottom, or ask the user where to place it
- Do not rewrite existing bullets — only append
- Confirm: "✅ Added [N] bullet(s) to master resume under [Role / Section]."

**If B or C — tailored resume:**
- Only applies if a tailored resume draft is active in the current session
- Insert the new bullet(s) into the appropriate role in the in-progress draft, at the position that best matches JD relevance ordering
- Confirm: "✅ Added [N] bullet(s) to the tailored resume draft under [Role]."
- If no tailored resume is in progress: add to master resume (if A or C was selected), then suggest: "No tailored resume is active yet — run `/tailor-resume` now to build one with these new bullets already in the master resume."

**Writing rules for new bullets (same standards as tailor-resume):**
- Action verb + What + How/Why + Result/Impact
- Quantify where possible — use what the user actually said (don't inflate)
- No banned words (check `skills/_shared/writing-style.md`)
- Pass the Interview Backtrack Test: candidate must be able to answer follow-up questions about every claim
- No AI-sounding constructions

---

## Step 5 — Wrap Up

```
🔍 Discovery session complete.

Added: [N] bullet(s) to [master resume / tailored draft / both]
Flagged for cover letter: [gaps with no usable experience]

→ /tailor-resume       — generate or update tailored resume with new content
→ /cover-letter-generator — address remaining gaps in the cover letter
→ /job-match           — re-evaluate match score with new experience included
```

---

## Rules

- Never fabricate, infer, or embellish. Only capture what the user explicitly said.
- Never add a bullet claiming a skill the user said they don't have.
- Always apply the Interview Backtrack Test to every suggested bullet.
- Respect `skills/_shared/writing-style.md` for all bullet language.
- If the user types **skip** at any point, move to the next gap immediately — no pressure.
- Keep the session focused. If the user gives a long narrative, extract the relevant bullet and move on.
