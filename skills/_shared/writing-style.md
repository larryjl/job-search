# Shared Writing Style — Job Search

All content-generating skills (tailor-resume, cover-letter-generator, cold-outreach, linkedin-optimizer) must
follow these rules. This is the single source of truth for voice, tone, and banned language.
Do not redefine these values inside individual skill files.

---

## Tone

Match tone to JD signal:
- Formal JD → professional and confident
- Startup / casual JD → direct and energetic
- Values-heavy JD → open with mission alignment

Default when unclear: **confident and direct**.

Write as the candidate would speak in a good interview — not stiff corporate-speak, not casual chat.
First person, active voice. "I built" not "a system was developed."

---

## Voice Rules — Non-Negotiable

### Banned phrases and clichés

Never use these. Rewrite the full sentence rather than just deleting the phrase:

- "I am excited to" / "I am passionate about" / "I look forward to"
- "proven track record" / "results-driven" / "team player" / "strategic thinker" / "forward-thinking" / "results-oriented"
- "bring value" / "contribute to success" / "leverage my skills" / "hit the ground running"
- "drive results" / "synergies" / "game-changing" / "innovative solutions" / "dynamic environment"
- "cross-functional collaboration" — unless it is a direct quote from the JD
- Rhetorical questions ("What excites me most about this role is...")
- Corporate enthusiasm openers ("What drew me to this opportunity...")

### Banned AI-sounding constructions

These constructions read as AI-generated and must never appear:

- "navigating the complexities of"
- "sits at the intersection of"
- "in today's rapidly evolving landscape"
- "I am uniquely positioned to"
- "leveraging my expertise"
- "a proven ability to"
- "a track record of"
- "seamlessly"
- "robust" (as a generic positive descriptor)
- "holistic"

### Unnecessary adverbs — delete on sight

- "deeply", "truly", "highly", "uniquely", "meticulously", "notably", "remarkably"

### Banned words — resume bullets and cover letters (with replacements)

Rewrite the full sentence containing the banned word. Never just delete it.

| Banned | Replace with |
|--------|-------------|
| Delve | investigate, analyze, explore |
| Harness | use, apply, draw on |
| Landscape | environment, market, field (literal use is fine) |
| Spearheaded | led, launched, drove |
| Championed | led, advocated for |
| Leveraged | used, applied, drew on |
| Fostered / Cultivated | built, developed |
| Streamlined | simplified, reduced, reorganized |
| Robust | strong, reliable, scalable |
| Seamless | smooth, consistent |
| Cutting-edge | modern, advanced |
| Transformative | significant, high-impact |
| Innovative / Dynamic (self-descriptor) | delete — show it instead |
| Synergy | collaboration, alignment |
| Game-changing | significant, major |
| Responsible for | start with action verb |
| Helped to / Assisted with / Worked to / Sought to / Aimed to | own the action directly |
| Tapestry / Realm / Paradigm | delete or be specific |
| Multifaceted / Nuanced | be specific instead |
| Pivotal | key, central |
| Embark | start, begin |
| Utilize | use |
| Cornerstone | foundation, core |

### General sentence discipline

- Every sentence must earn its place. If it adds no information, cut it.
- Vary sentence length. Short declarative sentences carry weight.
- Demonstrate, don't state. Instead of "I am a team player", write a specific example of teamwork and its outcome.
- No em-dashes (—). Use periods, commas, or semicolons instead.
- No apologetic or overly humble language. Not "I think I could contribute" but "I bring X, demonstrated by Y."
- Verb ownership must match actual role. Full-ownership verbs (built, led, designed, owned, launched) only where the candidate had sole or primary ownership. Use hedged verbs (contributed to, partnered on, supported) for collaborative or secondary roles. Mismatched verbs are a credibility risk — a single probing interview question will expose them.
- No gerund analysis endings on resume bullets. Bullets must not end with vague "-ing" phrases like "...advancing the field," "...contributing to improved outcomes," "...enabling new capabilities." ("...contributing to a 15% reduction" is fine — it ends with a metric. "...contributing to improved efficiency" is not.) Do not auto-fix these — flag them with ⚠️ in the post-output summary so the candidate can rewrite with the real context.
- Cover letters: mix sentence lengths deliberately. Three or more consecutive sentences of similar length read as AI-generated. Vary between short (8–12 words) and longer (20–30 words) sentences.
- Cover letters: avoid starting consecutive paragraphs with the same structure (e.g., "My research…", "My experience…", "My approach…").

---

## Interview Backtrack Test

Before finalising any framing of the candidate's experience, ask: could the candidate comfortably
explain this in an interview without backtracking? If they'd need to say "well, what I actually
meant was..." — it's too far.

| Zone | Definition | Action |
|------|-----------|--------|
| **OK** | Reordering content to lead with what's most relevant; using natural synonyms for the target domain; emphasising one aspect of a broad role | Proceed |
| **Flag it** | Combining academic + industry experience into a single claim that implies it was all industry; describing work using the posting's specific terminology when the actual work was adjacent but not identical | Note it in the post-output summary: "⚠️ Stretch framing: [what and why] — confirm before sending." |
| **Never** | Claiming experience the candidate doesn't have; implying they worked in a domain they haven't | Do not include |

When a framing decision falls in the "flag it" zone:
- **Cover letters:** note it in the Step 5 post-output summary.
- **Resumes:** surface it in the Step 4.5 reviewer agent output with a `⚠️` marker.

---

## No Unverified Company Claims

Every company-specific statement (partnerships, product names, technology descriptions, expansions,
strategic initiatives) must be independently verified via WebFetch or WebSearch before inclusion.
Do not trust reviewer agent research at face value — verify before incorporating.
If a claim cannot be verified, rephrase in general terms or omit it.

---

## Signals of Human Writing — Aim For These

The banned lists tell you what to remove. These tell you what to put in their place:

- **Front-loaded specifics.** Lead with the concrete thing, not the framing. "Reduced onboarding time by 40%" not "Contributed to process improvements that resulted in..."
- **Named entities.** Tool names, method names, team names, product names. Specificity reads as human.
- **Audience-appropriate vocabulary.** Use the JD's terminology, not generic synonyms. If the JD says "activation rate," write "activation rate," not "engagement metric."
- **Short connecting words in cover letters.** "so," "but," "then," "and" — not "consequently," "however," "additionally," "subsequently."
- **One concrete detail per cover letter page.** A specific problem you worked on, a decision you made, a result with a number. Not a general claim about your approach.

---

## Post-Generation Scan — Run Before Delivering Any Document

Scan the full text before presenting the preview to the user. Fix any failure before proceeding.

- [ ] Any banned word from the tables above?
- [ ] Any banned AI-sounding construction?
- [ ] Any resume bullet ending with a vague `-ing` phrase (e.g., "...improving outcomes," "...advancing the work")? → flag with ⚠️, do not auto-fix
- [ ] Any unnecessary adverb from the banned list?
- [ ] Cover letter: three or more consecutive sentences of similar length?
- [ ] Cover letter: consecutive paragraphs opening with the same structure?
- [ ] Cover letter: generic opener instead of a company-specific reference in the first sentence?
- [ ] Any passive voice where active is possible ("was responsible for" → action verb)?
- [ ] Any claim that would fail the Interview Backtrack Test?
