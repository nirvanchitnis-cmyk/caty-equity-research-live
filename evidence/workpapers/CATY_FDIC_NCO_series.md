# FDIC Net Charge-Off History – Cathay General Bancorp (CERT 23417)

**Source:** `evidence/raw/fdic_CATY_NTLNLSCOQR_timeseries.csv` (downloaded Oct 22, 2025)
**Context:** Quarterly net charge-off rate (annualised, basis points) for Cathay Bank. Dataset spans 2008-Q1 through 2025-Q2 (70 quarters).

## Summary Statistics
| Period | Quarters | Average (bps) | Median (bps) | Notes |
|--------|----------|---------------|--------------|-------|
| 2008-Q1 → 2025-Q2 | 70 | 26.9 | 7.2 | Full through-cycle sample including GFC and COVID |
| 2014-Q1 → 2025-Q2 | 46 | 4.0 | 2.6 | Post-crisis era (Basel III in force) |
| 2018-Q1 → 2025-Q2 | 30 | 5.1 | 3.5 | Post-tax reform, pre-pandemic |
| 2020-Q1 → 2025-Q2 | 22 | 8.1 | 6.8 | Pandemic + rate hike cycle |
| 2023-Q1 → 2025-Q2 | 10 | 10.7 | 8.0 | Recent regime feeding base case |

## Latest Observations
| Quarter | NCO (bps) |
|---------|-----------|
| 2023-Q3 | 11.54 |
| 2023-Q4 | 7.21 |
| 2024-Q1 | 1.97 |
| 2024-Q2 | 13.73 |
| 2024-Q3 | 7.24 |
| 2024-Q4 | 28.23 |
| 2025-Q1 | 3.42 |
| 2025-Q2 | 21.73 |

## Usage
- Base case normalization uses the full through-cycle average (42.8 bps).
- Sensitivity analysis in Module 12 includes scenarios at 25 bps (recent run-rate), 42.8 bps (through-cycle), and 60 bps (moderate recession).
- Q3 2025 investor presentation disclosed net charge-offs of 18.1 bps (annualised) – well below the through-cycle average but above post-pandemic median (7.2 bps). See `evidence/raw/CATY_2025Q3_8K/ex_873308.htm`.
