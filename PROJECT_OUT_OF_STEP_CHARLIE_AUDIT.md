# Project Out of Step, Charlie — Site Audit Report

**Date:** October 23, 2025
**Scope:** Full audit of caty-equity-research-live for inconsistencies, broken references, and missing integrations
**Triggered by:** Monte Carlo chart not showing on main page

---

## Critical Issues (Fix Immediately)

### **Issue #1: Monte Carlo Chart is Broken Image Reference** ⚠️ CRITICAL
- **Location:** `index.html` line 1785
- **Current state:** `<img src="assets/monte_carlo_pt_distribution.png">`
- **Problem:** This PNG file does not exist (verified via `ls assets/*.png` → no matches)
- **User impact:** Main page shows broken image in Monte Carlo section
- **Correct implementation:** Should be interactive Chart.js canvas (like `CATY_14_monte_carlo_valuation.html` line 81)
- **Fix:** Replace static image with Chart.js histogram showing distribution with percentile markers

**Code reference:** `CATY_14_monte_carlo_valuation.html:80-84`
```html
<div class="chart-wrapper">
    <canvas id="mcDistributionChart" role="img" tabindex="0" aria-label="Monte Carlo distribution histogram..."></canvas>
</div>
```

---

### **Issue #2: New Sensitivity Lab Not in Module Grid** ⚠️ HIGH
- **Location:** `sensitivity_analysis.html` exists and is LIVE
- **Problem:** No module card in the main page module grid (lines 104-211)
- **Current links:** Referenced in body text (lines 87, 550, 984, 1589, 1933, 1942) but missing from structured navigation
- **User impact:** Users have to stumble upon links in prose; not discoverable via module grid
- **Fix:** Add module card under "Valuation" or "Financial Analysis" section

**Suggested module card:**
```html
<a href="sensitivity_analysis.html" class="module-card module-card-gold" data-status="UPDATED">
    <div class="module-card-badge">SENSITIVITY LAB ⭐ • NEW</div>
    <div class="module-card-title">NIM Sensitivity Lab</div>
    <div class="module-card-description">Interactive EPS & TBVPS response to ±50 bps NIM shifts under 3 loan growth scenarios (updated 2025-10-23)</div>
</a>
```

---

## Medium Priority Issues

### **Issue #3: Duplicate Sensitivity Analysis Files**
- **Files:**
  1. `sensitivity_analysis.html` (NEW, Oct 23 2025, clean McCandless style, 450px charts)
  2. `CATY_18_sensitivity_analysis.html` (OLD, different title "CATY - EPS/TBV Sensitivities")
- **Problem:** Two files with similar names and purpose; unclear which is canonical
- **Current state:**
  - New file IS linked from index.html body text
  - Old CATY_18 file is NOT linked anywhere
  - Old file not in module grid
- **Fix:**
  - Option A: Delete `CATY_18_sensitivity_analysis.html` (obsolete)
  - Option B: Redirect CATY_18 → sensitivity_analysis.html
  - Option C: Keep both, clarify purpose (e.g., CATY_18 = old static, new = interactive)

**Recommendation:** Delete CATY_18 if it's obsolete, or merge content if there's unique data

---

### **Issue #4: CATY_SOCIAL_SENTIMENT Module Not Integrated**
- **File:** `CATY_SOCIAL_SENTIMENT.html` exists
- **Problem:** Not linked from module grid, not mentioned in index.html
- **Status:** Unclear if this is WIP, archived, or should be live
- **Fix:**
  - If live → Add to ESG section or create "Sentiment Analysis" category
  - If archived → Move to `/archive/` directory or delete
  - If WIP → Document status in filename (e.g., `CATY_SOCIAL_SENTIMENT_WIP.html`)

---

## Low Priority / Clarity Issues

