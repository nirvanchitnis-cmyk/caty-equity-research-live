# Codex Polish Patchwork — Subtle Visual Enhancements

**Mission:** Make the CATY site "pop" with 8-10 small CSS/JS tweaks. No structural changes, just polish.

---

## 1. Metric Card Hover (Like Module Cards)

**File:** `styles/caty-equity-research.css`
**Where:** After `.metric-card` definition (around line 1025-1035)

**Add:**
```css
.metric-card {
    /* ...existing styles... */
    transition: transform 200ms ease-out, box-shadow 200ms ease-out;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(20, 32, 45, 0.12);
}
```

**Why:** Metric cards are static. Adding subtle lift on hover makes them feel more premium, consistent with module cards.

---

## 2. Alert Box Left Accent Border

**File:** `styles/caty-equity-research.css`
**Where:** `.alert-box`, `.highlight-box`, `.status-banner` definitions

**Change:**
```css
/* BEFORE */
.alert-box.info {
    background: var(--info-surface);
}

/* AFTER */
.alert-box.info {
    background: var(--info-surface);
    border-left: 4px solid var(--info); /* ADD THIS */
}

.alert-box.warning {
    background: var(--warning-surface);
    border-left: 4px solid var(--warning); /* ADD THIS */
}

.alert-box.danger,
.status-banner.status-warning {
    background: var(--danger-surface);
    border-left: 4px solid var(--danger); /* ADD THIS */
}

.alert-box.success,
.highlight-box.success {
    background: var(--success-surface);
    border-left: 4px solid var(--success); /* ADD THIS */
}
```

**Why:** Adds visual hierarchy, makes semantic meaning clearer at a glance. Brand color pops.

---

## 3. CFA Category Header Emoji Scale on Hover

**File:** `styles/caty-equity-research.css`
**Where:** `.cfa-category-header` (around line 900-910)

**Add:**
```css
.cfa-category-header {
    /* ...existing styles... */
    transition: transform 150ms ease-out;
    display: inline-block; /* needed for transform */
}

.cfa-category-header:hover {
    transform: scale(1.02);
}
```

**Why:** Subtle playfulness. Emojis scale slightly on hover, adding life to section headers without being distracting.

---

## 4. Smooth Scroll Behavior

**File:** `styles/caty-equity-research.css`
**Where:** Top-level `html` selector (around line 200)

**Add:**
```css
html {
    scroll-behavior: smooth;
}

/* Disable for users who prefer reduced motion */
@media (prefers-reduced-motion: reduce) {
    html {
        scroll-behavior: auto;
    }
}
```

**Why:** TOC links scroll smoothly instead of jumping. Feels polished. Respects accessibility preferences.

---

## 5. Table Row Subtle Striping

**File:** `styles/caty-equity-research.css`
**Where:** `table` styles (around line 530-560)

**Add:**
```css
tbody tr:nth-child(even) {
    background: rgba(20, 32, 45, 0.02); /* very subtle */
}

tbody tr:hover {
    background: rgba(196, 30, 58, 0.05); /* existing hover, keep it */
}

/* Dark mode override */
[data-theme="dark"] tbody tr:nth-child(even) {
    background: rgba(255, 255, 255, 0.02);
}
```

**Why:** Easier to scan long tables (like peer comparison). Stripe is barely visible, hover is still dominant.

---

## 6. "NEW" / "UPDATED" Badge Subtle Pulse

**File:** `styles/caty-equity-research.css`
**Where:** After `.module-card-badge` (around line 970)

**Add:**
```css
@keyframes badge-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.75; }
}

.module-card-badge[data-status="UPDATED"],
.module-card-badge:contains("NEW") {
    animation: badge-pulse 3s ease-in-out infinite;
}

/* Disable for reduced motion */
@media (prefers-reduced-motion: reduce) {
    .module-card-badge {
        animation: none !important;
    }
}
```

**Why:** "UPDATED" and "NEW" badges subtly pulse, drawing attention to fresh content without being annoying. Accessibility-safe.

---

## 7. Chart Wrapper Fade-In on Load

**File:** Create new `scripts/chart-fade-in.js` (or add to bottom of each HTML page)

**Add to `<head>` of all CATY_*.html files:**
```html
<style>
.chart-wrapper {
    opacity: 0;
    transition: opacity 400ms ease-in;
}

.chart-wrapper.loaded {
    opacity: 1;
}
</style>
```

