# Job Search Learnings

_This file is written and updated by Claude after meaningful outcomes. Do not edit manually unless correcting something._

---

## Companies Evaluated
<!-- Running log of all /job-match runs. Sorted chronologically (oldest first). -->

| Company | Role | Match Score | Decision |
|---------|------|-------------|----------|
| CIHI | Senior Business Intelligence Analyst (Qlik) | 85/100 | Apply — strong fit; address Calgary/Ottawa location proactively |
| Computer Modelling Group (CMG) | Enterprise Applications Specialist | 71/100 | Apply — good fit, address Salesforce admin cert and Zendesk gap; watch comp (below-market reputation) and financial headwinds |
| Empire Life | Process Improvement Leader | 83/100 | Apply 🟡 Good fit — reframe resume summary + QHR bullets to lead with transformation language; add PI methodology keywords; domain switch (healthcare→insurance) is not a blocker |
| Deloitte | Data Quality Manager (Master Data) | 75/100 | Apply 🟡 Good fit — address Informatica MDM gap in cover letter; lead with secure messaging governance project; target $110K–$125K |
| Anatta Design | Business Analyst | 64/100 | Stretch 🟠 — Only pursue after getting hands-on with Shopify (dev store + Partner cert); confirm Canadian hiring model (employee vs contractor) |
| Deloitte | Senior Analyst - Technical, Clean Economy (Gi3) | 47/100 | Not recommended 🔴 — hard domain mismatch; requires engineering/science degree in clean energy; no energy sector experience |
| Deloitte | Senior Analyst, Data Modernization & Intelligence | 73/100 | Apply 🟡 Good fit — MS Purview and M365 Copilot gaps are familiarity-level only; deprioritise vs health analytics/data engineering roles |
| Deloitte | Senior Manager Data Analytics and AI/ML Products | 58/100 | Stretch 🟠 — Reframe to data product leader; address platform gaps; confirm Calgary hybrid is genuine before investing in full tailoring |
| Deloitte | Technology Manager (2-year Fixed Term) | 71/100 | Apply 🟡 Good fit — reframe as delivery manager, not data analyst; bridge QHR scope to Ascend platform; SAFe gap is addressable |
| Alignerr | Hospital Health Data Governance Lead (AI Training) | 80/100 | Apply — domain credentials are an exact match; best as supplemental freelance income; confirm hourly rate before committing hours |
| Government of Alberta (DDD) | Data Engineer — Senior | 81/100 | Apply 🟡 Good fit — no prior GoA contracts; earlier entries were fabricated from the job application itself (corrected 2026-05-04); honest Azure (~1 yr) and SSIS/ADF partial depth are real gaps but not disqualifying; requirements matrix is the critical submission document |
| Unknown Client (Calgary AB) | Senior Data Quality Analyst | 65/100 | Stretch 🟠 — ERP domain gap (SAP B1/NetSuite/financial reconciliation); strong migration/SQL/governance proof; 1-month initial term; only apply if pipeline is thin |
| WELL Health Technologies | Data Engineer | 75/100 | Apply 🟡 — applied 2026-04-29; corrected from 86 on 2026-05-05 — Snowflake/Python/Airflow/dbt/Fivetran were required (not preferred); Python beginner level is hard gap; healthcare DE depth still differentiator |
| TELUS Health | Senior QA Analyst – Data & Test Case Preparation | 42/100 | Not recommended 🔴 — SQA is the core job function and is entirely absent from Lawrence's background; SQL and multi-project management are assets but secondary; pension domain (not healthcare) adds second layer of unfamiliarity; wait for a data-primary TELUS Health role |
| Neo Financial | AML Data Analyst | 68/100 | Stretch 🟠 — AML/financial crime domain gap is real (no direct experience); data skills (SQL, dashboards, discrepancy investigation, cross-functional) are a solid match; JD frames domain as "strong asset" not required; cover letter must bridge regulated healthcare data governance to AML compliance operations |
| Alberta Innovates | Manager, Data Platforms | 61/100 | Stretch 🟠 — 4 mandatory Microsoft certs (DP-600, DP-203, AI-102, AZ-305) not held; 7yr vs 10yr IT req; Microsoft Fabric absent; leadership/platform delivery genuine; only apply if actively pursuing certs |
| WCB Alberta | Data Scientist | 49/100 | Not recommended 🔴 — Python ML and NLP/LLM are mandatory hard gaps; junior band (BSc+1yr min) creates overqualification; excellent domain fit (health outcomes data); monitor for DA/analytics manager roles |
| Everest Clinical Research | Clinical Data Manager | 46/100 | Not recommended 🔴 — EDC platform (Medidata/Oracle Inform/Veeva) absent; no CRF design, ICH/GCP, or MedDRA experience; CRO clinical trials is a distinct subdomain not bridgeable via healthcare analytics framing; comp low end ($60K) below floor |
| Fasken | Manager, Data Analytics | 74/100 | Apply 🟡 Good fit — primary target title; $125–150K posted; Power BI gap mitigated by Tableau acceptable; law firm governance/ethical walls directly maps to QHR regulated data background |
| StackAdapt | Senior Client Analytics Partner | 67/100 | Stretch 🟠 — ad tech domain gap (MTA/ABM/DSP) is real; SQL/analytical base strong; apply only if open to media analytics pivot |

