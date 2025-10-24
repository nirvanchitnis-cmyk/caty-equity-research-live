# CODEX HANDOFF: Operation STALE FIXES

**Date:** 2025-10-24
**From:** Claude (Creative Director)
**To:** Codex (Execution Specialist)
**Priority:** CRITICAL - Live site provenance broken

---

## Context

After reorganizing the repo (Operation Intuitive File System), we broke the live site's provenance trail:
1. **GitHub Pages cannot serve directory listings** - 4 directory links return 404
2. **2 stale file references** point to old locations
3. **Auditors clicking evidence links hit dead ends** - AUDIT FAILURE

---

## What You Must Fix

### CRITICAL FIX #1: Create 5 index.html Files for Evidence Directories

GitHub Pages requires index.html in each directory. These are MISSING:

#### 1. `evidence/index.html`
**Location:** `/Users/nirvanchitnis/caty-equity-research-live/evidence/index.html`
**Linked from:** index.html line ~960 ("Browse evidence directory →")
**Purpose:** Hub for all 159 evidence files across 6 subdirectories

**Content Requirements:**
- Page title: "CATY Evidence Directory"
- Link canonical CSS: `<link rel="stylesheet" href="../styles/caty-equity-research.css">`
- Header with back button to index.html
- 6 sections:
  1. **Root Evidence Files** (68 files) - list all .html files in evidence/ root
  2. **Workpapers** (10 files) - link to evidence/workpapers/
  3. **Raw Source Filings** (62 files) - link to evidence/raw/
  4. **Primary Sources** (13 files) - link to evidence/primary_sources/
  5. **Archive** (4 files) - link to evidence/archive/
  6. **Peer Sources** (2 files) - link to evidence/peer_sources/

**File List (evidence/ root - 68 files):**
```bash
ls -1 evidence/*.html | grep -v "^evidence/workpapers\|^evidence/raw\|^evidence/primary_sources\|^evidence/archive\|^evidence/peer_sources"
```

Use canonical CATY page structure (see CATY_01_company_profile.html for template).

---

#### 2. `evidence/workpapers/index.html`
**Location:** `/Users/nirvanchitnis/caty-equity-research-live/evidence/workpapers/index.html`
**Linked from:** index.html line ~975 ("Workpapers directory")
**Purpose:** 10 analytical workpapers (NCO bridge, buyback analysis, CET1 headroom, etc.)

**Content Requirements:**
- Page title: "CATY Workpapers"
- Link canonical CSS: `<link rel="stylesheet" href="../../styles/caty-equity-research.css">`
- Header with back button to ../index.html (evidence index) AND ../../index.html (main index)
- Table with 3 columns: **Document**, **Description**, **Format**
- List all 10 files:
  1. CATY_FDIC_NCO_series.html / .md - "NCO time series from FDIC Call Reports"
  2. CATY_Q3_2025_buyback_analysis.html / .md - "Buyback authorization and share repurchase analysis"
  3. CATY_Q3_2025_normalization_bridge.html / .md - "Q3 2025 normalized earnings bridge"
  4. CET1_headroom_schedule.html / .md - "CET1 capital headroom schedule"
  5. RATING_GUARDRAIL.html / .md - "Rating threshold and publication gate rules"

**File List:**
```bash
ls -1 evidence/workpapers/*.html
```

---

#### 3. `evidence/raw/index.html`
**Location:** `/Users/nirvanchitnis/caty-equity-research-live/evidence/raw/index.html`
**Linked from:** index.html line ~970 ("Browse raw directory")
**Purpose:** 62 SEC EDGAR filings + FDIC data (10-Qs, 8-Ks, XBRL, PDFs)

**Content Requirements:**
- Page title: "CATY Raw Source Filings"
- Link canonical CSS: `<link rel="stylesheet" href="../../styles/caty-equity-research.css">`
- Header with back button
- 5 sections:
  1. **CATY SEC Filings** - list all CATY_*.htm, CATY_*.pdf
  2. **CATY XBRL** - list all CATY_*_xbrl.zip and subdirectories
  3. **Peer SEC Filings** - list all EWBC_*, HAFC_*, WAFD_* subdirectories
  4. **FDIC Data** - list fdic_*.json and fdic_*.csv
  5. **DEF14A Extractions** - link to def14a/runs/

**File List:**
```bash
ls -1 evidence/raw/
```

---

#### 4. `evidence/raw/CATY_2025Q3_8K/index.html`
**Location:** `/Users/nirvanchitnis/caty-equity-research-live/evidence/raw/CATY_2025Q3_8K/index.html`
**Linked from:** index.html line ~935 ("Q3 2025 8-K source extracts")
**Purpose:** 7 XBRL/XSD/HTM files from Q3 8-K

