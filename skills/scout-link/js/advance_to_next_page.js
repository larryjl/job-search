// Advance to next page by incrementing start offset
(function() {
  const url = new URL(window.location.href);
  const cur = parseInt(url.searchParams.get('start') || '0', 10);
  url.searchParams.set('start', cur + 25);
  window.history.pushState({}, '', url.toString());
  // Try clicking Next button as fallback
  const next = document.querySelector('button[aria-label="View next page"]') ||
               Array.from(document.querySelectorAll('button')).find(b => /next/i.test(b.textContent));
  if (next) next.click();
  return url.toString();
})()
