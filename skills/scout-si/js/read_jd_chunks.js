/**
 * read_jd_chunks.js
 *
 * What it does:
 *   Reads the full job description text from the SI Systems JD panel in chunks
 *   to avoid browser tool output truncation. Anchors on the "Job ID" field as a
 *   reliable start point within the page's full body text.
 *
 * Called from:
 *   scout-si SKILL.md — Phase 2 Step B: run after clicking DETAILS and waiting
 *   2 seconds for the JD panel to fully load.
 *
 * How to use:
 *   Run each of the three extraction lines separately (as individual javascript_tool
 *   calls) and combine the returned strings to get the complete JD text. The chunks
 *   are contiguous (not overlapping) — boundaries are placed at fixed offsets from
 *   the "Job ID" position so no content is duplicated or skipped between chunks.
 *
 * Chunk boundaries (relative to the "Job ID" position in body text):
 *   Chunk 0 (header):  from 100 chars before "Job ID" → +500 chars  (Job ID + title area)
 *   Chunk 1 (first):   from +500 → +2500                             (main JD body)
 *   Chunk 2 (second):  from +2500 → +4500                            (extended JD if long)
 *
 * Returns (per line, evaluated separately):
 *   String — the text slice for that chunk. Empty if the JD is shorter than that range.
 */

// `innerText` returns only the visible rendered text (what the user sees on screen),
// while `textContent` also includes hidden elements. Since we want the rendered JD
// text, innerText is the correct choice here.
const fullPageText = document.body.innerText;

// Find where "Job ID" appears — this is a stable landmark in the SI Systems JD panel.
// Silent failure mode: if 'Job ID' is not found, indexOf returns -1, and
// Math.max(0, -1 - 100) clamps to 0 — so the script returns the top of the page
// instead of the JD area. Callers should verify the returned text contains real JD content.
const jobIdPosition = fullPageText.indexOf('Job ID');

// Chunk 0: header section (job title, ID, metadata)
// Guard against a negative index if 'Job ID' appears near the top of the page —
// `substring` with a negative start would silently clamp to 0 in JavaScript,
// but the explicit Math.max(0, ...) makes the intent clear.
fullPageText.substring(Math.max(0, jobIdPosition - 100), jobIdPosition + 500);

// Chunk 1: first body section (responsibilities, requirements)
fullPageText.substring(jobIdPosition + 500, jobIdPosition + 2500);

// Chunk 2: extended body (additional requirements, application info)
fullPageText.substring(jobIdPosition + 2500, jobIdPosition + 4500);
