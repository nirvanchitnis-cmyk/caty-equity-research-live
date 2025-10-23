# CET1 Headroom & Buyback Capacity – Q3 2025

Prepared: 2025‑10‑22

Objective: quantify pro‑forma CET1 paths under continued repurchases using Q3 starting capital and the empirically observed CET1 sensitivity.

## Starting point
- CET1 ratio: 13.15% (Q3 2025)
- Guardrail (management/conservative floor): 12.00%
- Observed impact: ~$50.1M repurchase in Q3 reduced CET1 ~20 bps and TBVPS by ~16 bps (see `CATY_10_capital_actions.html`)

Assumption (local linear): each $50M in net repurchases consumes ~20 bps CET1.

## Headroom schedule
| Incremental Buyback | CET1 delta | Pro‑forma CET1 | Status vs 12% |
| --- | ---: | ---: | --- |
| $0M (base) | 0 bps | 13.15% | +115 bps headroom |
| $50M | −20 bps | 12.95% | +95 bps |
| $100M | −40 bps | 12.75% | +75 bps |
| $150M | −60 bps | 12.55% | +55 bps |
| $200M | −80 bps | 12.35% | +35 bps |
| $250M | −100 bps | 12.15% | +15 bps |
| $300M | −120 bps | 11.95% | Breaches guardrail |

## Notes & constraints
- This schedule ignores earnings accretion and RWA changes; actual trajectories will be modestly better as earnings replenish capital.
- A breath test (no dividend cuts): with 70.8% LTM payout (dividends + buybacks), holding CET1 ≥12.0% suggests ≤ ~$250M of additional buybacks unless offset by earnings/RWA management.
- See also EPS/ROTE impacts in `CATY_10_capital_actions.html` and the buyback analysis workpaper.

## RWA creep scenarios (downgrade‑driven)
Approximate impact of RWA increases on CET1 ratio, holding CET1 capital constant (ratio scales as CET1% ÷ (1+ΔRWA%)).

| ΔRWA | CET1 (no buyback) | CET1 (−$100M buyback) | CET1 (−$200M buyback) |
|------|-------------------:|----------------------:|----------------------:|
| +0%  | 13.15%             | 12.75%               | 12.35% |
| +5%  | 12.52%             | 12.14%               | 11.76% |
| +10% | 11.95%             | 11.59%               | 11.23% |

Interpretation: A +5% RWA step‑up trims ~63 bps off CET1, independent of buybacks; combine rows with the headroom ladder to set program caps.

## Links
- Capital module: `CATY_10_capital_actions.html#repurchases`
- Q3 repurchase workpaper: `evidence/workpapers/CATY_Q3_2025_buyback_analysis.md`
