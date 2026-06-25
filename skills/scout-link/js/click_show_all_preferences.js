// Click the "Show all" link for the "Jobs based on your preferences" section
(function() {
  const headings = Array.from(document.querySelectorAll('h2, h3, span, div'));
  const prefHeading = headings.find(el => el.textContent.includes('Jobs based on your preferences'));
  if (!prefHeading) return 'not found';
  let container = prefHeading;
  for (let i = 0; i < 8; i++) {
    container = container.parentElement;
    if (!container) break;
    const links = Array.from(container.querySelectorAll('a, button'));
    const showAll = links.find(el => /show all/i.test(el.textContent));
    if (showAll) { showAll.click(); return 'clicked'; }
  }
  return 'not found';
})()