**Content Requirements:**
- Page title: "CATY Q3 2025 8-K (Source Extracts)"
- Link canonical CSS: `<link rel="stylesheet" href="../../../styles/caty-equity-research.css">`
- Header with back button to ../../raw/index.html
- Table listing all 7 files with SEC accession metadata
- Link to SEC EDGAR viewer: https://www.sec.gov/cgi-bin/viewer?action=view&cik=0000700564&accession_number=[accession]

**File List:**
```bash
ls -1 evidence/raw/CATY_2025Q3_8K/
```

---

#### 5. `evidence/primary_sources/index.html`
**Location:** `/Users/nirvanchitnis/caty-equity-research-live/evidence/primary_sources/index.html`
**Linked from:** Individual PDF links in index.html + CATY modules
**Purpose:** 13 earnings presentations, press releases, peer 10-Qs

**Content Requirements:**
- Page title: "CATY Primary Sources"
- Link canonical CSS: `<link rel="stylesheet" href="../../styles/caty-equity-research.css">`
- Header with back button
- 2 sections:
  1. **CATY Earnings Materials** - list all CATY_*.pdf and CATY_*.txt
  2. **Peer 10-Qs (Gzipped HTML)** - list all *.html.gz files with ticker labels

**File List:**
```bash
ls -1 evidence/primary_sources/
```

---

### CRITICAL FIX #2: Update Stale File Reference in Snapshot Test

**File:** `/Users/nirvanchitnis/caty-equity-research-live/scripts/tests/snapshots/reconciliation-dashboard.html`
**Line:** 36
**Current:** `href="analysis/RESIDUAL_INCOME_VALUATION.md"`
**Fix to:** `href="analysis/methodologies/RESIDUAL_INCOME_VALUATION.md"`

**Command:**
```bash
# Find and replace
sed -i '' 's|href="analysis/RESIDUAL_INCOME_VALUATION.md"|href="analysis/methodologies/RESIDUAL_INCOME_VALUATION.md"|g' scripts/tests/snapshots/reconciliation-dashboard.html
```

---

### CRITICAL FIX #3: Regenerate evidence/README.html

**File:** `/Users/nirvanchitnis/caty-equity-research-live/evidence/README.html`
**Issue:** Line 909 references `analysis/rating_policy.md` (old location)
**Fix:** Regenerate from evidence/README.md

**Check if evidence/README.md exists and contains stale reference:**
```bash
grep -n "analysis/rating_policy.md" evidence/README.md
```

**If found, update evidence/README.md first:**
```bash
sed -i '' 's|analysis/rating_policy.md|analysis/methodologies/rating_policy.md|g' evidence/README.md
```

**Then regenerate HTML (if conversion script exists):**
```bash
# Check for conversion script
ls -1 scripts/*convert*.py | grep -i "html\|md"
# Run conversion if found
# If no script, manually update evidence/README.html line 909
```

---

## Validation Steps (You Must Run These)

### 1. Verify all 5 index.html files exist:
```bash
ls -lh evidence/index.html
ls -lh evidence/workpapers/index.html
ls -lh evidence/raw/index.html
ls -lh evidence/raw/CATY_2025Q3_8K/index.html
ls -lh evidence/primary_sources/index.html
```

### 2. Verify stale reference is fixed:
```bash
grep -n "analysis/RESIDUAL_INCOME_VALUATION.md" scripts/tests/snapshots/reconciliation-dashboard.html
# Should find: analysis/methodologies/RESIDUAL_INCOME_VALUATION.md
```

### 3. Verify evidence/README.html is fixed:
```bash
grep -n "analysis/rating_policy.md" evidence/README.html
# Should find: analysis/methodologies/rating_policy.md (if reference exists)
```

### 4. Commit changes:
```bash
git add evidence/*.html evidence/**/index.html scripts/tests/snapshots/reconciliation-dashboard.html
git status
git commit -m "$(cat <<'EOF'
OPERATION STALE FIXES: Restore evidence provenance trail

GitHub Pages directory listings fixed:
- evidence/index.html: Hub for 159 evidence files
- evidence/workpapers/index.html: 10 analytical workpapers
- evidence/raw/index.html: 62 SEC/FDIC source filings
- evidence/raw/CATY_2025Q3_8K/index.html: Q3 8-K extracts
- evidence/primary_sources/index.html: 13 earnings materials

Stale file references fixed:
- scripts/tests/snapshots/reconciliation-dashboard.html: Updated analysis/*.md → analysis/methodologies/*.md
- evidence/README.html: Updated rating_policy.md path (if exists)

All 5 index.html pages use canonical CATY CSS and navigation structure.

Result: Auditors can now browse evidence/ directories. Provenance trail restored.

🤖 Generated with Codex (via Claude Code)
https://claude.com/claude-code

Co-Authored-By: Codex <noreply@anthropic.com>
EOF
)"
```

