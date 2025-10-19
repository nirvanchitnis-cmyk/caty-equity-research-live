# Probability Dashboard

**Last Updated:** October 19, 2025, 05:40 PT
**Next Update:** Post-Q3 earnings (Oct 28, 2025)

## Current Probability Estimates

| Framework | Base Prob | Tail Prob | Expected Target | Expected Return | Rating |
|-----------|-----------|-----------|-----------------|-----------------|--------|
| **Data-Anchored (post-2008 mean)** | **85%** | **15%** | **$53.86** | **+17.4%** | BUY |
| **Wilson 95% Upper Bound** | **74%** | **26%** | **$51.97** | **+13.3%** | **HOLD** ✓ |
| Market-Implied (spot $45.87) | 38% | 62% | $45.87 | 0.0% | — |

**Official Weighting:** 74/26 (Wilson 95% ceiling)
**Current Rating:** HOLD
**BUY Trigger:** Tail probability < 21.5%

## Divergence Monitoring

**Data vs Market Spread:**
- Data-anchored: 85% base case
- Market-implied: 38% base case
- **Spread: 47 percentage points**

Market appears **excessively pessimistic** relative to FDIC breach history (0% post-2014).

## Monitoring Schedule

**Quarterly (post-earnings):**
- Rerun `analysis/nco_probability_analysis.py` with new FDIC data
- Update Wilson confidence bounds
- Recalculate expected returns
- Apply rating policy auto-flip if bounds shift

**Monthly:**
- Track market-implied probability via stock price
- Monitor spread between data-anchored and market views
- Flag if spread widens >50 ppts

**Owner:** Derek review desk
**Next Execution:** October 28, 2025 (post-Q3 earnings)

---

**Generated:** 2025-10-19 05:40 PT
