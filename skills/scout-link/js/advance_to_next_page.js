/**
 * advance_to_next_page.js
 *
 * What it does:
 *   Advances the LinkedIn job search results to the next page.
 *   LinkedIn paginates results in increments of 25 via the `start` URL parameter
 *   (e.g. start=0 = page 1, start=25 = page 2, start=50 = page 3, etc.).
 *
 * Called from:
 *   scout-link SKILL.md — Step 4 (all-duplicate check): when every card on the
 *   current page has already been seen or skipped, this script moves to the next page
 *   instead of processing it further.
 *
 * Strategy:
 *   1. Try clicking a visible "Next" button if one exists in the DOM.
 *   2. Otherwise, bump the `start` URL parameter by 25 and navigate directly.
 *
 * Returns (as the last evaluated expression):
 *   'clicked-next'    — a Next button was found and clicked
 *   'offset-advanced' — URL was modified and navigation started
 */

// Parse the current page URL so we can read and modify the `start` parameter.
const currentUrl = new URL(window.location.href);

// Read the current `start` offset; default to 0 if the parameter is missing.
const currentOffset = parseInt(currentUrl.searchParams.get('start') || '0', 10);

// Build the next-page URL by adding 25 to the current offset.
currentUrl.searchParams.set('start', currentOffset + 25);

// Check for a visible "Next" button in the page (LinkedIn sometimes renders one).
const nextButton = Array.from(document.querySelectorAll('a, button'))
  .find(el => el.textContent.trim() === 'Next');

if (nextButton) {
  // Prefer clicking the native Next button — it preserves any SPA routing LinkedIn uses.
  nextButton.click();
  'clicked-next';
} else {
  // Fall back to a direct URL navigation with the bumped offset.
  window.location.href = currentUrl.toString();
  'offset-advanced';
}
