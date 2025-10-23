// Theme Toggle with proper ARIA states
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;
    const icon = document.getElementById('theme-icon');
    const text = document.getElementById('theme-text');

    // Load saved theme on page load
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);

    // Attach click listener
    themeToggle.addEventListener('click', () => {
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);
    });

    function applyTheme(theme) {
        html.setAttribute('data-theme', theme);

        if (theme === 'dark') {
            icon.textContent = '☀️';
            text.textContent = 'Light Mode';
            themeToggle.setAttribute('aria-checked', 'true');
        } else {
            icon.textContent = '🌙';
            text.textContent = 'Dark Mode';
            themeToggle.setAttribute('aria-checked', 'false');
        }
    }
}

// TOC Toggle with proper ARIA states
function initTOCToggle() {
    const tocToggle = document.getElementById('tocToggle');
    const navTOC = document.getElementById('navTOC');

    if (!tocToggle || !navTOC) return;

    tocToggle.addEventListener('click', () => {
        const isExpanded = tocToggle.getAttribute('aria-expanded') === 'true';

        if (isExpanded) {
            // Hide TOC
            navTOC.style.display = 'none';
            navTOC.setAttribute('aria-hidden', 'true');
            tocToggle.setAttribute('aria-expanded', 'false');
        } else {
            // Show TOC
            navTOC.style.display = 'block';
            navTOC.setAttribute('aria-hidden', 'false');
            tocToggle.setAttribute('aria-expanded', 'true');
        }
    });
}

// Smooth scroll for TOC links
function initTOCLinks() {
    const tocLinks = document.querySelectorAll('.toc-link');
    const tocToggle = document.getElementById('tocToggle');
    const navTOC = document.getElementById('navTOC');

    tocLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });

                // Close TOC on mobile after click
                if (window.innerWidth < 768) {
                    navTOC.style.display = 'none';
                    navTOC.setAttribute('aria-hidden', 'true');
                    tocToggle.setAttribute('aria-expanded', 'false');
                }
            }
        });
    });
}

// Initialize all on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initTOCToggle();
    initTOCLinks();
});
