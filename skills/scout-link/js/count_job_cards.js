// Count job cards in the results panel
(function() {
  const cards = Array.from(document.querySelectorAll('main div[role="button"]')).filter(el => {
    const txt = el.innerText || el.textContent;
    const lines = txt.split('\n').map(l => l.trim()).filter(Boolean);
    return lines.length >= 2 && el.offsetHeight > 30;
  });
  return cards.length;
})()
