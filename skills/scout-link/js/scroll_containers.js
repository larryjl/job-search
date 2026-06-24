/**
 * scroll_containers.js
 *
 * What it does:
 *   Scrolls every overflow container on the page to the bottom, waits 1 second,
 *   then scrolls them all back to the top. This forces LinkedIn to render any
 *   lazily-loaded job cards that only appear when scrolled into view.
 *
 * Called from:
 *   scout-link SKILL.md — Step 2a: run before count_job_cards.js and
 *   harvest_job_ids.js to ensure all cards are in the DOM before iterating.
 *
 * Why this is needed:
 *   LinkedIn virtualizes its job list — cards outside the visible viewport may not
 *   be in the DOM yet. Scrolling to the bottom triggers rendering of those cards.
 *   Scrolling back to the top afterward ensures harvest_job_ids.js starts from card #1.
 *
 * Returns (as the last evaluated expression):
 *   'scrolled' — always, once the scroll and wait are complete.
 */

// Find all elements that have scrollable overflow content.
// We detect these by comparing scrollHeight (total content height) to
// clientHeight (visible height) — a difference of >200px indicates real overflow.
const scrollableContainers = Array.from(document.querySelectorAll('div, ul'))
  .filter(el => el.scrollHeight > el.clientHeight + 200);

// Scroll every container to its bottom to trigger lazy rendering.
scrollableContainers.forEach(container => {
  container.scrollTop = container.scrollHeight;
});

// Wait 1 second for LinkedIn's virtual list to render the newly visible cards.
await new Promise(resolve => setTimeout(resolve, 1000));

// Scroll everything back to the top so the card walk starts from the beginning.
scrollableContainers.forEach(container => {
  container.scrollTop = 0;
});

'scrolled';
