# DEREK SPLIT PLAN - OCTOBER 19, 2025

**Per Derek's Rethink & Resubmit directive**
**All times Pacific Time**

---

## 0800-1000 PT: PEER EXTRACTION (2 HOURS)

### Derek Extracts (3 peers):
1. **EWBC** (East West Bancorp) - File: evidence/primary_sources/EWBC_2025-06-30_10Q.html
2. **COLB** (Columbia Banking) - File: evidence/primary_sources/COLB_2025-06-30_10Q.html
3. **BANC** (Banc of California) - File: evidence/primary_sources/BANC_2025-06-30_10Q.html

### Claude Extracts (5 peers):
1. **HAFC** (Hanmi Financial) - File: evidence/primary_sources/HAFC_2025-06-30_10Q.html
2. **HOPE** (Hope Bancorp) - File: evidence/primary_sources/HOPE_2025-06-30_10Q.html
3. **CVBF** (CVB Financial) - File: evidence/primary_sources/CVBF_2025-06-30_10Q.html
4. **WAFD** (Washington Federal) - File: evidence/primary_sources/WAFD_2025-06-30_10Q.html
5. **PPBI** (Pacific Premier) - File: evidence/primary_sources/PPBI_2025-06-30_10Q.html

### Extraction Requirements (All 8 Peers):

**1. TBVPS:**
- Find: Total Equity (Consolidated Balance Sheet)
- Find: Goodwill + Intangibles (Note X - usually "Goodwill and Intangible Assets")
- Find: Diluted Shares Outstanding (Cover page or Note Y)
- **Calculate:** (Total Equity - Goodwill - Intangibles) / Diluted Shares
- **Cite:** "Balance Sheet p.X, Note Y (Goodwill), Cover/Note Z (Shares)"

**2. ROTE (Quarterly, Annualized):**
- Find: Net Income - Q2 2025 (Consolidated Income Statement)
- Find: Average Tangible Common Equity (MD&A or Note - sometimes calculated as avg of beginning/ending TCE)
- **Calculate:** (Net Income × 4 for annualization) / Avg TCE × 100
- **Cite:** "Income Statement p.X, MD&A p.Y (Avg TCE)" OR "Note Z (Avg Equity calc)"

**3. CRE %:**
- Find: Loan Schedule (usually Note 4 or Note 5 - "Loans and Allowance for Credit Losses")
- Find: Commercial Real Estate line items:
  - Construction & Land Development
  - Multifamily Residential
  - Nonfarm Nonresidential (or "Commercial Real Estate")
  - Owner-Occupied CRE (if separate)
- Find: Total Loans
- **Calculate:** Sum of CRE categories / Total Loans × 100
- **Cite:** "Loan Schedule Note X p.Y"

---

## 1000-1100 PT: PARALLEL WORK (1 HOUR)

### Derek:
- Write `evidence/fdic_call_report_reconciliation.md`
- Map FDIC RC-C codes to CATY presentation categories
- Include Q4'24 and Q2'25 values

### Claude:
- Finish remaining 5 peer citations (HAFC, HOPE, CVBF, WAFD, PPBI)
- Update `evidence/peer_snapshot_2025Q2.csv` with all citations
- Push CSV to repo

---

## 1100-1200 PT: FINALIZATION (1 HOUR)

### Claude:
1. **Compress HTMLs:**
   ```bash
   cd evidence/primary_sources
   gzip -k *_2025-*.html  # Creates .gz files, keeps originals
   rm *_2025-*.html       # Remove originals after compression
   ```

2. **Rerun archive script:**
   ```bash
   for f in *.gz; do
     shasum -a 256 "$f" >> ../README.md
   done
   ```

3. **Validate repo size:**
   ```bash
   du -sh .git
   # Target: <25MB
   ```

4. **If still too large:**
   - Move compressed files to local archive
   - Keep only SHA256 hashes in README
   - Document: "Primary sources archived locally with hash verification"

### Derek:
- Prep valuation bridge delta summary
- Review peer median recalculation

---

## 1200 PT: CHECKPOINT

