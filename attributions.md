# Attributions

This project incorporates ideas and patterns adapted from the following open-source projects.

---

## career-os
**Author:** Harsimran Walia
**Source:** https://github.com/harsimranwalia/career-os

This project was originally built on career-os as its foundation. The core skill architecture (job-scout, job-match, tailor-resume, cover-letter-generator, interview-prep, mock-interview, linkedin-optimizer, cold-outreach) and the composable skills system running on Claude are derived from this project.

---

## career-helper
**Author:** Prosper AI Consulting
**Source:** https://github.com/Zal4DW/career-helper

**Adapted into this project:**
- Methodology transfer test concept (folded into bullet strength evaluation in `skills/_shared/reviewer-agent.md`)
- Verb discipline and overclaiming guidance (added to `skills/_shared/writing-style.md` and `reviewer-agent.md`)

---

## resume-tailoring-skill
**Author:** Varun R
**Source:** https://github.com/varunr89/resume-tailoring-skill

**Adapted into this project:**
- Experience discovery session state definitions ("active JD" and "tailored draft active")
- Explicit gap list input path (Step 1 third branch in `skills/experience-discovery/SKILL.md`)

---

## job-search-agent
**Author:** Byren Cheema
**Source:** https://github.com/byrencheema/job-search-agent

**Adapted into this project:**
- Adzuna API retry pattern (loop with exception-type branching, return None on failure) used in `skills/scout-adzuna/adzuna_search.py`
