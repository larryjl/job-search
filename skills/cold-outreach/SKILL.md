---
name: cold-outreach
description: "Generates personalised cold outreach messages — LinkedIn connection requests, InMails, and cold emails — that feel human and reference something real about the recipient or their company. Not spammy copy-paste. Designed to get replies. Trigger on: '/cold-outreach', 'write me a connection request', 'cold DM for this person', 'reach out to a recruiter', 'message this hiring manager', 'LinkedIn message for this job', or any request to write a professional outreach message to someone the candidate has not spoken to before."
---

# Cold Outreach Skill

The master resume is already in this project. Never ask for it.

---

## Step 1 — Input Detection

**What's needed:** recipient, purpose, channel, recipient context (name, company, role, LinkedIn profile detail, shared connection, company announcement).

**Input handling:**
- **All context provided** → proceed immediately
- **Recipient name + company only** → use web search to find context
- **"/cold-outreach" with nothing** → ask: "Who are you reaching out to, and what's the goal?"

**Channel character limits:**
- **LinkedIn connection request** → 300 characters max
- **LinkedIn InMail** → 200 character subject + 1,900 character body
- **Cold email** → aim for under 200 words

---

## Step 1.5 — Domain Access Gating

Ask: "I'll personalise this message by researching [Company]. Can I search the web for context? (yes / no)"

If yes, check each domain against `## cold-outreach` in `.claude/config/domains.md` before use. If not approved, ask permission and add to whitelist if granted. Planned domains: `linkedin.com`, `crunchbase.com`, `techcrunch.com`, `google.com`, `pitchbook.com`.

---

## Step 2 — Research the Recipient

**If a LinkedIn profile URL is provided:** use Claude in Chrome (`mcp__Claude_in_Chrome__navigate` then `mcp__Claude_in_Chrome__get_page_text`) to load and read the profile directly. Extract: current role and tenure, previous roles, any listed skills or summary text, featured posts or articles. Do this silently before writing.

**If no LinkedIn URL but a name + company is provided:** fall back to web search using approved domains.

Silently gather context:

**Person:** current role and tenure, recent public posts or articles, shared connections, career trajectory.

**Company:** recent news (funding, launches, expansions), what they build and what problem they solve, job postings signalling team growth, culture signals.

---

## Step 3 — Tone Calibration

**Recruiter:** direct, specific about the role or team, one clear ask.

**Hiring manager:** more personal, reference something specific about their work, softer ask ("would love your perspective").

**Employee (referral path):** warmest tone, lead with connection or common ground, honest and low-commitment ask.

**Warm contact / reconnecting:** reference shared history genuinely, brief update on where you are now, ask that feels like a natural continuation.

---

## Step 3.5 — Load Writing Style

Read `skills/_shared/writing-style.md` before writing. All messages follow its banned words, banned constructions, and signals-of-human-writing rules.

Outreach-specific reminders:
- No unnecessary adverbs: "deeply", "truly", "highly", "uniquely", etc.
- No AI constructions: "navigating the complexities of", "I am uniquely positioned to", "seamlessly", etc.
- No banned phrases: "excited to", "passionate about", "proven track record", "bring value", "leverage"
- Short connecting words over formal transitions: "so", "but", "and" — not "consequently", "however", "additionally"
- Named entities over generalities. Front-load specifics.
- No em-dashes.

---

## Step 4 — Write the Messages

Generate **2 variants** — different angles, not just tone shifts.

### LinkedIn Connection Request (300 chars max)

- No links
- Never start with "I" or "Hi, I"
- Reference one specific thing about them or their company
- Implicit ask only — no explicit job requests
- End with a reason to accept

```
Option A (N chars):
[Message text]

Option B (N chars):
[Message text]
```

### LinkedIn InMail

**Subject:** specific, curious — not "Exciting opportunity", "Quick question", or "Touching base".

**Body:**
- Para 1 (2 sentences): why you're reaching out + the one specific researched detail
- Para 2 (2–3 sentences): one achievement relevant to their world
- Para 3 (1–2 sentences): the ask — specific, small, easy to say yes to
- Sign-off: first name only

```
Option A:
Subject: [subject line]

[Body]

---

Option B:
Subject: [subject line]

[Body]
```

### Cold Email

**Subject:** same rules as InMail.

**Body:**
- Line 1: specific reference showing real research
- Lines 2–3: one relevant achievement from master resume
- Line 4: one specific ask (15-minute call, feedback, introduction)
- P.S. (optional): one human detail that makes the email memorable

```
Option A:
Subject: [subject line]

[Body]

---

Option B:
Subject: [subject line]

[Body]
```

---

## Step 5 — Output Block

```
─────────────────────────────────────────
📨 Cold Outreach — [Recipient Name / Role] at [Company]
Channel: [LinkedIn Connection / InMail / Cold Email]
─────────────────────────────────────────

[All message variants]

─────────────────────────────────────────
💡 Personalisation used:
[One sentence on the specific detail referenced and where it came from]

📋 Sending tips:
• Send connection requests Tue–Thu, 9–11am local time
• If no InMail response in 5 days, follow up once with a 2-sentence nudge
• Track replies: Name / Company / Sent / Reply / Outcome
• Best follow-up is a new reason: announcement, article, job posting

─────────────────────────────────────────
```

---

## Step 6 — Follow-up Messages (on request)

- Maximum 3 follow-ups total
- Each must add something new — not "checking in"
- Follow-up 1 (5 days): new angle or new context
- Follow-up 2 (10 days): graceful close — give them an easy out
- Never: "Just circling back", "Following up on my previous message", "Touching base"

**Graceful close template:**
"[Name], I know your inbox is full. I'll leave it here — but if timing is ever right, I'd love to connect. [First name]"

---

## Output Rules

- 2 variants for every message type
- Every message references something specific — no generic messages
- Never fabricate context — say what's missing if no recipient details are provided
- Stay within character limits
- One ask per message
- Use Claude in Chrome to read a LinkedIn profile when a URL is provided; fall back to web search otherwise
- Respect domain whitelist

---

## Post-Generation Scan

Run before presenting any message. Fix any failure before proceeding.

- [ ] Any banned word from `skills/_shared/writing-style.md`?
- [ ] Any AI-sounding construction?
- [ ] Any unnecessary adverb?
- [ ] Any banned phrase?
- [ ] Generic subject line?
- [ ] Connection request starting with "I" or "Hi, I"?
- [ ] Three or more consecutive sentences of similar length?
- [ ] Passive voice where active is possible?
- [ ] Any em-dash?
