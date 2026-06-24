/**
 * click_show_all_preferences.js
 *
 * What it does:
 *   On the LinkedIn Jobs home page, locates the "Jobs based on your preferences"
 *   section and clicks its "Show all" button/link to navigate to the full results list.
 *
 * Called from:
 *   scout-link SKILL.md — Step 1 (preferences mode): the default mode for scout-link.
 *   This script is always used (the top-applicant variant is a fallback/alternative mode).
 *
 * Strategy:
 *   Find the <h2> heading that contains "your preferences", then walk up the DOM
 *   tree (up to 10 ancestor levels) until we find a "Show all" clickable element
 *   scoped to that section. This avoids accidentally clicking a "Show all" from
 *   a different section on the same page.
 *
 * Returns (as the last evaluated expression):
 *   'clicked'    — the Show all element was found and clicked
 *   'not found'  — no matching heading or button was found
 */

// Find the section heading that identifies the "your preferences" job list.
const preferencesHeading = Array.from(document.querySelectorAll('h2'))
  .find(el => el.textContent.trim().includes('your preferences'));

// Track whether we successfully clicked something.
let clickResult = null;

if (preferencesHeading) {
  // Walk up the DOM from the heading, checking each ancestor for a "Show all" element.
  // LinkedIn wraps headings and their controls in a shared parent container, so the
  // "Show all" button may be several levels up from the <h2>.
  let currentElement = preferencesHeading;

  for (let ancestorLevel = 0; ancestorLevel < 10; ancestorLevel++) {
    currentElement = currentElement.parentElement;

    // Stop early if we've walked past the top of the DOM tree.
    if (!currentElement) break;

    // Look for any clickable element with "Show all" text within this ancestor.
    const showAllButton = Array.from(currentElement.querySelectorAll('a, button, div[role="button"]'))
      .find(el => el.textContent.trim() === 'Show all' || el.textContent.trim().startsWith('Show all'));

    if (showAllButton) {
      showAllButton.click();
      clickResult = 'clicked';
      break; // Stop walking up once we've found and clicked the target.
    }
  }
}

// Return the result: 'clicked' if successful, or 'not found' if nothing matched.
clickResult || 'not found';