**Add to bottom of `<body>`:**
```html
<script>
// Fade in charts after they render
document.addEventListener('DOMContentLoaded', () => {
    const wrappers = document.querySelectorAll('.chart-wrapper');
    wrappers.forEach(wrapper => {
        // Wait for Chart.js to render (brief delay)
        setTimeout(() => wrapper.classList.add('loaded'), 150);
    });
});
</script>
```

**Why:** Charts gracefully fade in instead of popping into existence. Feels smoother, more premium.

---

## 8. Status Banner Subtle Border Pulse (Very Subtle)

**File:** `styles/caty-equity-research.css`
**Where:** `.status-banner` (around line 750)

**Add:**
```css
@keyframes border-pulse {
    0%, 100% { border-left-color: var(--danger); }
    50% { border-left-color: var(--warning); }
}

.status-banner.status-warning {
    animation: border-pulse 4s ease-in-out infinite;
}

/* Disable for reduced motion */
@media (prefers-reduced-motion: reduce) {
    .status-banner {
        animation: none !important;
    }
}
```

**Why:** The "HOLD" banner border subtly shifts between danger red and warning orange, drawing attention without being aggressive.

---

## 9. Link Underline on Hover (Inline Links Only)

**File:** `styles/caty-equity-research.css`
**Where:** `a` styles (around line 720)

**Enhance:**
```css
a {
    color: var(--link-color);
    text-decoration: none;
    transition: color 200ms ease, border-bottom 200ms ease;
    border-bottom: 1px solid transparent;
}

a:hover {
    color: var(--link-hover);
    border-bottom: 1px solid var(--link-hover);
}

/* Exclude nav/card links from underline */
.module-card a,
.toc-link,
.back-button,
.theme-toggle {
    border-bottom: none !important;
}
```

**Why:** Inline text links get a subtle underline on hover, making them more discoverable without cluttering the design.

---

## 10. Focus Ring Enhancement (A11y + Brand)

**File:** `styles/caty-equity-research.css`
**Where:** After `:focus-visible` styles (around line 250)

**Enhance:**
```css
*:focus-visible {
    outline: 2px solid var(--cathay-gold); /* brand gold instead of default blue */
    outline-offset: 2px;
    border-radius: 2px;
}

/* Specific override for module cards */
.module-card:focus-visible {
    outline: 3px solid var(--cathay-gold);
    outline-offset: 4px;
}
```

**Why:** Keyboard navigation gets a branded, highly visible focus ring. More accessible and on-brand.

---

## Execution Checklist for Codex

### Phase 1: CSS-Only Changes (5 min)
- [ ] Add metric card hover state
- [ ] Add alert box left borders (info/warning/danger/success)
- [ ] Add CFA header hover scale
- [ ] Add smooth scroll behavior
- [ ] Add table row striping
- [ ] Enhance link hover underline
- [ ] Enhance focus rings with brand gold

### Phase 2: Animations (3 min)
- [ ] Add badge pulse animation
- [ ] Add status banner border pulse
- [ ] Add reduced-motion media queries

### Phase 3: Chart Fade-In (7 min)
- [ ] Add chart-wrapper fade CSS
- [ ] Add DOMContentLoaded script to all CATY_*.html files
- [ ] Test on 3 random pages

### Total Time: ~15 minutes

---

## Acceptance Criteria

**Before push:**
1. Test on index.html: metric cards lift on hover, smooth scroll works
2. Test on CATY_01: charts fade in, tables have subtle stripes
3. Test on CATY_11: alert boxes have left accent borders
4. Test keyboard navigation: gold focus rings visible on all interactive elements
5. Test with motion disabled: no animations trigger

**Visual Impact:**
- Site feels more polished and premium
- Interactions are smooth and intentional
- Brand colors (gold, red) pop in subtle ways
- No jarring changes, just refined details

---

## Notes for Nirvan

This patchwork keeps all existing structure and functionality. Zero risk of breaking anything, just layering polish on top.

If any animation feels too much after testing, we can dial it back. The badge pulse and border pulse are most likely to be polarizing — I kept them very subtle (3-4s duration) but test and adjust as needed.

All animations respect `prefers-reduced-motion`, so users who need it won't see any movement.

Ready for Codex execution whenever you want to proceed.