---

## Leadership & Management Context

### QHR Technologies — Operations Manager role
- Lawrence co-managed a team of ~20 alongside two other managers, each owning separate work streams day-to-day. For decisions with team-wide impact (infrastructure, policy, hiring), Lawrence would lead the discussion and prompt input from all managers.
- He explicitly uses situational leadership: heavy hands-on coaching for juniors (solution reviews, best practices, critical thinking), direction + autonomy for seniors. Goal is always to progress individuals to independent work. Milestone checklists used to formalize readiness during onboarding.
- Scaling the data migration infrastructure (100GB to 500GB capacity, 20x speed) had a cultural impact beyond throughput: engineers freed from repetitive interrupt-heavy tasks shifted to taking on complex problems, challenging their own code, and supporting each other. "Capability compounded" is Lawrence's framing for this outcome — strong for leadership interview questions and management-role cover letters.
- Built formal team infrastructure: onboarding program with milestone checklists, data dictionary and knowledge base, dedicated test environment, senior-junior coaching pairs, explicit advancement paths from junior to senior.

## Match Patterns
<!-- Cumulative learnings from /job-match runs. Grouped by theme. -->

### Healthcare / Public Sector Data Roles
- **HL7/FHIR:** Lawrence worked with HL7 and FHIR formats throughout his time at QHR — the EMR data migration work was largely conducted in these formats. This is a genuine, substantive skill. Surface it prominently for healthcare/health IT roles. Do NOT include in skills or bullets for roles outside the health industry — irrelevant and adds noise.
- Lawrence's Qlik + health data combo is rare and highly valued in Canadian public health sector roles
- SCPCN Qlik + data warehouse build is the strongest case study for BI-specialist roles
- MicroStrategy is a minor recurring gap — not a blocker in any health BI role evaluated so far
- Location (Calgary vs Ottawa/Toronto) is a recurring logistics question to address upfront
- WELL Health: healthcare DE roles reward provincial health privacy compliance experience and EMR pipeline depth over platform-specific tooling breadth — Lawrence's QHR background is the differentiator
- **Canadian healthcare privacy law — never cite PIPEDA for healthcare roles.** Provincial health privacy legislation governs healthcare data in Canada: Alberta uses the Health Information Act (HIA), Ontario uses PHIPA, BC uses PIPA. PIPEDA is federal and largely superseded in provincially-regulated healthcare contexts. HIPAA is the US equivalent and should only appear when a role explicitly mentions US compliance requirements.

### QHR Operations Manager — Strongest Proof Point
- Lawrence's QHR Operations Manager (250–300 projects, $20K savings, process ownership during Azure transition) is his strongest proof point for operator/transformation roles — should lead in resume for non-analytics roles
- Lawrence's Power BI + Salesforce operational use (QHR) is a strong proof point for enterprise application roles but needs reframing from "analyst" to "system owner" language
- Power BI experience at QHR was limited (sprint planning dashboards, not primary BI platform); do not overstate beyond 3 years — Qlik is the primary BI tool
- For non-data-primary roles at this level, the resume summary must be completely rewritten per application

