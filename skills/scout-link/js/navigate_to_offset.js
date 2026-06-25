// Navigate to a specific offset — replace [OFFSET] before running
(function() {
  const url = new URL(window.location.href);
  url.searchParams.set('start', '[OFFSET]');
  window.location.href = url.toString();
  return url.toString();
})()
