# Adzuna Queue Drain — Parent Orchestrator

Trigger: `/scout-adzuna drain` or "drain the adzuna queue"

Spawns sequential sub-agents to process the Adzuna queue 50 items at a time until the queue is empty or the session usage cap is hit.

---

## Step 1 — Pre-flight

Read `raw-results-queue.json` → count unprocessed items.

```
🚀 Adzuna queue drain starting.
Unprocessed items: [N]
Estimated batches: [ceil(N/50)]
```

If unprocessed = 0: output `✅ Queue is already empty.` and stop.

---

## Step 2 — Spawn Sub-Agent Loop

Read the full contents of `skills/scout-adzuna/adzuna-queue-batch.md` — this is the sub-agent prompt. Spawn one sub-agent at a time using that prompt verbatim as the agent's task.

Wait for the sub-agent to return its status line:
```
BATCH DONE. Processed: [N] | Passed threshold: [N] | Queue remaining: [N] | Title-skipped: [Company — Title, ...]
```

Log the result inline:
```
✅ Batch [#]: [status line]
```

Accumulate the `Title-skipped` entries from all batches into a session-level list (deduplicated by Company — Title).

Then:
- If `QUEUE EMPTY` in status → stop, output final summary
- If context/usage cap error → stop, output final summary with note
- Otherwise → spawn next sub-agent immediately

---

## Step 3 — Final Summary

```
─────────────────────────────────────────
🏁 Queue drain complete
Batches run: [N]
Total processed: [N]
Total passed threshold (≥6/10): [N]
Queue remaining: [N]
─────────────────────────────────────────
```

If any title-skipped entries were accumulated across batches, append immediately after the block:

```
🚫 Skipped by title ([N] total):
  • [Company] — [Title]
  • [Company] — [Title]
  ...
```

If stopped early due to cap: append `⚠️ Stopped early — session cap reached. Re-run /scout-adzuna drain to continue.`

---

## Step 3b — Ranked Table + Post-table Summary

Read `job-outputs/jobs.csv`. Select rows where:
- `Source` = `scout-adzuna`
- `Date` = today (YYYY-MM-DD)
- `Filter_Score` ≥ 6 (or `Status` = `pending` with a blank Filter_Score — these are ⚠️ Unverified rows)

Output the header block per `skills/scout-adzuna/SKILL.md` Step 9, then the ranked table:

```
─────────────────────────────────────────
🔍 Job Scout Results
Mode: Adzuna
Searches: data analyst | data engineer | analytics engineer | analytics manager | business analyst | data integration | Locations: Calgary + Canada remote
Live listings: [N] | Location-excluded: [N] | Dead dropped: [N]
Ranked by: Match Score (Filter Score where Match Score unavailable)
⚠️ Source: Adzuna API — postings not from tracked company boards.
─────────────────────────────────────────
```

| # | Company | Role | Filter Score | Match Score | Location | URL |
|---|---------|------|--------------|-------------|----------|-----|
| 1 | [Company] | [Title] | 🟢 9/10 | 76 | [City, Province / Remote / Hybrid — confirmed only] | [link] |

**Sorting:** Match Score descending; ties broken by Filter Score descending; then location preference (Calgary first, Remote second, On-site last). ⚠️ Unverified rows appear at the bottom regardless of score.

**Location rules:** Show city/province from the JD. Include work model (Remote / Hybrid / On-site) **only if explicitly stated in the JD**. Do not infer from city name alone. If unconfirmed, show city/province only (e.g. "Fredericton, NB" — not "Fredericton, NB (remote unconfirmed)").

**Score colour (Filter Score):** 🟢 9–10 | 🟡 7–8 | 🟠 6 | 🔴 below 6

Then output the post-table summary per `skills/scout-adzuna/SKILL.md` Step 10:

```
─────────────────────────────────────────
📊 Scout Summary

Top pick:     [Job Title] at [Company] — Filter [X]/10 | Match [Y]/100
              [One sentence: why strongest match]

Worth a look: [Job Title] at [Company] — Filter [X]/10 | Match [Y]/100
              [One sentence: what makes it interesting]

Skip:         [N] roles scored below 6/10

─────────────────────────────────────────
```

If no rows qualify (all below threshold or queue was already empty): output `✅ No new qualifying listings this run.` and stop.

---

## Rules

- Never process items directly in the parent — all processing happens in sub-agents
- Never run sub-agents in parallel — always wait for one to complete before spawning the next
- The queue file is the source of truth — if a sub-agent fails silently, the next sub-agent picks up correctly because items were marked processed before Chrome work began
- If a sub-agent returns an unexpected result or errors, log it and stop: `⚠️ Sub-agent error — stopping drain. Re-run to continue.`
