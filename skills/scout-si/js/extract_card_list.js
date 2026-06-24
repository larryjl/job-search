/**
 * extract_card_list.js
 *
 * What it does:
 *   Extracts a summary list of all job cards currently loaded on the SI Systems
 *   search results page. Returns the index, posted date, and title for each card
 *   in a plain-text format (one card per line) for quick review.
 *
 * Called from:
 *   scout-si SKILL.md — Phase 2: run after all cards have loaded via infinite scroll
 *   (scroll_to_bottom.js). Use this output to plan which cards to review and to
 *   check posted dates before opening individual DETAILS panels.
 *
 * Returns (as the last evaluated expression):
 *   Multi-line string, one card per line:
 *     "0 | Posted: 2024-01-15 | Senior Data Analyst"
 *     "1 | Posted: 2024-01-14 | Business Intelligence Developer"
 *     etc.
 *
 * Plain text (not JSON) is returned because the skill reads this output as a
 * human-readable block and parses it line by line — JSON would add unnecessary
 * complexity for a simple list.
 */

Array.from(document.querySelectorAll('.card')).map((cardElement, cardIndex) => {
  // `.card` is SI Systems portal's CSS class for each job result row — confirmed
  // by inspecting the portal's DOM. Update this selector if the portal redesigns.
  const textLines = cardElement.innerText
    .trim()
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0);

  // Find the job title: the first line that isn't a metadata label or action button.
  // SI Systems cards include lines like "Expertise: ...", "Job Type: ...", "DETAILS",
  // and "APPLY" which we skip to isolate the actual title.
  // This exclusion list was derived by inspecting real card DOM output.
  // If SI Systems adds new label prefixes, add them here.
  const title = textLines.find(line =>
    !line.startsWith('Expertise:') &&
    !line.startsWith('Job Type') &&
    !line.startsWith('Location') &&
    !line.startsWith('Posted') &&
    line !== 'DETAILS' &&
    line !== 'APPLY'
  ) || '';

  // Find the posted date line (starts with "Posted:").
  const postedDate = textLines.find(line => line.startsWith('Posted:')) || '';

  // Title is truncated to 70 chars — enough to identify the role for display/logging
  // without making output unwieldy. Does not affect downstream matching; the full
  // title is fetched when the JD is opened.
  return `${cardIndex} | ${postedDate} | ${title.substring(0, 70)}`;
}).join('\n');
