/**
 * navigate_to_offset.js
 *
 * What it does:
 *   Navigates the LinkedIn job search results to a specific page by injecting
 *   a `start` offset into the current URL. LinkedIn paginates in batches of 25,
 *   so offset = (pageNumber - 1) * 25.
 *
 * Called from:
 *   scout-link SKILL.md — Step 1 (page offset): use this to jump directly to a
 *   specific page of results, e.g. to resume a scout run from a known page number.
 *
 * Before running:
 *   Replace [OFFSET] with the desired numeric offset.
 *   Examples:
 *     Page 1 → start=0    (or omit the parameter)
 *     Page 2 → start=25
 *     Page 3 → start=50
 *
 * Returns:
 *   Nothing — triggers a page navigation immediately.
 */

// Parse the current URL so we can modify just the `start` parameter.
const pageUrl = new URL(window.location.href);

// Set the offset. [OFFSET] must be replaced with a number before running.
pageUrl.searchParams.set('start', [OFFSET]);

// Navigate to the new URL. This is a hard navigation (not SPA routing),
// which is fine because LinkedIn reloads the full search results page on offset change.
window.location.href = pageUrl.toString();
