function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update button text and ARIA state
    const button = document.querySelector('.theme-toggle');
    const icon = document.getElementById('theme-icon');
    const text = document.getElementById('theme-text');

    if (newTheme === 'dark') {
        icon.textContent = '☀️';
        text.textContent = 'Light Mode';
        button.setAttribute('aria-pressed', 'true');
    } else {
        icon.textContent = '🌙';
        text.textContent = 'Dark Mode';
        button.setAttribute('aria-pressed', 'false');
    }
}

// Load saved theme on page load
window.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    const button = document.querySelector('.theme-toggle');
    const icon = document.getElementById('theme-icon');
    const text = document.getElementById('theme-text');

    if (savedTheme === 'dark') {
        icon.textContent = '☀️';
        text.textContent = 'Light Mode';
        button.setAttribute('aria-pressed', 'true');
    } else {
        button.setAttribute('aria-pressed', 'false');
    }
});

// Toggle Table of Contents
function toggleTOC() {
    const toc = document.getElementById('navTOC');
    const button = document.querySelector('.toc-toggle-button');

    if (toc.style.display === 'none' || toc.style.display === '') {
        toc.style.display = 'block';
        button.setAttribute('aria-expanded', 'true');
    } else {
        toc.style.display = 'none';
        button.setAttribute('aria-expanded', 'false');
    }
}

// Smooth scroll for TOC links
document.addEventListener('DOMContentLoaded', () => {
    const tocLinks = document.querySelectorAll('.toc-link');
    const button = document.querySelector('.toc-toggle-button');

    tocLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                // Close TOC on mobile after click
                if (window.innerWidth < 768) {
                    const toc = document.getElementById('navTOC');
                    toc.style.display = 'none';
                    button.setAttribute('aria-expanded', 'false');
                }
            }
        });
    });
});
