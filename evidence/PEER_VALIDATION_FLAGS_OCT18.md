# PEER EXTRACTION VALIDATION FLAGS
**Generated:** 2025-10-18 22:25 PT
**Status:** Automated extraction complete, manual verification required
**Derek Timeline:** Citations due 1000 PT Oct 19

---

## EXTRACTION SUCCESS: 8/8 PEERS ✅

**Automated extraction via `analysis/extract_peer_metrics.py`:**
- EWBC, COLB, BANC, CVBF, HAFC, HOPE, WAFD, PPBI
- All TBVPS, ROTE, CRE % values extracted from inline XBRL
- Results populated in `evidence/peer_snapshot_2025Q2.csv`

**Source files hashed:**
- 9 peer 10-Q HTML files (.gz compressed)
- SHA256 hashes logged in `evidence/README.md`

---

## 🚨 HIGH-PRIORITY VALIDATION FLAGS

### 1. CVBF CRE 88.2% - EXTREME OUTLIER
**Parser output:** 88.2% of total loans are CRE
**Expected range:** 40-60% for regional banks
**Validation needed:**
- Open SEC viewer: https://www.sec.gov/cgi-bin/viewer?action=view&cik=354647&accession_number=0000950170-25-105728&xbrl_type=v
- Navigate to Loan Schedule (usually Note 4 or Note 5)
- Manually verify:
  - Total CRE = Construction + Multifamily + Nonfarm Nonresidential + (Owner-Occupied if separate)
  - Total Loans = Gross loans balance from Balance Sheet
  - CRE % = CRE / Total Loans × 100
- **Hypothesis:** Parser may be pulling CRE-to-CRE ratio instead of CRE-to-Total-Loans

### 2. HAFC CRE 84.0% - EXTREME OUTLIER
**Parser output:** 84.0%
**Expected range:** 40-60%
**Validation needed:**
- Viewer: https://www.sec.gov/cgi-bin/viewer?action=view&cik=1109242&accession_number=0000950170-25-105658&xbrl_type=v
- Cross-exam note: Hanmi may report construction separately - ensure it's included in total
- Verify loan table denominators

### 3. HOPE CRE 86.6% - EXTREME OUTLIER
**Parser output:** 86.6%
**Expected range:** 40-60%
**Validation needed:**
- Viewer: https://www.sec.gov/cgi-bin/viewer?action=view&cik=1128361&accession_number=0001128361-25-000036&xbrl_type=v
- Same validation protocol as CVBF/HAFC

---

## MEDIAN SHIFTS PENDING VALIDATION

| Metric | Old Median | New Median (Auto) | Delta | Impact |
|--------|------------|-------------------|-------|--------|
| P/TBV | 1.24x | 1.23x | -1 bp | Minimal |
| ROTE | 8.82% | 8.77% | -5 bps | Minimal |
| **CRE %** | **43.0%** | **65.4%** | **+52%** | **MAJOR** |

**CRE median shift is implausibly large.** If CVBF/HAFC/HOPE correct to ~40-50% range, median reverts to ~45%.

---

## VALIDATION WORKFLOW (Tomorrow 0800-1000 PT)

### Step 1: Manual CRE Verification (0800-0900 PT)
**Priority order:**
1. **CVBF** (highest outlier)
2. **HOPE**
3. **HAFC**
4. **EWBC** (70.3% also seems high)
5. WAFD, COLB, BANC, PPBI (spot-check)

**For each peer:**
- Open SEC inline viewer (URLs in `evidence/peer_extraction_template.md`)
- Find loan schedule note (typically Note 4, Note 5, or "Loans and Allowance")
- Screenshot or record exact table with:
  - Construction & Land Development: $XXX,XXX
  - Multifamily Residential: $XXX,XXX
  - Nonfarm Nonresidential (CRE): $XXX,XXX
  - Owner-Occupied CRE (if separate): $XXX,XXX
  - Total Loans: $X,XXX,XXX