### 5. Push to live:
```bash
git push origin-live main
```

### 6. Verify live site (wait 60 seconds for GitHub Pages):
```bash
sleep 60
curl -I https://nirvanchitnis-cmyk.github.io/caty-equity-research-live/evidence/
curl -I https://nirvanchitnis-cmyk.github.io/caty-equity-research-live/evidence/workpapers/
curl -I https://nirvanchitnis-cmyk.github.io/caty-equity-research-live/evidence/raw/
curl -I https://nirvanchitnis-cmyk.github.io/caty-equity-research-live/evidence/raw/CATY_2025Q3_8K/
curl -I https://nirvanchitnis-cmyk.github.io/caty-equity-research-live/evidence/primary_sources/
# All should return HTTP 200
```

---

## Template: Evidence Index.html Structure

Use this structure for ALL evidence index pages:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CATY Evidence - [Section Name]</title>
    <link rel="stylesheet" href="[relative-path-to]/styles/caty-equity-research.css">
</head>
<body data-theme="light">
    <!-- Theme Toggle Button (copy from any CATY_*.html) -->
    <button id="theme-toggle" class="theme-toggle" aria-label="Toggle dark mode">
        <!-- SVG icons here -->
    </button>

    <!-- Header -->
    <header>
        <div class="header-content">
            <h1 class="page-title">CATY Evidence</h1>
            <div class="page-subtitle">[Section Name]</div>
            <div class="page-meta">
                <span>CFA Institute Research Challenge</span>
                <span>Evidence Trail & Source Documents</span>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <div class="container">
        <a href="[relative-path]/index.html" class="back-button">← Back to Main Index</a>

        <div class="module-section">
            <h2>[Section Heading]</h2>
            <p>[Description of section]</p>

            <!-- File listing (table or list) -->
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Document</th>
                        <th>Description</th>
                        <th>Format</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><a href="filename.html">filename.html</a></td>
                        <td>Description of document</td>
                        <td>HTML / Markdown</td>
                    </tr>
                    <!-- Repeat for all files -->
                </tbody>
            </table>
        </div>

        <!-- Additional sections as needed -->
    </div>

    <!-- Footer -->
    <footer>
        <p>Evidence index auto-generated | <a href="https://github.com/nirvanchitnis-cmyk/caty-equity-research-live">View Repository</a></p>
    </footer>

    <!-- Theme toggle script (copy from any CATY_*.html) -->
    <script src="[relative-path-to]/scripts/theme-toggle.js"></script>
</body>
</html>
```

---

## Key Requirements

1. **Use canonical CSS** - Link to `styles/caty-equity-research.css` with correct relative path
2. **Match CATY page structure** - Header, container, back button, footer
3. **Theme toggle** - Include button + script for light/dark mode
4. **Descriptive tables** - 3 columns (Document, Description, Format)
5. **Navigation** - Back buttons to parent directory and main index
6. **File lists** - Use `ls -1` commands provided to get actual filenames

---

## Acceptance Criteria

✅ All 5 index.html files exist and use canonical CSS
✅ All evidence directory links return HTTP 200 on live site
✅ Stale reference in snapshot file updated
✅ evidence/README.html regenerated (if needed)
✅ Git commit includes all changes with detailed message
✅ Pushed to origin-live/main
✅ Live site verified via curl (all 5 URLs return 200)

---

## What NOT to Do

❌ Do NOT modify any CATY_*.html files (those are correct)
❌ Do NOT change analysis/methodologies/ file locations (those are correct)
❌ Do NOT use custom CSS or Tailwind defaults (use canonical CSS only)
❌ Do NOT skip validation steps
❌ Do NOT force-push

---

## Questions for Claude

If you encounter issues:
1. **Missing files?** Report which files `ls -1` doesn't find
2. **Unclear structure?** Ask for specific table/section layout
3. **Git conflicts?** Report the conflict before resolving
4. **Validation failures?** Report which curl returned non-200

---

**GOOD LUCK, CODEX. THE AUDIT DEPENDS ON YOU.**

---

**Last Updated:** 2025-10-24
**Handoff From:** Claude (Creative Director)
**Handoff To:** Codex (Execution Specialist)
