# Filter: Filter Score Layer

Runs automatically after `/job-scout` and before any `/job-match`.
Scores each job 0–10 across two dimensions using `.claude/memory/targets.md` and `profile/skills-inventory.md` as inputs.
Does NOT require the master resume.

---

## Inputs

- `profile/targets.md` — target roles, seniority, location, visa, industry preferences (read from `profile/targets.md`, not `.claude/memory/targets.md`)
- `profile/skills-inventory.md` — candidate's tools and skills for Skills Match scoring
- Job listing data from `/job-scout` — title, responsibilities, location, requirements

**Does NOT use `profile/master-resume.md`.** The filter scores against stated targets and skills inventory only — full capability matching happens in `/job-match`.

---

## Location Block

Before calculating dimension scores, check for hard-block conditions,
if any of the following are present, flag the role ⛔ with the reason and do not run `/job-match`:

- Role is located outside candidate's province (Alberta) or country (Canada) AND explicitly states on-site, in-person, or relocation required
- Role requires citizenship or work authorisation or security clearance not held in `targets.md`
- Role requires a licence or credential listed not held in `targets.md`

---

## Scoring Rubric

### 1. Role Match (0–5)

Does the job title and core responsibilities match the candidate's target role?

**Before scoring:** Read the `## Target Roles` section of `profile/targets.md`. Score against the listed target roles.

| Score | Criteria |
|-------|----------|
| 5 | Title and responsibilities are an exact match to a listed target role |
| 4 | Title differs slightly but core work matches a listed target role |
| 3 | Meaningful overlap with a listed target — at least 60% of responsibilities align |
| 2 | Related role but not a listed target; significant scope mismatch |
| 1 | Tangentially related to any listed target |
| 0 | Unrelated to all listed targets |

### 2. Skills Match (0–5)

Do the role's required tools and skills align with the candidate's skills inventory?

**Before scoring:** Read `profile/skills-inventory.md`. Score required tools/skills only — preferred, nice-to-have, or familiarity-only items do not count as missing.

| Score | Criteria |
|-------|----------|
| 5 | All required tools present, experience level met or exceeded, most nice-to-haves also met |
| 4 | All required tools present, slight mismatch on experience level or nice-to-have skills |
| 3 | 1 required tool missing but an easily bridgeable gap or an alternative tool is met|
| 2 | 2 required tools missing but a bridgeable gap or alternative tools are met|
| 1 | 3+ required tools missing or experience level is not bridgeable|
| 0 | Core stack largely foreign — majority of required tools absent |

Note specific missing tools in the Reason column whenever Skills Match ≤ 3.

---

## Threshold

| Score | Decision |
|-------|----------|
| 9–10 | Strong — recommend for `job-match` |
| 6–8  | Eligible — eligible for `job-match` |
| 4–5  | Borderline — display with reason, skip unless overridden |
| 0–3  | Skip — do not run `job-match`,  skip unless overridden |

---

## Output Format

The Filter Score is a /10 gate score. It is distinct from match score, which is tracked in a separate column.

Display a results table. Show all jobs, including skipped ones.

Example:
```
| #  | Company  | Role              | Filter Score | Status      | Reason (if skipped/flagged)     |
|----|----------|-------------------|--------------|-------------|---------------------------------|
| 1  | Shopify  | Senior Analyst    | 9/10         | ✅ Match     |                                 |
| 2  | Stripe   | Analytics Eng     | 7/10         | ✅ Match     | Missing: dbt                    |
| 3  | Acme Co  | Data Engineer     | 4/10         | ⚠️ Skip      | Missing: Spark, Airflow         |
| 4  | US Corp  | Data Analyst      | ⛔           | ⛔ Hard block | Requires US citizenship         |
```

---

## Potential Future Dimensions

**Seniority Fit (0–5):** Score against the target seniority band in `targets.md`. Direct match → 5; one level off → 4; two levels off or ambiguous → 3; no signals or significant mismatch → 2; clear mismatch (e.g. Director when targeting Senior IC) → 1. Would require adjusting threshold (~≥9/15) to maintain selectivity.

**Industry Relevance (0–5):** Score against preferred industries in `targets.md`. Exact match → 5; adjacent/overlapping domain → 4; broadly tech-adjacent → 3; unrelated → 2; poor fit → 1; hard constraint mismatch → 0. Only worth adding if industry targeting becomes more selective.

**Geography / Visa / Constraints (0–5):** Score against location, remote policy, and work authorisation in `targets.md`. All satisfied → 5; minor friction (hybrid vs remote) → 4; one constraint borderline → 3; policy unknown → 2; outside target location with unspecified remote → 1. Currently handled via hard-block for disqualifying cases.

**Compensation Fit (0–5):** Score against the salary floor and target range in `targets.md`. Below floor → 0–1; within range → 4–5; unknown → 2. Add when enough postings include comp data to make scoring reliable.

**Contract/Permanent Fit (0–5):** Score against stated contract preference in `targets.md`. Only worth adding if there is a clear preference — otherwise adds noise.
