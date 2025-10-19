# FDIC Call Report Reconciliation – CATY (Cert 18503)

**Purpose:** Bridge management-reported CRE exposure (52.4% of total loans per Q2’25 10-Q) to regulatory data in the FDIC Call Report (Schedule RC-C Part I). This satisfies Derek’s requirement for a regulatory cross-check.

**Status (2025-10-18 21:55 PT):** Framework drafted. Data pulls scheduled for 2025-10-19 10:00–11:00 PT once browser access to FDIC UBPR or SDI portal is available.

---

## Data Sources Required
- FDIC Statistics on Depository Institutions (SDI) – Cathay Bank (RSSD 476401).
- Schedule RC-C Part I (Loans and Leases) fields:
  - RCON1410 – Loans secured by real estate: Construction, land development, and other land loans.
  - RCON1415 – Loans secured by real estate: Secured by nonfarm nonresidential properties (owner-occupied proxy).
  - RCON1417 – Loans secured by real estate: Multifamily (5 or more) residential properties.
  - RCON1460 – Loans secured by real estate: Commercial and industrial loans secured by real estate (if separately disclosed).
  - RCON1400 – Total loans and leases, net of unearned income.
  - RCON5367 – Total commercial real estate loans (if available in SDI download).

---

## Mapping Table Template (to be populated 2025-10-19)

| FDIC Code | FDIC Description | Mgmt Category (Q2’25 deck) | 2Q25 Balance (FDIC) | 2Q25 Balance (Mgmt) | Recon Notes |
|-----------|-----------------|-----------------------------|---------------------|---------------------|-------------|
| RCON1410  | Construction, land development, and other land loans | Included in “Construction” (1.52% of total loans) | _TBD_ | 0.30B | Pending pull |
| RCON1415  | Secured by nonfarm nonresidential properties | Maps to CRE: Office, Retail, Industrial, etc. | _TBD_ | 10.06B | Need owner-occupied breakdown |
| RCON1417  | Multifamily (5+ units) | Maps to Residential CRE (53% LTV) | _TBD_ | 3.53B | Verify against presentation |
| RCON1418  | Secured by 1–4 family residential properties | Excluded from CRE | _TBD_ | 5.72B | Should reconcile to residential mortgage bucket |
| RCON1420  | Loans to finance agricultural production and other loans to farmers | Non-CRE | _TBD_ | N/A | Confirm immaterial |
| RCON1400  | Total loans and leases | Managerial total (19.785B) | _TBD_ | 19.785B | Ensure balances tie |

_TBD_ values will be populated once SDI extracts are downloaded. Recon notes will capture any differences due to net vs gross classifications or inclusion/exclusion of owner-occupied CRE.

---

## Next Steps
1. **Download SDI CSV:** `https://cdr.ffiec.gov/public/ManageFacsimiles.aspx` (requires manual export due to login gates).
2. **Populate Table:** Enter FDIC balances (in $M) and compare to management figures documented in `CATY_08_cre_exposure.html`.
3. **Explain Variances:** Document whether differences stem from owner-occupied loans, held-for-sale adjustments, or netting conventions.
4. **Update Evidence README:** Log the reconciliation deliverable with timestamp once complete.

Deliverable deadline: **2025-10-19 12:00 PT** (per Derek timeline).
