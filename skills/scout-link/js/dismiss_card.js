// Dismiss a job card — replace [Job Title] and [Company] before running
(async function() {
  const targetTitle = '[Job Title]';
  const targetCompany = '[Company]';
  const cards = Array.from(document.querySelectorAll('main div[role="button"]'));
  const card = cards.find(el => {
    const txt = el.textContent;
    return txt.includes(targetTitle) && txt.includes(targetCompany);
  });
  if (!card) return 'not found';
  // Look for dismiss/X button in the card or nearby
  const parent = card.closest('li') || card.parentElement;
  const dismissBtn = parent ? (
    parent.querySelector('button[aria-label*="dismiss"]') ||
    parent.querySelector('button[aria-label*="Dismiss"]') ||
    parent.querySelector('button[aria-label*="hide"]') ||
    Array.from(parent.querySelectorAll('button')).find(b => /dismiss|hide|not interested/i.test(b.getAttribute('aria-label') || b.textContent))
  ) : null;
  if (dismissBtn) { dismissBtn.click(); return 'dismissed'; }
  return 'not found';
})()
