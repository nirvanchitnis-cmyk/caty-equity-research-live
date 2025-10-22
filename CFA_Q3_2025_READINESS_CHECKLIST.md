## CFA Board Readiness Checklist – Q3 2025 Refresh

| Item | Status | Evidence / Reference |
| --- | --- | --- |
| Form 8-K Exhibit 99.1 (Oct 21 2025) archived in `evidence/raw/CATY_2025Q3_10Q_xbrl/` | ✅ | `git ls evidence/raw/CATY_2025Q3_10Q_xbrl` |
| Automation pipeline re-run (`scripts/update_all_data.py`) post 8-K ingestion | ✅ | `logs/automation_run.log` entry 2025-10-22 02:34 UTC |
| Static site rebuilt (`scripts/build_site.py`) after data refresh | ✅ | Build log + latest timestamps on HTML modules |
| Index valuation cards show Q3 metrics (Wilson $48.70, IRC $50.97, Regression $54.71) | ✅ | `index.html` |
| Module 01 (Company Profile) market snapshot updated to Q3 price, shares, TBVPS | ✅ | `CATY_01_company_profile.html` / `data/caty01_company_profile.json` |
| Module 02 (Income Statement) snapshot uses Q3 8-K; legacy tables clearly labeled Q2 | ✅ | `CATY_02_income_statement.html`, source box references 8-K + 10-Q |
| Module 03 (Balance Sheet) assets/equity refreshed to September 30 balance | ✅ | `data/caty03_balance_sheet.json` |
| Module 05 (NIM) highlights Q3 margin (3.31%) and notes beta window coverage | ✅ | `CATY_05_nim_decomposition.html`, `data/caty05_calculated_tables.json` |
| Module 06 (Deposits) uses Q3 deposit mix (NIB 17.4%, NOW line added) | ✅ | `CATY_06_deposits_funding.html`, `data/caty06_deposits_funding.json` |
| Module 07 (Credit Quality) reflects ACL 0.98%, NPAs $198.7M, NCOs 7.8 bps (Q3) | ✅ | `CATY_07_loans_credit_quality.html`, `data/caty07_credit_quality.json` |
| Module 09 (Capital) capital table compares Q3 vs Q2; CET1 13.15% | ✅ | `CATY_09_capital_liquidity.html`, `data/caty09_capital_liquidity.json` |
| Valuation metadata table timestamps match Q3 run | ✅ | `CATY_12_valuation_model.html` |
| Recent Developments list includes Oct 21 earnings release with metrics | ✅ | `index.html` / `data/recent_developments.json` |
| Market data hub updated (`data/market_data_current.json`) with Q3 ACL, NCO, NIB | ✅ | File check |
| Reconciliation guard executed after changes (noted legacy warnings) | ✅ | `analysis/reconciliation_guard.py` output |
| Manual spot-check of GitHub Pages pending (post-deploy) | ☐ | Visit https://nirvanchitnis-cmyk.github.io/caty-equity-research-live/ after publish |
| Outstanding limitation: detailed cash flow & criticized loan tables still Q2 10-Q (disclosed) | ✅ | Footnotes in Modules 02, 04, 07 |

### Additional Analyst Notes
- Deposit betas remain anchored to Q1’22 → Q2’25 hiking window; down-cycle sensitivities flagged for update once the Q3 10-Q provides average balance schedules.
- Criticized loan percentage retains Q2 disclosure; 8-K did not provide refreshed segmentation. Disclosure text explicitly calls this out.
- Reconciliation guard still reports legacy marker warnings (Wilson/IRC autogen), but run exits cleanly—tracked in backlog `analysis/reconciliation_guard.py`.
- Next action once Q3 10-Q posts: refresh cash flow module, update criticized loan detail, rerun beta calculations with updated average balances, remove disclosures marked “pending Q3 10-Q”.

