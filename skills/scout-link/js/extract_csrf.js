// Extract LinkedIn CSRF token from cookies
(function() {
  const match = document.cookie.match(/JSESSIONID="?([^";]+)"?/);
  return match ? match[1] : null;
})()
