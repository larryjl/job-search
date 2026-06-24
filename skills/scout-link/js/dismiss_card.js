/**
 * dismiss_card.js
 *
 * What it does:
 *   Dismisses a single job card from LinkedIn's recommendations feed by clicking
 *   its dismiss (X) button. Verifies that both the job title AND company match
 *   within the same DOM ancestor before clicking, to prevent accidentally dismissing
 *   a different card with a similar title.
 *
 * Called from:
 *   scout-link SKILL.md — Step 9: after scoring a card as low-match or already-seen,
 *   dismiss it from the feed so it doesn't reappear in future scout runs.
 *
 * Before running:
 *   Replace the two [Job Title] placeholders and the [Company] placeholder with the
 *   exact strings from Step 2's harvest output (case-sensitive).
 *   Example:
 *     'button[aria-label*="Dismiss Senior Data Analyst"]'
 *     el.textContent.includes('Senior Data Analyst') && el.textContent.includes('Acme Corp')
 *
 * Note on aria-label matching:
 *   LinkedIn appends trailing spaces to aria-labels, so we use *= (contains) instead
 *   of = (exact match) to reliably find the button regardless of trailing whitespace.
 *
 * Returns (as the last evaluated expression):
 *   'dismissed'  — the button was found with matching context and clicked
 *   'not found'  — no button matched both title and company within 12 ancestor levels
 */

// Select all dismiss buttons whose aria-label contains the target job title.
// (There may be multiple if the title appears in more than one card on screen.)
const dismissButtons = Array.from(
  document.querySelectorAll('button[aria-label*="Dismiss [Job Title]"]')
);

let dismissResult = 'not found';

for (const button of dismissButtons) {
  // Walk up the DOM from this button to find a shared ancestor that contains
  // both the job title AND the company name. This confirms we have the right card.
  let currentElement = button;

  for (let ancestorLevel = 0; ancestorLevel < 12; ancestorLevel++) {
    currentElement = currentElement.parentElement;

    // Stop walking if we've reached the top of the tree.
    if (!currentElement) break;

    const ancestorText = currentElement.textContent;

    // Only click if BOTH title and company are present in this ancestor block.
    if (
      ancestorText.includes('[Job Title]') &&
      ancestorText.includes('[Company]')
    ) {
      button.click();
      dismissResult = 'dismissed';
      break;
    }
  }

  // Stop checking other buttons once we've successfully dismissed one.
  if (dismissResult === 'dismissed') break;
}

dismissResult;
