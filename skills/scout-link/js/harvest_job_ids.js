/**
 * harvest_job_ids.js
 *
 * What it does:
 *   Iterates over every job card in the LinkedIn search results panel, clicks each
 *   one, and reads the resulting `currentJobId` from the URL to collect all job IDs
 *   on the current page. This is the "click-walk" strategy adopted after LinkedIn's
 *   RSC migration removed stable data attributes from card elements.
 *
 * Called from:
 *   scout-link SKILL.md — Step 2b: run after scroll_containers.js and count_job_cards.js.
 *   After this script completes (it's async), run a second call:
 *     JSON.stringify(window.__cardWalk.results)
 *   to read the full per-card results array.
 *
 * How it works:
 *   - Clicking a card updates the URL's `currentJobId` parameter asynchronously
 *     (typically within 70–175ms, based on measured timing).
 *   - We poll the URL in tight 20ms intervals (up to 1 second) to catch that change.
 *   - The card list is re-queried on each iteration because LinkedIn may re-render
 *     the list when a card is selected (virtual DOM diffing).
 *   - Results are stored on window.__cardWalk so they survive the async closure.
 *
 * Returns (as the last evaluated expression — run synchronously after the async block):
 *   JSON string with summary fields:
 *     total      — number of cards found on the page
 *     uniqueIds  — number of distinct job IDs collected
 *     nulls      — number of cards where no ID could be extracted
 *
 * Full results (run separately after this completes):
 *   JSON.stringify(window.__cardWalk.results)
 *   Each entry: { i, title, company, id, dup }
 *     i       — zero-based card index
 *     title   — first line of card text (job title)
 *     company — second line of card text (company name)
 *     id      — the currentJobId string, or null if extraction failed
 *     dup     — true if this id was already seen earlier on the page
 */

/**
 * IIFE (Immediately Invoked Function Expression): a function defined and called
 * in the same expression. `async` is required so we can use `await` inside.
 * Results are stored on `window.__cardWalk` rather than returned because the
 * browser javascript_tool cannot `await` a top-level async expression — storing
 * on `window` lets the caller read the result after the async work completes.
 */
await (async () => {
  const mainPanel = document.querySelector('main');

  // Helper: re-query cards on each call because LinkedIn may re-render the list.
  // Uses the same filter logic as count_job_cards.js.
  const getJobCards = () =>
    Array.from(mainPanel.querySelectorAll('div[role="button"]'))
      .filter(el => {
        const text = el.innerText?.trim() || '';
        // > 25 chars: excludes UI buttons and header labels that are too short to be cards.
        // < 400 chars: excludes non-card DOM elements (e.g. whole panels) that are too long.
        // >= 2 lines: ensures the element has a title + at least one other line
        //             (actual job cards always have at least title + company).
        return text.length > 25 && text.length < 400 && text.split('\n').length >= 2;
      });

  // Helper: read the currentJobId from the URL at this exact moment.
  // new URL(...) is used over string splitting because the URL API parses query
  // strings reliably without breaking on edge cases like multiple params or encoding.
  const getCurrentJobId = () => new URL(location.href).searchParams.get('currentJobId');

  const results = [];
  const seenIds = new Set(); // Track IDs we've already collected (for dup detection).
  const totalCards = getJobCards().length;

  for (let cardIndex = 0; cardIndex < totalCards; cardIndex++) {
    // Re-query the cards on each iteration — the list may have re-rendered.
    const card = getJobCards()[cardIndex];

    if (!card) {
      // Card disappeared (e.g. list re-rendered with fewer items); record the gap.
      results.push({ i: cardIndex, err: 'no-card' });
      continue;
    }

    // Extract title and company from the card's text lines for identification.
    const textLines = card.innerText
      .split('\n')
      .map(line => line.trim())
      .filter(Boolean);
    const title = (textLines[0] || '').slice(0, 80);
    const company = (textLines[1] || '').slice(0, 80);

    // Record the ID that's in the URL before we click, so we can detect the change.
    const idBeforeClick = getCurrentJobId();
    let extractedId = null;

    // Try clicking up to 3 times — occasionally the first click doesn't register.
    for (let attempt = 0; attempt < 3 && !extractedId; attempt++) {
      // Scroll the card into view so it's clickable (not off-screen).
      card.scrollIntoView({ block: 'center' });
      await new Promise(resolve => setTimeout(resolve, 30)); // Brief pause for scroll.
      card.click();

      // Poll the URL every 20ms for up to 1 second (50 polls × 20ms) waiting for
      // LinkedIn to update currentJobId in response to the click.
      for (let pollCount = 0; pollCount < 50; pollCount++) {
        await new Promise(resolve => setTimeout(resolve, 20));
        const currentId = getCurrentJobId();
        if (currentId && currentId !== idBeforeClick) {
          extractedId = currentId;
          break; // ID changed — we got it.
        }
      }

      // Special case: the very first card on the page may already be selected
      // before we click it, so idBeforeClick === id and the change never fires.
      if (!extractedId && attempt === 0 && cardIndex === 0) {
        extractedId = getCurrentJobId();
      }
    }

    // Final fallback: read whatever currentJobId is in the URL now.
    if (!extractedId) extractedId = getCurrentJobId();

    results.push({
      i: cardIndex,
      title,
      company,
      id: extractedId,
      dup: seenIds.has(extractedId), // Flag if we've seen this ID before on this page.
    });

    if (extractedId) seenIds.add(extractedId);
  }

  // Store results globally so they're accessible after this async IIFE completes.
  window.__cardWalk = {
    hidden: document.hidden,          // Was the tab hidden during the walk? (affects rendering)
    total: totalCards,
    collected: results.length,
    uniqueIds: seenIds.size,
    nulls: results.filter(entry => !entry.id).length,
    results,
  };
})();

// By this point the `await` inside the IIFE has fully resolved, so
// window.__cardWalk is guaranteed to be populated before these lines run.
// Return a quick summary immediately — the full results are in window.__cardWalk.results.
JSON.stringify({
  total: window.__cardWalk.total,
  uniqueIds: window.__cardWalk.uniqueIds,
  nulls: window.__cardWalk.nulls,
});
