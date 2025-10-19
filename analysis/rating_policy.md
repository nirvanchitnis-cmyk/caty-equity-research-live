# Rating Policy Reference – CATY Equity Research

**Objective:** Encode decision thresholds so rating moves are data-driven, not ad hoc.

---

## Return-Based Bands (12-Month Horizon)

- **BUY:** Expected total return > **+15%**
- **HOLD:** Expected total return between **-10%** and **+15%**
- **SELL:** Expected total return < **-10%**

Returns measured off latest closing price; targets derived from probability-weighted scenario analysis.

---

## Probability Discipline

Let `P_base` be probability of the “current earnings” regime and `P_tail = 1 - P_base` be the normalized credit scenario.

1. Start with data-anchored estimate (latest FDIC sample mean).
2. Stress with Wilson 95% upper bound; if the interval crosses a rating boundary, default to the more conservative rating until new data tightens the band.
3. Flip rating automatically once entire confidence interval clears or breaches a threshold.

Example (Oct-19-2025):
- Base scenario probability: 85% (post-2008 mean)
- Tail ceiling (95%): 26%
- BUY hurdle requires tail ≤ 21.5%; interval crosses boundary → HOLD with positive bias.

---

## Monitoring & Trigger Cadence

- **Quarterly:** Refresh FDIC NCO data and recompute Wilson bounds.
- **Earnings (next: Oct-28-2025):** Update management guidance, CRE delinquency trends, reserve build.
- **Monthly:** Track market-implied probabilities via spot price reconciliation.
- **Kill-Switches:**
  - Tail scenario triggered if CET1 buffer < 120 bps or NCO > 35 bps for two consecutive quarters.
  - Upgrade trigger if tail probability upper bound drops below 21.5% or market-implied tail < 30%.

Assignments: Derek review desk maintains methodology; Claude updates calculations post data releases.

