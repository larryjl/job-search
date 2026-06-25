// Harvest job IDs by clicking each card and reading currentJobId from URL
(async function() {
  window.__cardWalk = { results: [] };
  const cards = Array.from(document.querySelectorAll('main div[role="button"]')).filter(el => {
    const txt = (el.innerText || el.textContent).trim();
    const lines = txt.split('\n').map(l => l.trim()).filter(Boolean);
    return lines.length >= 2 && el.offsetHeight > 30;
  });

  function getCurrentJobId() {
    const url = new URL(window.location.href);
    return url.searchParams.get('currentJobId');
  }

  function parseCard(el) {
    const lines = (el.innerText || el.textContent).split('\n').map(l => l.trim()).filter(Boolean)
      .filter(l => !/^(Promoted|Viewed|Easy Apply|Applied)$/i.test(l));
    const title = lines[0] || '';
    const company = lines[1] || '';
    const locationLine = lines[2] || '';
    let work_type = 'Unknown';
    if (/\(Remote\)/i.test(locationLine)) work_type = 'Remote';
    else if (/\(Hybrid\)/i.test(locationLine)) work_type = 'Hybrid';
    else if (/\(On-site\)/i.test(locationLine)) work_type = 'On-site';
    const location = locationLine.replace(/\s*\(.*?\)\s*/g, '').trim();
    return { title, company, location, work_type };
  }

  const seenIds = new Set();
  for (let i = 0; i < cards.length; i++) {
    const card = cards[i];
    const meta = parseCard(card);
    const before = getCurrentJobId();
    card.click();
    // Poll for URL change up to 500ms
    let id = null;
    for (let t = 0; t < 10; t++) {
      await new Promise(r => setTimeout(r, 60));
      const cur = getCurrentJobId();
      if (cur && cur !== before) { id = cur; break; }
    }
    const isDup = id && seenIds.has(id);
    if (id) seenIds.add(id);
    window.__cardWalk.results.push({ ...meta, id: isDup ? null : id, dupId: isDup ? id : null });
  }
  return { total: cards.length, uniqueIds: window.__cardWalk.results.filter(r => r.id).length };
})()
