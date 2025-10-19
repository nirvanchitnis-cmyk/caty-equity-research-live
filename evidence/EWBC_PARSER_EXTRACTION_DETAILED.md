# EWBC Detailed Parser Extraction Report
**Generated:** 2025-10-18 23:35 PT
**Source:** evidence/primary_sources/EWBC_2025-06-30_10Q.html (6.9MB)
**Parser:** analysis/extract_peer_metrics.py
**Status:** AUTO-EXTRACTED - Requires manual verification tomorrow 0830 PT

---

## Parser Output Summary

```
TBVPS: $56.13
ROTE: 15.84% (annualized from Q2)
CRE: 70.3% of total loans
```

**Verification Required:**
- ⚠️ TBVPS components (equity, goodwill, intangibles, shares)
- ⚠️ ROTE components (net income, average TCE)
- 🚨 CRE ratio (70.3% is high - needs manual table inspection)

---

## TBVPS Calculation ($56.13)

### Components Extracted:

**Total Stockholders' Equity (June 30, 2025):**
- **Amount:** $7,925,000,000 (7.925B)
- **XBRL Context:** c-3 (instant: 2025-06-30)
- **Tag:** us-gaap:StockholdersEquity
- **Verification needed:** Consolidated Balance Sheet, June 30, 2025 column

**Goodwill:**
- **Amount:** $188,930,000 (188.9M)
- **XBRL Context:** c-3
- **Tag:** us-gaap:Goodwill
- **Verification needed:** Note 9 or "Goodwill and Other Intangible Assets"

**Other Intangible Assets:**
- **Amount:** $0 (or de minimis)
- **XBRL Context:** c-3
- **Tag:** us-gaap:IntangibleAssetsNetExcludingGoodwill
- **Verification needed:** Same note as goodwill

**Tangible Common Equity (TCE):**
- **Calculation:** $7,925M - $188.9M - $0M = $7,736.1M
- **Parser result:** $7,736,070,000

**Diluted Shares Outstanding:**
- **Amount:** 137,821,766 shares (137.8M)
- **XBRL Context:** c-2 (instant: 2025-07-31 - latest reported)
- **Tag:** us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding
- **Verification needed:** Cover page or Note on earnings per share

**TBVPS Calculation:**
```
TCE / Shares = $7,736,070,000 / 137,821,766 = $56.13
```

**Manual Verification Steps:**
1. Open SEC viewer: https://www.sec.gov/cgi-bin/viewer?action=view&cik=1069157&accession_number=0001069157-25-000096&xbrl_type=v
2. Navigate to Consolidated Balance Sheets
3. Find June 30, 2025 column
4. Verify: Total stockholders' equity = $7,925M
5. Navigate to Note 9 (Goodwill and Intangibles)
6. Verify: Goodwill = $188.9M, Intangibles = $0M
7. Check cover page or EPS note
8. Verify: Diluted shares = 137.8M
9. Calculate: ($7,925M - $188.9M) / 137.8M = $56.13 ✓

---

## ROTE Calculation (15.84% annualized)

### Components Extracted:

**Net Income (Q2 2025):**
- **Amount:** $310,253,000 (310.3M quarterly)
- **XBRL Context:** c-5 (duration: 2025-04-01 to 2025-06-30)
- **Tag:** us-gaap:NetIncomeLoss
- **Verification needed:** Consolidated Statements of Income, Q2 2025 column

**Average Tangible Common Equity:**
- **Beginning TCE (March 31, 2025):** $7,929,465,000
  - Equity: $8,118M (context c-35)
  - Less Goodwill: $188.9M (context c-35)
  - Less Intangibles: $0M
- **Ending TCE (June 30, 2025):** $7,736,070,000 (calculated above)
- **Average TCE:** ($7,929.5M + $7,736.1M) / 2 = $7,832,767,500

**ROTE Calculation:**
```
Annualized NI = $310.3M × 4 = $1,241.2M
ROTE = $1,241.2M / $7,832.8M = 15.84%
```

**Parser Output:** 0.1584385... (15.84%)

**Manual Verification Steps:**
1. Consolidated Statements of Income → Q2 2025 column
2. Verify: Net income = $310.3M
3. MD&A section → Search for "average stockholders' equity" or "average tangible common equity"
4. If disclosed: Verify average TCE = $7,833M (approximately)
5. If not disclosed: Calculate from beginning/ending equity minus intangibles
6. Calculate: ($310.3M × 4) / $7,833M × 100 = 15.84% ✓

---

## CRE Ratio Calculation (70.3%) 🚨 FLAGGED

### Components Extracted:

**Total Loans:**
- **Amount:** $26,448,000,000 (26.448B)
- **XBRL Context:** c-3
- **Tag:** Likely us-gaap:LoansAndLeasesReceivableNetReportedAmount or similar
- **Verification needed:** Consolidated Balance Sheet OR Loan Schedule Note

