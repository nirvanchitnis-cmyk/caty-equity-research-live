/* Performance & Compatibility Helpers
 * - Provides a shared idle scheduler (requestIdleCallback fallback)
 * - Flags reduced motion preference for CSS and JS consumers
 * - Normalises external link attributes for enterprise safe-link scanners
 */
(function () {
    'use strict';

    const root = document.documentElement;
    const motionQuery = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;

    function applyMotionPreference(matches) {
        if (!root) {
            return;
        }
        if (matches) {
            root.setAttribute('data-reduces-motion', 'true');
        } else {
            root.removeAttribute('data-reduces-motion');
        }
    }

    if (motionQuery) {
        applyMotionPreference(motionQuery.matches);
        motionQuery.addEventListener('change', (event) => applyMotionPreference(event.matches));
    }

    function scheduleIdle(callback, timeout = 1200) {
        if (typeof callback !== 'function') {
            return;
        }

        if ('requestIdleCallback' in window) {
            window.requestIdleCallback(callback, { timeout });
            return;
        }

        window.setTimeout(callback, Math.min(timeout, 500));
    }

    function normaliseExternalLinks() {
        const anchors = document.querySelectorAll('a[target="_blank"]');
        anchors.forEach((anchor) => {
            const rel = anchor.getAttribute('rel') || '';
            const values = new Set(rel.split(/\s+/).filter(Boolean));
            values.add('noopener');
            values.add('noreferrer');
            anchor.setAttribute('rel', Array.from(values).join(' '));
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        scheduleIdle(normaliseExternalLinks, 1800);
    });

    window.__scheduleIdle = scheduleIdle;
})();