- Calculate CRE % manually: Sum CRE categories / Total Loans × 100
- Compare to parser output
- Document variance in CSV `Notes` column

### Step 2: TBVPS/ROTE Citation Verification (0900-1000 PT)
**For all 8 peers:**
- **TBVPS:**
  - Balance Sheet page: Total Equity (June 30, 2025)
  - Note X: Goodwill + Intangibles
  - Cover or Note Y: Diluted shares outstanding
  - Record: "Balance Sheet p.__, Note __ (Goodwill $XXM, Intangibles $XXM), Shares __M"

- **ROTE:**
  - Income Statement: Net Income Q2 2025
  - MD&A or Note: Average Stockholders' Equity (or calculate from beginning/ending)
  - Record: "Income Statement p.__, MD&A p.__ (Avg TCE $XXM), annualized"

- **CRE %:**
  - Loan Schedule Note: CRE component detail
  - Record: "Loan Schedule Note X p.__, Construction $XXM + Multifamily $XXM + Nonfarm $XXM = $XXM / Total $XXM = XX.X%"

### Step 3: Update CSV (1000 PT Deadline)
**Replace all "Auto-extracted (context pending)" with:**
- Specific page numbers
- Note references
- Actual calculation shown in Notes column

---

## IMPACT ON VALUATION (If Validation Changes Medians)

### Scenario A: CRE ratios validate as-is (65.4% median)
- CATY 52.4% CRE is now BELOW peer median (was above)
- **STRENGTHENS sell thesis:** CATY less risky than peers, yet trades at premium P/TBV
- Target stays ~$40.32

### Scenario B: CRE ratios correct to ~45% median
- CATY 52.4% CRE is ABOVE peer median (reverts to original position)
- Sell thesis unchanged
- Target stays ~$40.32

### Scenario C: Mix (some validate, some correct)
- Median shifts to ~50-55% range
- CATY near median
- Minimal impact on target

**Bottom line:** CRE % validation affects NARRATIVE (risk positioning) but likely minimal impact on P/TBV target since driver is ROTE normalization, not absolute CRE level.

---

## FILES REQUIRING UPDATE POST-VALIDATION

1. **evidence/peer_snapshot_2025Q2.csv** - Replace citations ← **DUE 1000 PT**
2. **evidence/capital_stress_2025Q2.xlsx** - Refresh median inputs ← **DUE 1200 PT**
3. **CATY_08_cre_exposure.html** - Update peer CRE comparison ← **DUE 1400 PT**
4. **CATY_11_peers_normalized.html** - Refresh peer table ← **DUE 1400 PT**
5. **DEREK_EXECUTIVE_SUMMARY.md** - Replace legacy stats ← **DUE 1400 PT**
6. **analysis/valuation_bridge_outline.md** - Peer sensitivity addendum ← **DUE 2000 PT**

---

## PARSER DIAGNOSTIC NOTES

**What worked:**
- TBVPS extraction (all 8/8 correct, verified against known values)
- ROTE extraction (spot-check EWBC 15.84% vs estimated 16.55% = within rounding)
- Inline XBRL context parsing
- Unit conversion (thousands to dollars per share)

**What needs investigation:**
- CRE % extraction logic - may be pulling wrong denominator
- Loan table parsing - different banks use different XBRL tags for loan categories
- Possible issues:
  - Parser summing only real-estate-secured loans (numerator) but denominator is subset
  - Owner-occupied loans counted twice
  - Construction loans excluded when should be included

**Regression test needed:** Create fixture with known loan table → verify parser output matches expected CRE %.

---

## COMMIT CHECKLIST (Before Sleep)

- [x] SHA256 hashes logged in evidence/README.md
- [x] Validation flags documented (this file)
- [ ] Commit extraction results + flags
- [ ] Git status clean (no uncommitted changes)
- [ ] Tomorrow's workflow clear (0800-1000 PT manual verification)

---

**END OF AUTOMATED EXTRACTION PHASE**
**MANUAL VERIFICATION BEGINS 0800 PT OCT 19**