### **Issue #5: Module Count Mismatch**
- **Files:** 19 CATY module HTML files on disk
- **Module cards shown:** 17 cards in the grid
- **Missing from grid:**
  - `sensitivity_analysis.html` (addressed in Issue #2)
  - `CATY_18_sensitivity_analysis.html` (addressed in Issue #3)
  - `CATY_SOCIAL_SENTIMENT.html` (addressed in Issue #4)
- **Status:** This is consequence of Issues #2-4, not a standalone problem

---

### **Issue #6: No Static Image Assets Directory Structure**
- **Current:** `assets/` directory has NO png/jpg/svg files (verified via ls)
- **Problem:** If we ever need static images (logos, diagrams, screenshots), unclear where they go
- **Impact:** Low (all charts are Chart.js currently)
- **Fix:** Create `assets/img/` subdirectory for any future static images

---

## Autogen Marker Audit (No Issues Found)

- **Total autogen sections:** 59 markers (29.5 BEGIN/END pairs) ✅
- **All pairs balanced:** Verified BEGIN has matching END ✅
- **No orphaned markers:** All sections properly closed ✅

**Sample autogen sections verified:**
- page-title (line 6)
- module-grid (lines 104-211)
- exec-company-snapshot (line 222)
- monte-carlo-summary (lines 1769-1796)

---

## Validation Gate Status (Passing)

Ran validation scripts:
```bash
scripts/reconciliation_guard.py → Exit 0 ✅
scripts/disconfirmer_monitor.py → Exit 0 ✅
```

**No data integrity issues found.**

---

## Recommended Fix Priority

### **Immediate (Deploy Today):**
1. ✅ **Fix Issue #1:** Replace broken Monte Carlo PNG with interactive Chart.js canvas
2. ✅ **Fix Issue #2:** Add sensitivity_analysis.html to module grid

### **This Week:**
3. **Fix Issue #3:** Resolve CATY_18 duplicate (delete or redirect)
4. **Fix Issue #4:** Integrate or archive CATY_SOCIAL_SENTIMENT

### **Nice to Have:**
5. Create `assets/img/` directory structure for future static images

---

## Codex Execution Plan

### **Task 1: Monte Carlo Interactive Chart**
**Target:** Replace `index.html` line 1785 broken image with Chart.js canvas

**Steps:**
1. Read `CATY_14_monte_carlo_valuation.html` lines 1-200 to extract Chart.js implementation
2. Extract the `mcDistributionChart` canvas setup and JavaScript
3. In `index.html`, replace lines 1785-1786 (broken img tag) with:
   - Canvas element wrapper
   - Chart.js script (inline or separate)
   - Maintain same visual hierarchy (within `.insight-box`)
4. Verify Chart.js CDN is loaded in index.html `<head>` (should already be line 10)
5. Test locally to ensure chart renders with correct data from `data/caty14_monte_carlo.json`

**Acceptance Criteria:**
- Monte Carlo section shows interactive histogram (not broken image)
- Percentile markers (5th, 25th, 50th, 75th, 95th) visible
- Spot price overlay ($46.17) shown
- Hover tooltips work
- No console errors

---

### **Task 2: Add Sensitivity Lab Module Card**
**Target:** Add `sensitivity_analysis.html` to module grid in `index.html`

**Steps:**
1. Find the "Valuation" section module grid (around line 130-146)
2. Add new module card after CATY_16 (COE Triangulation)
3. Use `module-card-gold` class (same tier as Monte Carlo, RIM)
4. Badge text: "SENSITIVITY LAB ⭐ • NEW"
5. Description: "Interactive EPS & TBVPS response to ±50 bps NIM shifts under 3 loan growth scenarios (updated 2025-10-23)"

**Code to insert after line 145:**
```html
<a href="sensitivity_analysis.html" class="module-card module-card-gold" data-status="UPDATED">
    <div class="module-card-badge">SENSITIVITY LAB ⭐ • NEW</div>
    <div class="module-card-title">NIM Sensitivity Lab</div>
    <div class="module-card-description">Interactive EPS & TBVPS response to ±50 bps NIM shifts under 3 loan growth scenarios (updated 2025-10-23)</div>
</a>
```

**Acceptance Criteria:**
- Module card appears in Valuation section
- Link works (opens sensitivity_analysis.html)
- Visual styling matches peer cards (gold tier)
- No layout breaks on mobile

---

### **Task 3: Resolve CATY_18 Duplicate**
**Target:** Decide fate of `CATY_18_sensitivity_analysis.html`

**Investigation needed:**
1. Compare `CATY_18_sensitivity_analysis.html` vs `sensitivity_analysis.html`:
   - File size
   - Chart implementation
   - Data source
   - Last modified date
2. If CATY_18 is obsolete → Delete it
3. If CATY_18 has unique content → Document why we have both

**Default action (if no unique content):** Delete `CATY_18_sensitivity_analysis.html`

---

### **Task 4: CATY_SOCIAL_SENTIMENT Integration**
**Target:** Integrate or archive `CATY_SOCIAL_SENTIMENT.html`

**Steps:**
1. Read first 50 lines to understand purpose
2. Check if it references live data (`data/*.json`)
3. If complete → Add to module grid (ESG or new "Market Sentiment" section)
4. If WIP → Rename to `CATY_SOCIAL_SENTIMENT_WIP.html` and document in README
5. If obsolete → Move to `/archive/` directory

---

## Testing Checklist (After Codex Fixes)

**Before push:**
- [ ] Open `index.html` in browser
- [ ] Scroll to Monte Carlo section → verify interactive chart renders (not broken image)
- [ ] Scroll to module grid → verify Sensitivity Lab card appears
- [ ] Click Sensitivity Lab card → verify page loads
- [ ] Click module cards for Files 01-17 → all work
- [ ] Run validation gates: `python3 scripts/reconciliation_guard.py` → Exit 0
- [ ] Run: `python3 scripts/disconfirmer_monitor.py` → Exit 0
- [ ] Check browser console → no errors
- [ ] Mobile responsive check → module grid wraps correctly

**After push:**
- [ ] Wait 2 min for GitHub Pages build
- [ ] curl -I live site → HTTP 200
- [ ] Open live site → Monte Carlo chart works
- [ ] Open live site → Sensitivity Lab card visible and clickable

---

## Summary for Nirvan

**What we found:**
1. Monte Carlo chart is broken (static PNG that doesn't exist)
2. New sensitivity lab isn't in the module grid (hidden in plain sight)
3. Duplicate sensitivity files (CATY_18 vs new one)
4. Social sentiment module floating unlinked

**What we're fixing:**
1. Replace broken image with interactive Chart.js (matches CATY_14 module)
2. Add sensitivity lab to module grid (Valuation section, gold tier)
3. Delete or clarify CATY_18 duplicate
4. Integrate or archive social sentiment

**Time estimate:**
- Codex execution: 15-20 minutes
- Local testing: 5 minutes
- Deploy + verify: 5 minutes
- **Total: ~30 minutes**

**Risk level:** Low (all fixes are additive or replacements, no deletions of live content)

---

**Status:** AUDIT COMPLETE — Ready for Codex execution

**Next:** Nirvan approves fix plan → Codex executes → Test → Push live
