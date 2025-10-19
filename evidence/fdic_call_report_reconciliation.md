# FDIC Call Report Reconciliation - CATY Q2 2025

**Purpose:** Reconcile CATY management CRE disclosure (52.4% of total loans) with FDIC RC-C schedule  
**As of:** June 30, 2025  
**FDIC Cert:** 18503 (Cathay Bank)

## Executive Summary

**Management reported CRE:** 52.4% of total loans ($10,363M / $19,785M)  
**FDIC RC-C CRE codes:** _IN PROGRESS_ (data extraction started 02:50 PT Oct 19)

---

## Mapping Table

| FDIC Code | RC-C Description | Management Category | Q2'25 FDIC ($M) | Q2'25 Mgmt ($M) | Delta | Notes |
|-----------|------------------|---------------------|-----------------|-----------------|-------|-------|
| RCON1410 | Construction & land development | Construction | _TBD_ | $157.5 | _TBD_ | Extracting from SDI |
| RCON1415 | Nonfarm nonresidential | Office + Retail + Industrial + Warehouse + Other | _TBD_ | $6,631.8 | _TBD_ | Core CRE bucket |
| RCON1420 | Multifamily (5+ units) | Residential CRE | _TBD_ | $3,573.5 | _TBD_ | Excludes 1-4 family |
| RCON1400 | Total loans & leases (gross) | Total loans | _TBD_ | $19,785.0 | _TBD_ | Denominator |

**Target CRE sum:** $10,362.8M (Construction + Nonfarm nonres + Multifamily)  
**Target ratio:** 52.4% ($10,362.8M / $19,785.0M)

---

## Data Sources

### Management Disclosure
- **Source:** CATY Q2 2025 10-Q, Note 4 (Loans), p.19
- **Date:** June 30, 2025
- **URL:** https://www.sec.gov/Archives/edgar/data/0000861842/000143774925025772/caty20250630_10q.htm

### FDIC Call Report
- **Source:** FDIC SDI (Structure View)
- **Institution:** Cathay Bank (FDIC Cert 18503, RSSD ID 195135)
- **Schedule:** RC-C (Loans and Lease Financing Receivables)
- **Report Date:** June 30, 2025
- **Access:** https://banks.data.fdic.gov/bankfind-suite/financials (manual extraction required)

---

## Extraction Status

**Started:** October 19, 2025, 02:50 PT  
**Due:** 11:00 PT Oct 19 (Derek deadline)

**Next steps:**
1. Access FDIC SDI portal (browser-based, cannot automate from terminal)
2. Search for Cert 18503 (Cathay Bank)
3. Navigate to Financial Performance → Call Report Data → Schedule RC-C
4. Extract RCON1410, RCON1415, RCON1420, RCON1400 for 2025-06-30
5. Populate mapping table above
6. Calculate: (RCON1410 + RCON1415 + RCON1420) / RCON1400 × 100
7. Compare to management 52.4%
8. Document any variance > 1%

---

## Expected Outcome

**If FDIC ≈ Management (within 1%):**  
Confirms management disclosure is consistent with regulatory reporting. No adjustment required.

**If FDIC ≠ Management (variance > 1%):**  
Document variance, investigate cause (e.g., timing, classification differences), and determine which figure to use for credit analysis.

---

## Pending

- [ ] FDIC RC-C data extraction (in progress)
- [ ] Populate mapping table
- [ ] Calculate reconciliation
- [ ] Document variance (if any)
- [ ] Update evidence/README.md with completion timestamp

**Status:** _IN PROGRESS as of 02:50 PT Oct 19_

---

**Generated:** 2025-10-19 02:50 PT  
**Authority:** Claude (Equity Research Team)  
**Completion target:** 11:00 PT Oct 19
