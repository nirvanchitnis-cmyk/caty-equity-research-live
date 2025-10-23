const TOC_FOCUSABLE_SELECTOR = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
].join(', ');

let tocPreviouslyFocusedElement = null;

function updateThemeToggleState(isDarkMode) {
    const button = document.querySelector('.theme-toggle');
    const icon = document.getElementById('theme-icon');
    const text = document.getElementById('theme-text');

    if (!button || !icon || !text) {
        return;
    }

    button.setAttribute('aria-checked', isDarkMode ? 'true' : 'false');
    icon.textContent = isDarkMode ? '☀️' : '🌙';
    text.textContent = isDarkMode ? 'Light Mode' : 'Dark Mode';
}

function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeToggleState(newTheme === 'dark');
}

function getTOCElements() {
    return {
        toc: document.getElementById('navTOC'),
        toggleButton: document.querySelector('.toc-toggle-button')
    };
}

function getFocusableElements(container) {
    if (!container) {
        return [];
    }

    return Array.from(container.querySelectorAll(TOC_FOCUSABLE_SELECTOR))
        .filter(element => !element.hasAttribute('hidden') && element.getAttribute('aria-hidden') !== 'true');
}

function openTOC() {
    const { toc, toggleButton } = getTOCElements();
    if (!toc || !toggleButton) {
        return;
    }

    tocPreviouslyFocusedElement = document.activeElement && typeof document.activeElement.focus === 'function'
        ? document.activeElement
        : toggleButton;

    toc.removeAttribute('hidden');
    toggleButton.setAttribute('aria-expanded', 'true');

    const focusTarget = toc.querySelector('.toc-link') || toc;
    window.requestAnimationFrame(() => focusTarget.focus());
}

function closeTOC({ restoreFocus = true } = {}) {
    const { toc, toggleButton } = getTOCElements();
    if (!toc || !toggleButton) {
        return;
    }

    if (toc.hasAttribute('hidden')) {
        return;
    }

    toc.setAttribute('hidden', '');
    toggleButton.setAttribute('aria-expanded', 'false');

    if (restoreFocus) {
        const fallbackTarget = tocPreviouslyFocusedElement && typeof tocPreviouslyFocusedElement.focus === 'function'
            ? tocPreviouslyFocusedElement
            : toggleButton;
        window.requestAnimationFrame(() => fallbackTarget.focus());
    }

    tocPreviouslyFocusedElement = null;
}

function toggleTOC(forceState) {
    const { toc } = getTOCElements();
    if (!toc) {
        return;
    }

    const isHidden = toc.hasAttribute('hidden');
    const shouldOpen = typeof forceState === 'boolean' ? forceState : isHidden;

    if (shouldOpen) {
        openTOC();
    } else {
        closeTOC();
    }
}

function handleTOCKeydown(event) {
    const { toc, toggleButton } = getTOCElements();
    if (!toc || !toggleButton || toc.hasAttribute('hidden')) {
        return;
    }

    if (event.key === 'Escape' || event.key === 'Esc') {
        event.preventDefault();
        closeTOC();
        return;
    }

    if (event.key !== 'Tab') {
        return;
    }

    const focusableElements = getFocusableElements(toc);

    if (focusableElements.length === 0) {
        event.preventDefault();
        toggleButton.focus();
        return;
    }

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    const isShiftPressed = event.shiftKey;
    const activeElement = document.activeElement;

    if (!isShiftPressed && activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
    } else if (isShiftPressed && activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
    }
}

function handleGlobalEscape(event) {
    if (event.key !== 'Escape' && event.key !== 'Esc') {
        return;
    }

    const { toc } = getTOCElements();
    if (!toc || toc.hasAttribute('hidden')) {
        return;
    }

    event.preventDefault();
    closeTOC();
}

function initialiseSkipLink() {
    const skipLink = document.querySelector('.skip-link');
    const mainContent = document.getElementById('main-content');

    if (!skipLink || !mainContent) {
        return;
    }

    skipLink.addEventListener('click', () => {
        window.requestAnimationFrame(() => mainContent.focus());
    });

    skipLink.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            window.requestAnimationFrame(() => mainContent.focus());
        }
    });
}

window.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeToggleState(savedTheme === 'dark');

    initialiseSkipLink();

    const { toc, toggleButton } = getTOCElements();
    if (toggleButton) {
        toggleButton.setAttribute('aria-expanded', toggleButton.getAttribute('aria-expanded') || 'false');
    }

    if (toc && toggleButton) {
        const tocLinks = toc.querySelectorAll('.toc-link');

        tocLinks.forEach(link => {
            link.addEventListener('click', (event) => {
                event.preventDefault();
                const targetId = link.getAttribute('href');
                const targetElement = document.querySelector(targetId);

                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });

                    if (window.innerWidth < 768) {
                        closeTOC({ restoreFocus: true });
                    }
                }
            });
        });

        toc.addEventListener('keydown', handleTOCKeydown);
        toggleButton.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' || event.key === 'Esc') {
                event.preventDefault();
                closeTOC();
            }
        });
    }
});

window.toggleTheme = toggleTheme;
window.toggleTOC = toggleTOC;

document.addEventListener('keydown', handleGlobalEscape);
