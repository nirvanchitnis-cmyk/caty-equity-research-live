# Peer Extraction Workbook – Manual Pull Instructions

**Objective:** Produce audit-grade TBVPS, ROTE, and CRE % inputs for `evidence/peer_snapshot_2025Q2.csv`. Each peer requires (a) raw values with filing citations, and (b) arithmetic notes proving the calculation path.

**How to use this template**
- Open each SEC inline viewer in a browser (viewer URL provided below).
- Capture screenshots or copy exact figures with line labels, statement names, and column dates.
- Record all data points and the math inside the CSV `Notes` column.
- Update the new citation columns (`TBVPS_Citation`, `ROTE_Citation`, `CRE_Citation`) with “Statement/Page – Note – Column Date” references.

---

## EWBC – East West Bancorp
- **Viewer URL:** https://www.sec.gov/cgi-bin/viewer?action=view&cik=1069157&accession_number=0001069157-25-000096&xbrl_type=v
- **TBVPS Steps**
  1. Consolidated Balance Sheets → “Total stockholders’ equity” (June 30, 2025 column).
  2. Same table → “Goodwill” and “Other intangible assets”.
  3. Cover page → “Shares outstanding, diluted” (or Note 1 if disclosed elsewhere).
  4. Calculation: (Equity – Goodwill – Intangibles) ÷ diluted shares.
- **ROTE Steps**
  1. Consolidated Statements of Income → “Net income”.
  2. MD&A section → “Average tangible common equity” (if unavailable, compute from average equity minus average intangibles).
  3. Annualize if the filing reports quarterly figures: ROTE = (Q2 net income × 4) ÷ average tangible equity.
- **CRE % Steps**
  1. Loans and Leases footnote (generally Note 4 or 5) → “Loans secured by real estate” detail.
  2. Identify commercial real estate total; include construction if management classifies as CRE.
  3. Divide CRE total by gross loans balance from balance sheet.

## COLB – Columbia Banking System
- **Viewer URL:** https://www.sec.gov/cgi-bin/viewer?action=view&cik=887343&accession_number=0000887343-25-000233&xbrl_type=v
- Repeat TBVPS, ROTE, CRE workflow above. Note that Columbia may provide average shares in the equity footnote; capture whichever is used in TBVPS calculation and document context IDs if available.

## BANC – Banc of California
- **Viewer URL:** https://www.sec.gov/cgi-bin/viewer?action=view&cik=1169770&accession_number=0001169770-25-000029&xbrl_type=v
- Ensure construction and multi-family loans are treated consistently with management guidance when computing CRE %.

## CVBF – CVB Financial Corp
- **Viewer URL:** https://www.sec.gov/cgi-bin/viewer?action=view&cik=354647&accession_number=0000950170-25-105728&xbrl_type=v
- Highlight whether owner-occupied loans are disclosed separately; note any mapping assumptions in the CSV `Notes`.

## HAFC – Hanmi Financial Corp
- **Viewer URL:** https://www.sec.gov/cgi-bin/viewer?action=view&cik=1109242&accession_number=0000950170-25-105658&xbrl_type=v
- Pay attention to construction balances; Derek wants to know if they were blended into CRE. Document explicitly.

## HOPE – Hope Bancorp
- **Viewer URL:** https://www.sec.gov/cgi-bin/viewer?action=view&cik=1128361&accession_number=0001128361-25-000036&xbrl_type=v
- Capture any average tangible equity disclosure in MD&A for ROTE and cite the section header.

## WAFD – Washington Federal
- **Viewer URL:** https://www.sec.gov/cgi-bin/viewer?action=view&cik=936528&accession_number=0000936528-25-000086&xbrl_type=v
- If WAFD segregates CRE by collateral code (owner-occupied vs investor), record both and note the aggregation choice in the CSV.

## PPBI – Pacific Premier Bancorp
- **Viewer URLs:**  
  - Q2 2025: https://www.sec.gov/cgi-bin/viewer?action=view&cik=1028918&accession_number=0001028918-25-000086&xbrl_type=v  
  - Q1 2025 (for fiscal calendar alignment): https://www.sec.gov/cgi-bin/viewer?action=view&cik=1028918&accession_number=0001013237-25-000070&xbrl_type=v
- Confirm fiscal quarter end dates; note any need to annualize or adjust averages.

---

### CSV Update Checklist (per peer)
1. `TBVPS` value matches the verified calculation (equity – intangibles ÷ diluted shares).
2. `TBVPS_Citation` includes statement name, column date, and note reference.
3. `ROTE` and `ROTE_Citation` document net income source, average tangible equity, and annualization.
4. `CRE_Pct` ties to loan footnote totals; `CRE_Citation` lists note/page and describes included categories.
5. `Notes` field records the actual arithmetic (with units in millions where applicable).

Document all deviations or missing disclosures. If any peer lacks the data, mark the CSV row as “DATA GAP” and describe the unlock path (e.g., IR call, supplemental deck).
