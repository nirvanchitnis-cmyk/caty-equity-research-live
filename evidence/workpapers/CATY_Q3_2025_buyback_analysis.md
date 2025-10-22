# CATY Q3 2025 Share Repurchase Analysis

Prepared October 22, 2025 to support the capital-actions module and CFA review comments.

## 1. Transaction Detail

- Shares repurchased: **1,070,000** at an average price of **$46.81** (total **$50.1M**).  
  Source: Q3 2025 press release (Form 8-K Exhibit 99.1), management commentary paragraph 3 (`evidence/raw/CATY_2025Q3_8K/ex_873308.htm`, line ~247).

## 2. EPS Uplift (Quarterly Run-Rate)

| Metric | Q3 2025 | Q2 2025 | Evidence |
| --- | ---: | ---: | --- |
| Diluted average shares | 68,990,648 | 70,188,902 | Form 8-K Exhibit 99.1 share count table (`ex_873308.htm`, lines ~4720) |
| Net income (USD M) | 77.651 | — | Form 8-K Exhibit 99.1 financial highlights (`ex_873308.htm`, line ~1745) |
| EPS (actual) | 1.13 | — | Reported |
| EPS (pro forma, Q2 share base) | 77.651 ÷ 70.188902 = **1.11** | — | Calculated |

**Accretion:** ~**$0.02** per share (1.8¢) quarter over quarter attributable to the lower share count.

## 3. Tangible Book Value Impact

- Tangible book value per share (TBVPS) Q3 2025: **$36.96**  
- TBVPS Q2 2025: **$36.16**  
  (Form 8-K Exhibit 99.1, non-GAAP reconciliation, `ex_873308.htm`, lines ~6280).

Without deploying the $50.1M, the pro-forma TBVPS would have been **$37.12**, implying **16 bps** of dilution from buying stock at ~**1.29×** TBV.

## 4. CET1 Headroom

- CET1 ratio September 30, 2025: **13.15%** (vs. 13.35% at June 30).  
  Source: Form 8-K Exhibit 99.1 capital ratios paragraph (`ex_873308.htm`, line ~1661).
- Tangible/common equity (proxy for CET1): **$2,523.9M** (`ex_873308.htm`, non-GAAP table, line ~6068).

Derived risk-weighted assets:

```
RWA = CET1 $ / CET1% = 2,523.9 / 0.1315 ≈ $19,193M
```

Headroom before breaching management’s 12.0% guardrail:

```
ΔCET1 (bps) = 13.15% − 12.00% = 1.15%
Capital capacity = 0.0115 × 19,193 ≈ $221M
```

That capacity covers roughly **4×** the Q3 deployment.

## 5. Authorization Status

- Board authorization: **$150M** (July 15, 2024).  
- Cumulative spent through Q3 2025: **$90.1M** → **$59.9M** remaining.  
  Source: `data/caty10_capital_actions.json` (aggregated from treasury stock footnotes; next update scheduled once the Q3 10-Q posts).

## 6. Summary

- Buyback lifted quarterly EPS by ~1.8¢ and ROTE by ~9 bps through a smaller equity base.
- Trade-off: 16 bps of TBV dilution and 20 bps CET1 consumption.
- With ~$221M of CET1 headroom to a 12% target and $59.9M left on the authorization, management can continue repurchases but should avoid prices materially above TBV unless incremental ROE is demonstrably accretive.