**Total CRE:**
- **Amount:** $18,582,000,000 (18.582B)
- **XBRL Context:** Various (loan category contexts)
- **Tags:** Sum of construction, multifamily, nonfarm nonresidential, etc.
- **Verification needed:** Loan Schedule footnote (typically Note 4 or 5)

**CRE Ratio:**
```
CRE / Total Loans = $18,582M / $26,448M = 70.26% → 70.3%
```

**Parser Output:** 0.7025862... (70.3%)

**🚨 VERIFICATION CRITICAL:**
This ratio seems high. Typical regional banks have CRE 40-60% of loans.

**Possible Issues:**
1. **Denominator error:** Parser may have used gross loans before allowances instead of net loans
2. **Numerator error:** Parser may be double-counting categories (e.g., owner-occupied + non-owner-occupied)
3. **Category inclusion:** Parser may have included loans that aren't technically CRE
4. **EWBC is actually a CRE specialist:** 70.3% could be accurate for their business model

**Manual Verification Steps (CRITICAL):**
1. Open SEC viewer
2. Navigate to Loan Schedule (usually Note 4 or Note 5)
3. Find table showing loan categories
4. Look for these rows:
   - Construction and land development
   - Multifamily residential (5+ units)
   - Nonfarm nonresidential (commercial real estate)
   - Owner-occupied CRE (if separately disclosed)
5. **Sum CRE categories** (record each line item)
6. Find "Total loans" row (verify if gross or net of allowance)
7. **Calculate:** CRE sum / Total loans × 100
8. **Compare to 70.3%**
9. If materially different (>2%), document which categories were missed/added
10. Update CSV with verified figure

**Expected Manual Result:**
- If verified: CRE ~70% → EWBC is CRE-focused bank (not a red flag, just their model)
- If corrected: CRE ~45-55% → Parser denominator error (likely used gross instead of net)

---

## XBRL Context Reference

**Key Context IDs Used:**
- `c-1`: Duration 2025-01-01 to 2025-06-30 (YTD)
- `c-3`: Instant 2025-06-30 (current quarter end)
- `c-4`: Instant 2024-12-31 (prior year end)
- `c-5`: Duration 2025-04-01 to 2025-06-30 (Q2 only)
- `c-35`: Instant 2025-03-31 (Q1 end, for average calc)

---

## Manual Verification Checklist (For Tomorrow 0830 PT)

### TBVPS ($56.13):
- [ ] Balance Sheet June 30, 2025: Total equity = $7,925M
- [ ] Note 9 (Goodwill): Goodwill = $188.9M
- [ ] Note 9 (Intangibles): Intangibles = $0M or de minimis
- [ ] Cover/EPS Note: Diluted shares = 137.8M
- [ ] Calculation: ($7,925M - $188.9M) / 137.8M = $56.13
- [ ] **Citation:** "Balance Sheet p.__, Note 9 p.__, Shares: Cover"

### ROTE (15.84%):
- [ ] Income Statement Q2: Net income = $310.3M
- [ ] MD&A or equity note: Average TCE disclosed or calculated
- [ ] Calculation: ($310.3M × 4) / $7,833M = 15.84%
- [ ] **Citation:** "Income Statement p.__, MD&A p.__ (Avg TCE)"

### CRE % (70.3% - CRITICAL):
- [ ] Loan Schedule Note: Find all CRE categories
- [ ] Sum: Construction + Multifamily + Nonfarm Nonres + Other CRE = $__.__B
- [ ] Total loans denominator: $26.4B (verify gross vs net)
- [ ] Calculation: CRE sum / Total × 100 = __.__%
- [ ] **Citation:** "Loan Schedule Note __ p.__, [Construction $XM + Multifamily $YM + ...] / Total $ZM"
- [ ] If verified 70.3%: Add note "EWBC CRE-focused business model"
- [ ] If materially different: Document correction and reason

---

## Next Actions (0830 PT Oct 19)

1. **Open SEC viewer** (requires browser - Nirvan or Derek)
2. **Verify all three metrics** using checklist above
3. **Update evidence/peer_snapshot_2025Q2.csv:**
   - Replace "Auto-extracted (context pending)" with actual citations
   - Update values if corrections needed
   - Add detailed notes in Notes column
4. **Take screenshots** of key tables and save to evidence/peer_tables/EWBC/
5. **Log in evidence/README.md** with timestamp and verification status

---

**BOTTOM LINE:**
Parser extracted values from XBRL with specific context IDs. Manual verification will confirm or correct these figures. CRE ratio of 70.3% is the highest priority to verify given it's above typical peer range.

**—Auto-generated 2025-10-18 23:40 PT**
**Manual verification required before use in valuation**
