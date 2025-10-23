# Valuation Sensitivity Summary

Baseline implied price (regression path): $56.50

## Net charge-off shocks

Assumption: provision delta fully flows to after-tax earnings (20% tax).

| NCO Shock | Price Impact |
|-----------|--------------|
| +10 bps | $-1.98 |
| +25 bps | $-4.96 |
| +50 bps | $-9.92 |

## Deposit beta shocks

Interest-bearing deposit base assumed at 16.9B (83% of total).

| Beta Shock | Price Impact |
|------------|--------------|
| +10 bps | $-1.73 |
| +25 bps | $-4.32 |
| +50 bps | $-8.64 |

## Usage

- Apply these deltas on top of scenario prices to articulate elasticities (e.g., +10 bps NCO reduces price by $-1.98).
- Update TOTAL_DEPOSITS and NON_INTEREST_DDA_RATIO once Q3'25 figures are available.

Generated via `analysis/valuation_sensitivity.py`.