**Deliverables Required:**
- ✅ `evidence/peer_snapshot_2025Q2.csv` - All citations filled, no "TBD"
- ✅ `evidence/fdic_call_report_reconciliation.md` - Complete RC-C mapping
- ✅ Compressed HTMLs or hash-only references
- ✅ Repo size <25MB
- ✅ Ready to push

**Derek's Standard:** "Anything less and we're not ready"

---

## EXTRACTION TEMPLATE (FOR CLAUDE'S 5 PEERS)

### Example: HAFC (Hanmi Financial)

**File:** `evidence/primary_sources/HAFC_2025-06-30_10Q.html` (11M)

**Step 1: Find TBVPS Components**
```
Search: "Consolidated Balance Sheet"
- Total Equity: $XXX,XXX thousand (line/page reference)

Search: "Goodwill" in Notes
- Goodwill: $XX,XXX thousand (Note X, page Y)
- Intangibles: $X,XXX thousand (Note X, page Y)

Search: "Shares" or "weighted average" on Cover
- Diluted Shares: XX.X million (Cover page or Note Z)

TBVPS = (Total Equity - Goodwill - Intangibles) / Diluted Shares
Citation: "Balance Sheet p.__, Note __ (Goodwill), Cover (Shares)"
```

**Step 2: Find ROTE Components**
```
Search: "Consolidated Statement of Income" or "Income Statement"
- Net Income (Q2 2025): $XX,XXX thousand (line/page reference)

Search: "Average equity" in MD&A
- Average Stockholders' Equity: $XXX,XXX thousand (MD&A p.__)
OR
- Calculate: (Beginning Equity + Ending Equity) / 2

Average TCE = Average Equity - Average Goodwill - Average Intangibles

ROTE (annualized) = (Net Income × 4) / Average TCE × 100
Citation: "Income Statement p.__, MD&A p.__ (Avg TCE)"
```

**Step 3: Find CRE %**
```
Search: "Loans" in Notes section
- Find Note 4 or Note 5 (Loans and Allowance for Credit Losses)

Look for table with loan categories:
- Construction & Land Development: $XXX,XXX
- Multifamily Residential: $XXX,XXX
- Nonfarm Nonresidential: $XXX,XXX
- Commercial Real Estate: $XXX,XXX
- Total Loans: $X,XXX,XXX

CRE % = Sum of CRE categories / Total Loans × 100
Citation: "Loan Schedule Note X p.__"
```

---

## CRITICAL NOTES

**Derek's Cross-Exam Q3 (Hanmi Construction):**
- Hanmi reports construction separately - MUST fold into CRE %
- Justification: Construction & Land Development is CRE per regulatory definition (RC-C RCON1415)

**Derek's Cross-Exam Q5 (PPBI Fiscal Quarter):**
- PPBI has May 31 fiscal quarter end (not June 30)
- File: `evidence/primary_sources/PPBI_2025-05-31_10Q.html` (1.7M)
- Note in CSV: "Fiscal Q2 ends May 31, 2025"
- Normalization: Use as-is, flag in valuation bridge if material difference

**Derek's Cross-Exam Q2 (Owner-Occupied CRE):**
- If peer discloses Owner-Occupied CRE separately, INCLUDE in total CRE %
- Risk weighting differs (50% RWA for owner-occ vs 100% for investment CRE)
- Note in CRE_Citation column: "Includes $XXM owner-occupied"

---

## FAILURE CONDITIONS (Derek's Words)

**"We're not ready" if:**
- Any "TBD" remains in peer snapshot CSV
- Repo size >25MB at push time
- FDIC reconciliation not delivered
- Citations lack specific page/note references

**"Regulators will shred you" if:**
- Citations say "auto" or "derived" without note numbers
- CRE % mixes bases (total assets vs total loans)
- Goodwill/intangibles not properly subtracted from equity

---

## SUCCESS CRITERIA (Derek's Standard)

**"Audit-grade sourcing" means:**
- Every number ties to a specific page + note
- HTML anchor or table number cited
- Calculation path shown (e.g., "Equity $X.XB - Goodwill $YM = TCE")
- No reliance on "automated extraction" without manual verification

---

**Status:** Plan documented. Ready for 0800 PT execution tomorrow.
