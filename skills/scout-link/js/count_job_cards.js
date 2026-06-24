/**
 * count_job_cards.js
 *
 * What it does:
 *   Counts the number of job cards currently visible in the main results panel.
 *   Used to know how many cards to iterate over before starting the harvest loop.
 *
 * Called from:
 *   scout-link SKILL.md — Step 2a: run after scroll_containers.js to confirm
 *   how many cards loaded before starting the click-walk in harvest_job_ids.js.
 *
 * Background — post-RSC-migration card selector:
 *   After LinkedIn's React Server Components (RSC) migration, job cards no longer
 *   have stable CSS class names. Instead, each card is a `div[role="button"]`
 *   containing multi-line text (title, company, location, etc.).
 *   We identify cards by filtering on text length and line count to avoid matching
 *   other generic `div[role="button"]` elements on the page (e.g. filter pills).
 *
 * Returns (as the last evaluated expression):
 *   Integer — the number of job cards found.
 */

// Scope the search to the <main> element to avoid picking up sidebar or nav buttons.
const mainPanel = document.querySelector('main');

// Count elements that look like job cards:
//   - Must be a div with role="button" (LinkedIn's post-RSC card structure)
//   - innerText between 25 and 400 chars (short = UI button, long = article/ad)
//   - At least 2 non-empty lines (cards always have title + company at minimum)
const cardCount = Array.from(mainPanel.querySelectorAll('div[role="button"]'))
  .filter(el => {
    const text = el.innerText?.trim() || '';
    return text.length > 25 && text.length < 400 && text.split('\n').length >= 2;
  })
  .length;

cardCount;