#### QHR Azure Work — Ground-Truth Calibration

**Critical distinction:** Infrastructure migration (on-premises → Azure cloud storage) was owned by QHR's IT infrastructure team, not Lawrence. Lawrence owned the **operations and process side** — adapting the team's 250–300 annual client data migrations to pull from Azure storage instead of on-prem.

**What Lawrence DID:**
- Defined requirements, testing, process implementation, and risk mitigation for the new Azure-sourced workflows
- Coordinated collaboration between data, infrastructure, and development teams
- Identified risks, edge cases, and process controls
- Led requirements for secure messaging data migration (distinct privacy/governance rules, separate cloud database, role-based access, legal documentation)
- Designed updated migration processes for blob storage access patterns, data staging, environment-specific synchronization
- Created process documentation, user stories, troubleshooting guides for edge cases (blob storage, data team UI, test/prod sync)
- Drove collaboration standards between data platform and infrastructure teams to prevent integration gaps and outages
- Implemented process controls and standards for the team

**What Lawrence DID NOT:**
- Develop the technical tools for pulling data from Azure (infrastructure/development team owned this)
- Lead the infrastructure migration itself (a parallel company-wide initiative)

**Resume language calibration:**
- ❌ Overstatement: "Adapted SQL-based migration processes to Azure cloud storage, developing scripts and checkpoints to manage coordinated database cut-over from on-premises to cloud"
- ✅ Accurate: "Collaborated with IT infrastructure and development teams to identify risks, edge cases, and process controls needed as client migration workflows shifted from on-premises to cloud-based source systems; implemented process standards and documentation to handle blob storage access patterns, data staging, and environment-specific synchronization"

**Strongest fit for:** operations management, process improvement and transformation, stakeholder coordination across technical teams, risk identification and mitigation, documentation and process control implementation. **Weakest fit for:** cloud architect, infrastructure engineering, or any role expecting hands-on Azure tooling ownership — these will catch overclaiming on technical interview.

### Government / Public Sector
- GoA "equivalent size and complexity" row: QHR Technologies (600+ employees, thousands of Canadian clients including hospitals and universities, strictly regulated and audited) is strong evidence alongside AHS — use both; total 7 years, last used 2024
- GoA DDD roles: Lawrence has NO prior GoA contracts. Previous entries claiming 1 or 3 GoA contracts were fabricated — the system confused the job application itself with work history. Do not cite GoA familiarity as a differentiator based on prior employment
- Azure depth (~1 year direct) vs. requirement for cloud fluency: honest bridging is the right strategy for government scorers; overclaiming will be spotted
- Fabrication risk: never use job applications from applications.csv as evidence of prior work experience in skill matrices or requirements responses. Applications are prospective, not historical
- SSIS/ADF: both named in resume but at partial depth; government evaluators appreciate specificity about scope of use

### Domain-Specific Gaps & Bridges
- Healthcare-to-insurance domain switch is a recurring scenario; regulated compliance framing bridges it effectively
- Absence of formal Lean/Six Sigma language is a recurring ATS keyword gap for process improvement roles — worth adding even as a skills section entry
- Deloitte MDM role: Lawrence's data governance depth (QHR secure messaging, multi-jurisdictional compliance) is the strongest bridge to MDM-adjacent roles even without Informatica product experience
- For specialist-manager hybrid roles: lead with governance outcomes + team coaching; avoid leading with pure technical stack
- Anatta: eCommerce BA roles require domain-specific platform experience (Shopify) — BA/Agile generalist skills are necessary but not sufficient for agency roles
- Agency-model roles (Anatta, similar): client-facing BA with Shopify hands-on is a hard requirement that can't be bridged by adjacent experience alone
- Clean economy consulting roles (Gi3-type): require domain-specific engineering/science background in energy systems — Lawrence's regulatory/PM skills are adjacent but insufficient without the energy sector foundation
- ERP data migration roles: Lawrence's EMR migration depth (QHR 250–300/year) maps structurally but ERP financial object models (GL/AR/AP/COA/inventory) are absent — only viable for stretch applications

