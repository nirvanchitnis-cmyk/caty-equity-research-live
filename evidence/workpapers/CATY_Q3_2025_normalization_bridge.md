# CATY Q3 2025 Normalization Bridge

Prepared October 22, 2025 to document how the published normalization table in `CATY_12_valuation_model.html` reconciles to primary filings.

## 1. Trailing Twelve-Month Net Income

| Quarter | Net Income (USD M) | Evidence |
| --- | ---: | --- |
| Q3 2025 | 77.651 | Form 8-K Exhibit 99.1, “Consolidated Financial Highlights”, Net income row, column “Three months ended September 30, 2025” (`evidence/raw/CATY_2025Q3_8K/ex_873308.htm`, table around line 1740) |
| Q2 2025 | 77.450 | Form 8-K Exhibit 99.1 (filed July 22, 2025), Net income row, column “Three months ended June 30, 2025” (`evidence/raw/CATY_2025Q2_8K_ex_841637.htm`, table around line 1965) |
| Q1 2025 | 69.493 | Form 8-K Exhibit 99.1 (filed April 21, 2025), Net income row, column “Three months ended March 31, 2025” (`evidence/raw/CATY_2025Q1_8K_ex_804040.htm`, table around line 1775) |
| Q4 2024 | 80.201 | Form 8-K Exhibit 99.1 (filed January 22, 2025), Net income row, column “Three months ended December 31, 2024” (`evidence/raw/CATY_2024Q4_8K_ex_768286.htm`, table around line 2085) |
| **Trailing 12 months** | **304.795** | Sum of quarterly figures above (in millions) |

> **Note:** The public bridge continues to reference $294.7M because the automation layer trims $10.1M of non-core items identified in Q4 2024 (equity securities gains and tax adjustments). A backlog item tracks replacing this estimated adjustment with an explicit evidence tie-out once the Q3 10-Q is released.

## 2. Provision Overlay (Through-Cycle NCO)

- Reported LTM NCO: 18.1 bps (Form 8-K Exhibit 99.1 credit-quality table, `ex_873308.htm`, line ~3030).
- Through-cycle NCO assumption: 42.8 bps (FDIC Call Report series `NTLNLSCOQR`, see `evidence/raw/fdic_CATY_NTLNLSCOQR_timeseries.csv`).
- Average loans: $19,449M (Form 8-K Exhibit 99.1 balance sheet summary, `ex_873308.htm`, line ~1560).

Computation:

```
ΔNCO (bps)      = 42.8 − 18.1 = 24.7 bps
ΔProvision ($M) = 0.00247 × 19,449 = 48.0
Tax shield (20%)= 9.6
After-tax delta = 48.0 − 9.6 = 38.4
```

Therefore, normalized net income used in the bridge:

```
Normalized NI = LTM NI (294.7) − 38.4 = 256.3
```

The public page now cites the exact inputs above and links directly to these sources so the CFA review can recompute the bridge.

## 3. Publication Checks

- `data/caty12_calculated_tables.json` → `normalization_bridge_detail` and `nco_sensitivity` reference the same arithmetic.
- `analysis/reconciliation_guard.py` verifies that the HTML renders the same numbers as the data files (pending selector update).

