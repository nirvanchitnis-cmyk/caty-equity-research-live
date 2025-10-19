# Valuation Sensitivity Summary

Baseline implied price (regression path): $56.11

## Net charge-off shocks

Assumption: provision delta fully flows to after-tax earnings (20% tax).

| NCO Shock | Price Impact |
|-----------|--------------|
| +10 bps | $-1.83 |
| +25 bps | $-4.59 |
| +50 bps | $-9.17 |

## Deposit beta shocks

Interest-bearing deposit base assumed at 16.6B (83% of total).

| Beta Shock | Price Impact |
|------------|--------------|
| +10 bps | $-1.57 |
| +25 bps | $-3.92 |
| +50 bps | $-7.83 |

## Usage

- Apply these deltas on top of scenario prices to articulate elasticities (e.g., +10 bps NCO reduces price by $-1.83).
- Update TOTAL_DEPOSITS and NON_INTEREST_DDA_RATIO once Q3'25 figures are available.

Generated via `analysis/valuation_sensitivity.py`.
