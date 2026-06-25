// Scroll to render all job cards
(async function() {
  const main = document.querySelector('main') || document.body;
  main.scrollTo(0, main.scrollHeight);
  await new Promise(r => setTimeout(r, 1000));
  main.scrollTo(0, 0);
  // Also try the jobs list panel
  const panels = document.querySelectorAll('.jobs-search-results-list, [class*="scaffold-layout__list"]');
  for (const p of panels) {
    p.scrollTo(0, p.scrollHeight);
    await new Promise(r => setTimeout(r, 500));
    p.scrollTo(0, 0);
  }
  return 'scrolled';
})()
