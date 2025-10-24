// Minimal theme toggle shim for evidence HTML pages
// Provides window.toggleTheme and initializes theme based on localStorage
(function(){
  function updateButton(isDark){
    var btn = document.querySelector('.theme-toggle');
    var icon = document.getElementById('theme-icon');
    var text = document.getElementById('theme-text');
    if (btn) btn.setAttribute('aria-checked', isDark ? 'true' : 'false');
    if (icon) icon.textContent = isDark ? '☀️' : '🌙';
    if (text) text.textContent = isDark ? 'Light Mode' : 'Dark Mode';
  }
  function toggleTheme(){
    var html = document.documentElement;
    var current = html.getAttribute('data-theme') || 'light';
    var next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch(e) {}
    updateButton(next === 'dark');
  }
  window.toggleTheme = toggleTheme;
  document.addEventListener('DOMContentLoaded', function(){
    var saved = 'light';
    try { saved = localStorage.getItem('theme') || 'light'; } catch(e) {}
    document.documentElement.setAttribute('data-theme', saved);
    updateButton(saved === 'dark');
  });
})();

