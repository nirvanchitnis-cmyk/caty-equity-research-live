# Probability-Weighted Valuation Analysis

**Generated:** October 19, 2025, 04:40 PT
**Rating:** **HOLD** (downgraded from SELL)
**Method:** Dual-path valuation with explicit probability weighting

---

## TWO SCENARIOS

### Scenario 1: Current Earnings Sustained (23.0% upside)
- ROTE: 11.95% (current)
- P/TBV: 1.560x (regression-implied)
- Target: $56.42
- **Probability: 60%** (analyst assessment)

**Assumptions:**
- Management sustains current credit discipline
- NCO remains below 20 bps
- CRE concentration manageable
- No through-cycle reversion

### Scenario 2: Through-Cycle Normalization (-14.3% downside)
- ROTE: 10.21% (normalized)
- P/TBV: 1.087x (Gordon Growth)
- Target: $39.32
- **Probability: 40%** (analyst assessment)

**Assumptions:**
- NCO reverts to 45.8 bps (42.8 through-cycle + 3.0 CRE premium)
- Annual provision increases $53.8M
- Earnings compression inevitable
- CRE concentration drives higher loss content

---

## PROBABILITY-WEIGHTED TARGET

**Analyst Weights (60/40):**
```
Expected Target = 0.60 × $56.42 + 0.40 × $39.32
                = $33.85 + $15.73
                = $49.58
```

**Return:** +8.1% from current $45.87

**Rating Threshold:**
- BUY if expected return > +15%
- SELL if expected return < -10%
- **HOLD if -10% to +15%**

**Result:** +8.1% → **HOLD**

---

## MARKET-IMPLIED PROBABILITIES

**What does current price $45.87 imply?**

Solving: $45.87 = p × $56.42 + (1-p) × $39.32

```
p = ($45.87 - $39.32) / ($56.42 - $39.32)
p = $6.55 / $17.10
p = 38.3%
```

**Market-implied weights:**
- Current Earnings: **38%**
- Normalization: **62%**

**KEY INSIGHT:** Market is already pricing 62% probability of through-cycle normalization. This is HIGHER than analyst assessment (40%).

**Implication:** Market may be OVERSHOOTING on downside pessimism. Current price already reflects significant normalization risk.

---

## RATING RECONCILIATION

**Why HOLD instead of SELL:**

1. **Market already prices the risk:**
   - 62% implied probability of normalization vs 40% analyst estimate
   - Current price reflects substantial credit concern
   - Limited incremental downside from here

2. **CRE premium unsubstantiated:**
   - Would need 212 bps higher COE than peers
   - CAPM beta 0.90 suggests LOWER risk, not higher
   - No market evidence (CDS, options) supports premium

3. **Expected value modest:**
   - 60/40 weights: +8% expected return
   - Not compelling enough for overweight (BUY threshold: +15%)
   - But not negative enough for underweight (SELL threshold: -10%)

4. **Uncertainty high:**
   - Through-cycle NCO (42.8 bps) based on 17-year history including crisis
   - Recent 8-quarter average: 10.2 bps (much lower)
   - Management track record vs macro uncertainty = coin flip

---

## SENSITIVITY ANALYSIS

| Prob Current | Prob Normalized | Expected Target | Expected Return | Rating |
|--------------|-----------------|-----------------|-----------------|--------|
| 70% | 30% | $51.27 | +11.8% | HOLD |
| **60%** | **40%** | **$49.58** | **+8.1%** | **HOLD** |
| 50% | 50% | $47.86 | +4.3% | HOLD |
| 40% | 60% | $46.18 | +0.7% | HOLD |
| 30% | 70% | $44.46 | -3.1% | HOLD |
| 20% | 80% | $42.77 | -6.7% | HOLD |
| 10% | 90% | $41.05 | -10.5% | SELL |

**Finding:** SELL rating only triggered if >85% probability assigned to normalization scenario.

---

## CONCLUSION

**RATING: HOLD**

**Valuation Summary:**
- Regression (current): $56.42 (+23%)
- Normalized (Gordon): $39.32 (-14%)
- Expected (60/40): $49.58 (+8%)
- Market-implied (38/62): $45.87 (current price)

**Decision:**
Market pricing appears rational. Risk/reward not compellingly directional. Through-cycle thesis has merit but CRE premium unquantified. **Await more evidence before taking strong view.**

---

**Generated:** 2025-10-19 04:40 PT
**Script:** analysis/probability_weighted_valuation.py
**Status:** Complete probability analysis delivered