### Deloitte-Specific
- Deloitte internal tech roles: "communications and collaboration" domain means closer to IT ops than analytics — data skills transfer but daily work is enterprise tooling (M365/Purview), not data engineering or business analytics
- Deloitte Tech Manager: QHR Operations Manager (250–300 projects, process/requirements ownership during Azure transition, SDLC governance) is the strongest proof point — must be reframed using delivery manager language, not data language. Note: Process ownership, not infrastructure migration leadership
- Deloitte SM Data/AI: Lawrence's governance depth and transformation leadership are the strongest bridge to product leadership roles, but formal AI/ML product ownership and enterprise platforms (Snowflake, Databricks) are recurring hard gaps for this tier
- Senior Manager / Director-level data product roles require explicit product portfolio framing — "operations manager" language won't pass screening even with equivalent delivery scope
- Deloitte Senior Analyst band ($69–114K) has wide range; Lawrence's 7 years supports upper-mid ($95–105K) negotiation target
- MS Purview is appearing as a named tool across multiple enterprise/governance roles — worth getting familiar with (free tier available)
- SAFe is a recurring preferred qualification in enterprise tech delivery roles — worth pursuing certification if targeting more of these
- Informatica is a recurring MDM platform — worth a free trial / certification if targeting more MDM roles

### Modern Data Engineering Stack

**Tools on resume:** SQL Server, Azure (process-side), Power BI, Qlik, Tableau, SQL, Python (beginner), R, Stata, SPSS, Git, Salesforce, HL7/FHIR

**Universal rule for tools NOT on resume (including dbt, Snowflake, Databricks, Airflow, Fivetran, Spark, Kafka, Looker, and any other modern data tool):**
- Apply if the tool is listed as preferred, nice-to-have, or familiarity only
- If more than 1 year of experience is required on more than 1 of these tools, expect a low filter and match score — surface for human review rather than auto-skip

**Named gaps (frequently appearing in JDs):**
- dbt: no experience
- Snowflake: no experience
- Databricks: no experience
- Airflow: no experience
- Fivetran: no experience
- PySpark / pandas / numpy at production scale: no experience (Python is beginner level)
- Cloud infrastructure engineering (AWS, GCP, Azure hands-on build): no experience — Azure scope is process/requirements-side only

- For cloud-native DE roles: be precise about Azure scope (requirements and process design, not infrastructure engineering) — overclaiming infrastructure ownership will be exposed in technical screening
- Read JD qualification tiers carefully: "experience building and monitoring data pipelines with tools such as Airflow, dbt, or Fivetran" under Required means at least one tool is expected, not optional


### Freelance / AI Training
- Alignerr AI training roles: Lawrence's healthcare governance depth (QHR secure messaging, multi-jurisdictional compliance, AHS hospital background) is an unusually strong fit for domain expert evaluation roles
- For freelance/AI training gigs: skip full resume tailoring; a light governance-focused pitch or profile is sufficient
- HIPAA vs Canadian privacy frameworks (PIPEDA): not a blocker — evaluate using Canadian equivalents and note the parallel; AI training evaluators spot framework errors regardless of jurisdiction

### Compensation Outliers
- US remote roles with $120–140K USD salary (~$165–193K CAD) are high-value targets if domain gap can be closed

---

## Resume Feedback
<!-- Updated when the human gives feedback on a generated resume (tone, format, content) -->

- **Always retain the promotion to Lead Data Analyst bullet.** Even when trimming bullets for space or relevance, do not cut the point about Lawrence being promoted to Lead Data Analyst — it anchors the work history timeline and clarifies the progression of his seniority at that employer.

## Cover Letter Feedback
<!-- Updated when the human gives feedback on a generated cover letter -->

## Interview Insights
<!-- Updated after /mock-interview: weak areas, strong stories, patterns to fix -->

---

## Filter Overrides
<!-- Logged when /job-match is run on a job that scored below 14 on the Quick Score. -->
<!-- Format: Date | Company | Role | QS | Reason | Outcome -->

