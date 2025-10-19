# VALUATION RECONCILIATION - Regression vs Gordon Growth

**Generated:** October 19, 2025, 04:30 PT
**Conclusion:** **DOWNGRADE FROM SELL TO HOLD**

---

## PATH A: PEER REGRESSION (Current Earnings)

**Method:** Cross-sectional P/TBV vs ROTE regression

**Sample:** n=7 peers (excluding HOPE negative ROTE)
- EWBC, CVBF, HAFC, COLB, WAFD, PPBI, BANC

**Regression:**
```
P/TBV = 0.6049 + 0.0799 × ROTE
R² = 0.6649
p-value = 0.025 (statistically significant)
Std Error = 0.0233
```

**CATY Valuation:**
- Current ROTE: 11.95%
- Implied P/TBV: 1.560x
- TBVPS: $36.16
- **Target: $56.42**
- Current: $45.87
- **Return: +23.0% UPSIDE**

---

## PATH B: GORDON GROWTH (Normalized Earnings)

**Method:** P/TBV = (Normalized ROTE - g) / (COE - g)

**Normalization:**
- LTM Net Income: $294.7M
- LTM NCO Rate: 18.13 bps
- Through-Cycle NCO: 42.8 bps (17-year FDIC median)
- CRE Premium: 3.0 bps (from concentration analysis)
- **Total Normalized NCO: 45.8 bps**

**Provision Impact:**
- Delta NCO: 27.67 bps
- Delta Provision: $53.8M
- After-tax impact: $43.1M
- **Normalized NI: $251.6M**

**Normalized ROTE:**
- Normalized NI / Avg TCE: $251.6M / $2,465.1M = **10.21%**

**Gordon Growth Inputs:**
- Normalized ROTE: 10.21%
- Growth (g): 2.5%
- COE: 9.59%

**Calculation:**
```
P/TBV = (10.21 - 2.5) / (9.59 - 2.5)
P/TBV = 7.71 / 7.09
P/TBV = 1.088x
```

**CATY Valuation:**
- Normalized P/TBV: 1.088x
- TBVPS: $36.16
- **Target: $39.32**
- Current: $45.87
- **Return: -14.3% DOWNSIDE**

---

## PATH C: CRE RISK PREMIUM RECONCILIATION

**Question:** What COE premium would make Gordon Growth = Regression target?

**Target from Regression:** $56.42
**Required P/TBV:** 1.560x

**Solving for COE:**
```
1.560 = (10.21 - 2.5) / (COE - 2.5)
COE = (10.21 - 2.5) / 1.560 + 2.5
COE = 7.47%
```

**COE Comparison:**
- Current COE (baseline): 9.59%
- Required COE (for $56): 7.47%
- **Implied CRE Premium: 212 bps**

**Wait - this is BACKWARDS:**
Required COE is LOWER than baseline, not higher. This means regression implies CATY deserves a 212 bps DISCOUNT (lower COE), not premium.

**Recalculating...**

To reconcile Gordon Growth target ($39.32) with regression framework:
- Need P/TBV 1.088x
- At normalized ROTE 10.21%, regression predicts: 0.6049 + 0.0799 × 10.21 = 1.420x
- Regression overvalues by: 1.420x - 1.088x = 0.332x
- This is a 23.4% overvaluation at normalized ROTE

**Correct reconciliation:**
For Gordon Growth $39.32 to equal regression, need to ADD risk premium:
- Gordon COE must increase from 9.59% to drive P/TBV down from 1.088x to match reality
- OR: Normalized ROTE must be even LOWER than 10.21%

**Actually solving for COE that gives P/TBV = 1.088x:**
```
1.088 = (10.21 - 2.5) / (COE_adj - 2.5)
COE_adj = (10.21 - 2.5) / 1.088 + 2.5
COE_adj = 9.59%
```

This is the SAME as baseline COE. So Gordon Growth at 9.59% COE gives correct $39.32.

**The issue:** Regression at current ROTE 11.95% gives $56, but we believe ROTE will fall to 10.21%.

---

## RECONCILIATION SUMMARY

**Two methods, two assumptions:**

1. **Regression:** Assumes ROTE stays at 11.95% → $56.42 target
2. **Gordon Growth:** Assumes ROTE falls to 10.21% → $39.32 target

**The thesis:** Current 11.95% ROTE is UNSUSTAINABLE due to:
- Through-cycle NCO normalization (42.8 bps vs current 18.1 bps)
- CRE concentration premium (+3 bps)
- Required provision build ($53.8M annual)

**If you believe the thesis:** Target $39-40 (SELL)
**If you don't:** Target $56 (BUY based on current earnings)

---

## CONCLUSION: HOLD (not SELL)

**Cannot justify SELL because:**

1. **Regression shows +23% upside** at current earnings
2. **Through-cycle normalization is NOT CERTAIN:**
   - 17-year average includes 2008-09 crisis
   - Recent 8-quarter average NCO: 10.2 bps (not 42.8 bps)
   - Management may sustain current credit discipline

3. **CRE premium lacks quantitative support:**
   - CAPM beta 0.90 (below market)
   - No evidence CATY COE should be higher than peers
   - HIGH-CRE status documented but premium magnitude uncertain

4. **Market may be right:**
   - Current price $45.87 between regression $56 and normalized $39
   - Implies market assigns ~40% probability to normalization scenario
   - This is REASONABLE given uncertainty

**DOWNGRADE: SELL → HOLD**

**Reasoning:**
- Upside if earnings sustained: +23%
- Downside if normalized: -14%
- Expected value: Neutral to slight negative
- Risk/reward: Asymmetric but not compellingly negative
- **Rating: HOLD** (wait for more evidence on credit trends)

---

**Generated:** 2025-10-19 04:32 PT
**Script:** analysis/valuation_bridge_final.py
**Status:** Complete dual valuation bridge delivered
