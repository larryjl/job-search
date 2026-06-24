/**
 * click_details_by_index.js
 *
 * What it does:
 *   Clicks the DETAILS button for a specific job card on the SI Systems search
 *   results page, which opens the inline job description panel for that card.
 *
 * Called from:
 *   scout-si SKILL.md — Phase 2 Step B (Method 1, preferred): click each card's
 *   DETAILS button one at a time to load the JD panel before reading it.
 *   If this causes an unexpected redirect, fall back to Method 2 (find + left_click).
 *
 * Before running:
 *   Replace N with the zero-based index of the card to open.
 *   Example: N=0 opens the first card, N=1 opens the second, etc.
 *
 * Returns:
 *   Nothing — triggers a click that loads the JD panel inline.
 */

// Collect all DETAILS buttons on the page (one per job card).
// Then click the one at the target index N.
// N must be replaced with a number (e.g. 0, 1, 2) before running.
Array.from(document.querySelectorAll('button'))
  .filter(button => button.textContent.trim() === 'DETAILS')[N]
  .click();