| Date | Company | Role | QS | Reason given | Outcome |
|------|---------|------|----|--------------|---------|
| 2026-05-25 | CPKC | Analyst Engineering Operations | 13/20 | Human override | 58 — Stretch |
| 2026-04-26 | Deloitte | Data Quality Manager (Master Data) | 13/20 | Human override | 75/100 — Good fit; Informatica MDM gap is preferred-only; strong governance/seniority match |
| 2026-04-27 | Anatta Design | Business Analyst | 10/20 | Human override | 64/100 — Stretch; Shopify zero experience is the blocker; comp is strong ($120–140K USD) |
| 2026-04-27 | Deloitte | Senior Analyst - Technical, Clean Economy | 11/20 | Human override | 47/100 — Significant mismatch; clean energy engineering background is a hard requirement |
| 2026-04-27 | Deloitte | Senior Manager Data Analytics and AI/ML Products | 11/20 | Human override | 58/100 — Stretch; seniority gap 1.5–2 levels; Snowflake/Databricks/Vertex AI absent; no AI/ML product ownership |
| 2026-04-27 | Deloitte | Architect Manager (2-yr Fixed Term) | 11/20 | Human requested job-match | 54/100 — Significant mismatch; cloud/AI architect domain gap; not recommended |
| 2026-05-06 | TELUS Health | Senior QA Analyst – Data & Test Case Preparation | 12/20 | Human requested job-match | 42/100 — Significant mismatch; SQA core-function gap is a hard blocker; pension domain unfamiliar; not recommended |
| 2026-05-19 | Government of Alberta (CTS) | Application Analyst — Intermediate | 10/20 | Human requested job-match | 57/100 — Stretch; 100% in-person Edmonton is hard constraint; ServiceNow 4-yr gap; strong BA/governance/data platform fit |

---

## Compensation Research
<!-- Updated after /job-match +comp runs. Cache expires 90 days from Last updated date. Check here before running salary research on a similar role + location. -->
<!-- Format: [Role title] — [Geography/context]: [Min CAD] - [Max CAD] | Sources: [...] | Last updated: [YYYY-MM-DD] -->
CRM Business Analyst / Salesforce BA — Canada (nonprofit context): $78,000 - $115,000 CAD | Sources: talent.com, Glassdoor, PayScale | Last updated: 2026-06-11
Note: CCS posted $65K–$75K (Salary Band 5) — below market; nonprofit discount applies; anchor at $72K–$75K (top of band) when salary expectations required
Associate Director / Director, Data Analytics — Canada (national orgs, health sector): CA$125,000–CA$175,000; posted range CBS: CA$132,300–CA$155,600; CBS comp rated 3.9/5 (average), modest annual increases; target top of band CA$155,600, floor CA$145,000; nonprofit total comp (pension/benefits) typically above-market | Sources: Glassdoor, Indeed CA, PayScale | Last updated: 2026-05-29
Business Analyst (mid-level, healthcare/health IT, permanent) — Calgary, AB / Canada: CA$79,000–CA$105,000 (Calgary BA avg CA$79K, senior BA Calgary avg CA$97K, healthcare BA national avg CA$97K, IT BA Canada avg CA$87.5K); TELUS comp rated 3.3/5 avg; target anchor CA$90,000–CA$100,000 for 7yr healthcare domain profile | Sources: Glassdoor, Indeed CA, Talent.com | Last updated: 2026-05-29
Operations/Engineering Analyst — Calgary, AB (railway/CPKC): CA$63,000–CA$102,000 (25th–75th pct Glassdoor); ops analyst broad market CA$54K–CA$85K; CPKC comp rated 3.5/5, below-avg overall (2.6/5); intra-role pay gap risk; floor risk for this role at junior posting level | Sources: Glassdoor, Indeed CA | Last updated: 2026-05-25
Data Steward — Canada Remote / Alberta: CA$62,714–CA$98,673 (25th–75th pct); national avg CA$78,597; Alberta avg CA$91,882; senior level (8+ yrs) CA$127K; target for Lawrence CA$90,000–CA$100,000 given 7 yrs experience; Sentrex likely budgeting CA$75K–CA$90K for 3–5 yr baseline | Sources: Glassdoor CA, ZipRecruiter, SalaryExpert | Last updated: 2026-05-06

