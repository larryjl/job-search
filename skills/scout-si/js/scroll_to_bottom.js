/**
 * scroll_to_bottom.js
 *
 * What it does:
 *   Scrolls the page to the very bottom, triggering SI Systems' infinite scroll
 *   to load additional job cards that aren't rendered on initial page load.
 *
 * Called from:
 *   scout-si SKILL.md — Phase 2: run before extract_card_list.js and before
 *   starting card-by-card review. Repeat this call (and re-run extract_card_list.js)
 *   until the number of DETAILS buttons stops increasing between calls, which means
 *   all available cards have loaded.
 *
 * Returns:
 *   Nothing — triggers a scroll action only.
 */

// Scroll to the absolute bottom of the document.
// document.body.scrollHeight is the full height of all page content including
// content below the visible viewport.
window.scrollTo(0, document.body.scrollHeight);
