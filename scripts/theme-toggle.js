const TOC_FOCUSABLE_SELECTOR = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
].join(', ');

let tocPreviouslyFocusedElement = null;
const motionQuery = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;

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

function setTOCLinksInteractive(toc, enabled) {
    if (!toc) {
        return;
    }

    if (enabled) {
        toc.removeAttribute('inert');
    } else {
        toc.setAttribute('inert', '');
    }

    const links = toc.querySelectorAll('.toc-link');
    links.forEach((link) => {
        if (enabled) {
            link.removeAttribute('tabindex');
        } else {
            link.setAttribute('tabindex', '-1');
        }
    });
}

function isMobileViewport() {
    return window.matchMedia('(max-width: 768px)').matches;
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
    if (!toc || !toggleButton || !isMobileViewport()) {
        return;
    }

    tocPreviouslyFocusedElement = document.activeElement && typeof document.activeElement.focus === 'function'
        ? document.activeElement
        : toggleButton;

    toc.classList.add('open');
    toc.setAttribute('aria-hidden', 'false');
    setTOCLinksInteractive(toc, true);
    toggleButton.setAttribute('aria-expanded', 'true');

    const focusTarget = toc.querySelector('.toc-link') || toc;
    window.requestAnimationFrame(() => focusTarget.focus());
}

function allowsSmoothScroll() {
    if (document.documentElement.getAttribute('data-reduces-motion') === 'true') {
        return false;
    }
    return !(motionQuery && motionQuery.matches);
}

function closeTOC({ restoreFocus = true } = {}) {
    const { toc, toggleButton } = getTOCElements();
    if (!toc || !toggleButton || !isMobileViewport()) {
        return;
    }

    if (!toc.classList.contains('open')) {
        return;
    }

    toc.classList.remove('open');
    if (isMobileViewport()) {
        toc.setAttribute('aria-hidden', 'true');
    }
    setTOCLinksInteractive(toc, false);
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
    if (!toc || !isMobileViewport()) {
        return;
    }

    const isOpen = toc.classList.contains('open');
    const shouldOpen = typeof forceState === 'boolean' ? forceState : !isOpen;

    if (shouldOpen) {
        openTOC();
    } else {
        closeTOC();
    }
}

function handleTOCKeydown(event) {
    const { toc, toggleButton } = getTOCElements();
    if (!toc || !toggleButton || !isMobileViewport()) {
        return;
    }

    const tocActive = toc.classList.contains('open');
    if (!tocActive) {
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
    if (!toc || !isMobileViewport()) {
        return;
    }

    if (!toc.classList.contains('open')) {
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
    if (toc) {
        const syncTOCState = () => {
            if (isMobileViewport()) {
                toc.classList.remove('open');
                toc.setAttribute('aria-hidden', 'true');
                if (toggleButton) {
                    toggleButton.setAttribute('aria-expanded', 'false');
                }
                setTOCLinksInteractive(toc, false);
            } else {
                toc.classList.add('open');
                toc.setAttribute('aria-hidden', 'false');
                if (toggleButton) {
                    toggleButton.setAttribute('aria-expanded', 'false');
                }
                setTOCLinksInteractive(toc, true);
            }
        };

        syncTOCState();
        window.addEventListener('resize', () => syncTOCState());
    }

    if (toc && toggleButton) {
        toggleButton.setAttribute('aria-expanded', toggleButton.getAttribute('aria-expanded') || 'false');
        const tocLinks = toc.querySelectorAll('.toc-link');

        tocLinks.forEach(link => {
            link.addEventListener('click', (event) => {
                event.preventDefault();
                const targetId = link.getAttribute('href');
                const targetElement = document.querySelector(targetId);

                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: allowsSmoothScroll() ? 'smooth' : 'auto',
                        block: 'start'
                    });

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