Senior Data Analytics Engineer — Canada: CA$97,000–CA$155,000 (avg ~CA$119K); TELUS Digital data engineers rate comp 1.8/5 (47% below peers); negotiate $115K–$125K for 7yr profile; floor $105K | Sources: PayScale, Glassdoor, Levels.fyi | Last updated: 2026-06-01
Senior Data Analyst — Calgary, AB / Canada: CA$79,683 – CA$118,295 (avg CA$96,470) | Sources: Glassdoor (April 2026) | Last updated: 2026-04-28
Business Data Analyst (Senior/7yr) — Canada Remote contract: $85,000–$116,000 CAD annual equivalent (~$41–$56/hr) | Sources: PayScale, Glassdoor, Indeed, talent.com | Last updated: 2026-05-24
Senior Client Analytics Partner / Ad Tech Analytics (Senior IC) — Canada Remote: CA$90,000–CA$130,000; negotiation anchor CA$110,000–CA$120,000; StackAdapt comp rated average (3.0–3.6/5 Glassdoor); Ontario benchmark rate referenced but not disclosed in JD | Sources: Glassdoor, Indeed CA, talent.com | Last updated: 2026-05-25
Senior Data Integration Specialist / Senior Data Engineer — Calgary, AB: CA$120,000 – CA$160,000 (national); Calgary slightly below national avg; posted mid-point ~CA$132,500 | Sources: Glassdoor, Levels.fyi | Last updated: 2026-04-28
Manager Business Insights / Analytics Manager — Canada Remote: CA$94,000–CA$149,000 (25th–75th pct; Glassdoor avg CA$117,767; Indeed avg CA$100,038; PayScale range CA$82K–CA$126K); negotiation anchor CA$115,000–CA$125,000 for 7yr profile with team leadership; Kensington comp reputation unknown (no Glassdoor data) | Sources: Glassdoor CA, Indeed CA, PayScale | Last updated: 2026-06-03
Data Analyst (generalist, non-profit) — Calgary, AB: CA$59,238 – CA$94,316 market; non-profit likely CA$65,000–CA$85,000; seniority anchor CA$80,000–CA$88,000 | Sources: Glassdoor, PayScale, Indeed, Levels.fyi | Last updated: 2026-04-28
Business Analyst (eCommerce/Shopify agency) — US Remote: USD$83,000 – USD$137,000 (25th–75th pct); listed CA$165,000–CA$193,000 at 1.38x rate | Sources: Glassdoor, Levels.fyi | Last updated: 2026-04-28
Data Engineer — Calgary, AB / Canada: CA$98,000–CA$143,000 (Glassdoor Calgary 25th–75th pct); top earners CA$166,500; Levels.fyi Canada median CA$120,350; Orennia SWE median CA$122,171; Robert Half Calgary specialist band ~CA$110,000–CA$140,000; floor CA$105,000; target anchor CA$120,000–CA$125,000; stretch CA$130,000–CA$135,000 | Sources: Glassdoor, Levels.fyi, ZipRecruiter, Robert Half, SalaryExpert | Last updated: 2026-05-20
Senior Contract Data Engineer — Canada Remote (NB govt): CA$110–CA$120/hr listed; market CA$60–CA$120/hr; full-time equivalent CA$108,000–CA$165,000 | Sources: Glassdoor CA, ZipRecruiter | Last updated: 2026-04-28
Senior Contract Data Engineer — Alberta public sector (GoA): CA$70–CA$85/hr target; derived from GoA FTE grid CA$82K–CA$108K x 1.4x contractor premium / 1,960 hrs; 4 of 9 must-haves partial reduces ceiling; recommended anchor CA$75/hr | Sources: Alberta Public Service pay grid (2025), Talent.com, Glassdoor Canada | Last updated: 2026-05-04
Deloitte Senior Analyst — Canada (Calgary / national): CA$69,000–CA$114,000 posted; market CA$83,000–CA$120,000; median ~CA$85,693; target CA$95,000–CA$105,000 | Sources: Glassdoor (1,575–1,861 salaries), Levels.fyi | Last updated: 2026-04-28
Deloitte Senior Consultant — Canada: CA$72,000–CA$138,000 posted; market CA$83,000–CA$120,000; target CA$95,000–CA$105,000; comp rated avg 3.2/5 | Sources: Glassdoor (1,861 salaries, March 2026), Levels.fyi | Last updated: 2026-04-28
Deloitte Manager / Technology Manager — Canada: CA$85,000–CA$156,000 posted; market base ~CA$125,000; total comp CA$113,000–CA$140,000; target CA$120,000–CA$130,000 | Sources: Glassdoor, Levels.fyi | Last updated: 2026-04-28
Deloitte Tech Lead / Technical Lead — Canada: CA$105,000–CA$175,000 posted; market CA$90,000–CA$142,000 (avg ~CA$112,000); target CA$120,000–CA$135,000 | Sources: Glassdoor (Feb 2026), ZipRecruiter (Dec 2025) | Last updated: 2026-04-28
Deloitte Senior Manager (Data/AI) — Canada: CA$104,000–CA$215,000 posted + bonus; market base CA$108,000–CA$166,000 (median ~CA$133,000); total comp CA$147,000–CA$186,000 | Sources: Glassdoor | Last updated: 2026-04-28
Data Quality Manager / Data Governance Manager — Canada: CA$74,000–CA$123,000 market (median ~CA$88,000); Deloitte posted CA$85,000–CA$156,000; target CA$110,000–CA$125,000 | Sources: Glassdoor | Last updated: 2026-04-28
IT Analyst II (Health/Government, AUPE grid) — Alberta: CA$42.12–CA$56.86/hr (~CA$85,000–CA$115,000); union grid, no negotiation | Sources: JD / AUPE GSS wage grid | Last updated: 2026-04-28
Senior IT Business Analyst / Senior Healthcare BA — Edmonton, AB (contract, government health): CA$75–CA$90/hr target; Edmonton FTE avg CA$97,705 x 1.4x contractor premium / 1,960 hrs = ~CA$70/hr base; GoA Senior Business Consultant ceiling CA$92.47/hr; healthcare specialization and HIA context support upper end; recommended anchor CA$80–CA$85/hr (~CA$156,800–CA$166,600 annualized) | Sources: PayScale (Edmonton BA 2026), PayScale (GoA salary data), Indeed CA | Last updated: 2026-05-05
## Scout-Link Execution Notes

