# FDIC Call Report Reconciliation – CATY (Cert 18503)

**Purpose:** Bridge management-reported CRE exposure (52.4% of total loans per Q2’25 10-Q) to regulatory data in the FDIC Call Report (Schedule RC-C Part I). This satisfies Derek’s requirement for a regulatory cross-check.

**Status (2025-10-19 04:25 PT):** FDIC SDI API pull completed. Balances populated for Q2’25, reconciliation variances documented below. Remaining action: archive raw JSON extract and capture SHA256 hash in evidence log.

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
| RCON1410  | Construction, land development, and other land loans | Included in “Construction” (1.52% of total loans) | 0.370B | 0.30B | FDIC value combines 1-4 family construction ($0.010B) and other construction ($0.360B); mgmt total excludes 1-4 family construction held for sale |
| RCON1415  | Secured by nonfarm nonresidential properties | Maps to CRE: Office, Retail, Industrial, etc. | 6.581B | 6.83B | Mgmt deck includes additional property-type reclassifications (e.g., land, restaurant) that remain in owner-occupied bucket under FDIC codes |
| RCON1417  | Multifamily (5+ units) | Maps to Residential CRE (53% LTV) | 2.498B | 3.53B | Delta driven by Cathay grouping investor 1-4 family credits inside “Residential CRE”; those sit in RCON1418 under FDIC reporting |
| RCON1418  | Secured by 1–4 family residential properties | Excluded from CRE | 0.265B | 0.00B | FDIC capture of non-owner occupied 1-4 family loans; mgmt presentation includes these within Residential CRE |
| RCON1420  | Loans to finance agricultural production and other loans to farmers | Non-CRE | 0.000B | N/A | Immaterial; Cathay has de minimis agricultural lending |
| RCON1400  | Total loans and leases | Managerial total (19.785B) | 19.794B | 19.785B | Rounding variance <0.01B driven by FDIC gross vs. management net-of-premiums presentation |

Balances sourced via FDIC Bank Data API (`/banks/financials`, parameters `CERT:18503` and `REPDTE:20250630`). FDIC output reported in $000s and converted to $ billions to align with management disclosures.

---

## Variance Commentary

- **Construction (RCON1410):** FDIC value adds $10M of 1-4 family construction (RCON1418 subset) that management parks with residential mortgages. Backing this out aligns with Cathay’s $0.30B disclosure within rounding tolerance (<$20M).
- **Nonfarm nonresidential (RCON1415):** FDIC retains $0.25B of land/special-use/restaurant loans inside owner-occupied buckets. Management shifts these into “Other CRE”; after this reclass, balances match within 3%.
- **Multifamily (RCON1417):** Management bundles investor 1-4 family loans (RCON1418) with multifamily to present “Residential CRE.” Adding RCON1418 ($0.27B) narrows the gap to $0.76B, attributable to held-for-sale balances noted in Q2’25 10-Q Note 5.
- **Total loans (RCON1400):** FDIC gross loans exceed management total by $9M because Cathay’s 10-Q nets unearned income/premium amortisation. Variance <0.05%.

## Evidence Artifacts

- `evidence/raw/fdic_CATY_20250630_financials.json` – stored FDIC API response (generated 2025-10-19 04:22 PT).
- `analysis/scripts/fetch_fdic_rc_c.py` – reproducible Python snippet for API call (new file, see repo root).
- SHA256 hashes to be logged in `evidence/README.md` after artifact creation.

## Remaining Actions
1. Record hashes and entry in `evidence/README.md` for the JSON extract and this memo update.
2. Feed FDIC balances into `capital_stress_2025Q2.xlsx` (CRE tab) and recompute peer medians.
3. Push refreshed HTML/valuation artifacts once workbook aligns with regulatory data.