### Right Panel Render Timing (2026-05-26)
**Issue:** `document.body.innerText` search for "About the job" returned `null` immediately after clicking a LinkedIn job card, even though the JD was present and extractable seconds later.
**Root cause:** LinkedIn's right panel renders asynchronously. Collapsing the "… more" click and body text extraction into the same `javascript_tool` call (or calling extraction immediately after the card click) doesn't allow enough time for the JD content to appear in the DOM.
**Fix:** Always use separate `javascript_tool` calls with natural round-trip latency between: (1) click card → (2) check/click "… more" → (3) extract body text. The inter-call latency (~1–2s) is sufficient for the right panel to render. Never collapse steps 2 and 3 into the same call immediately after step 1.

## Scout Execution Notes

### ATB Financial — permanently blocked (2026-06-10)
ATB Financial blocks Claude automation entirely — the `atb.com` domain is restricted and cannot be accessed via Chrome MCP or any automated tool. **Never attempt to automate ATB Financial.** Browse manually at https://careers.atb.com/careers/data_ai_analytics.

### Close-date handling — timezone (2026-06-10)
Always resolve close dates against **Mountain Time (MT)** before deciding whether a posting is expired. A posting with Apply By = today's MT date is still live — treat it as normal, log as `pending` with `⚠️ Closes today — urgent apply` in Notes, and surface with 🔥 in the ranked table. **Never skip a listing because its close date matches today.** Only skip if the close date is strictly in the past (MT). Applies to all scout entry points.

**Why:** On 2026-06-10, Business Technology Analyst (Apply By Jun 10 MT) and Business Analyst (Apply By Jun 11 MT) at City of Calgary were both skipped as "expired" when they were still live. The Business Technology Analyst was recoverable same session; the error was caught before any permanent loss.

## Resume Skills Formatting

### Health IT Skills — EMR/EHR grouping (2026-06-05)
Write EMR and EHR together as "EMR/EHR" in the Health IT skills section. Do not list them as separate comma-separated items.
