# Capital Stress → Probability Weight Bridge

**Generated:** October 19, 2025, 05:50 PT
**Purpose:** Link capital stress outcomes to tail probability adjustments

---

## Capital Stress Outputs

From `evidence/capital_stress_2025Q2.xlsx`:

**Base Case (42.8 bps NCO normalization):**
- CET1 burn: 20.1 bps
- Remaining cushion: 265 bps

**Combined Stress (NCO + Industrial/Warehouse):**
- CET1 burn: 141.3 bps
- **Remaining cushion: 164 bps**

**Regulatory minimum:** CET1 7.0%
**Management target:** CET1 10.0%

---

## Bridge to Probability Framework

**Question:** How does capital stress inform tail probability?

**Current Approach (Wilson Bounds):**
- Tail probability derived from FDIC NCO breach frequency
- 95% upper bound: 26% normalization probability
- **Capital stress used for VALIDATION, not calibration**

**Validation Logic:**
1. At 74/26 weights, combined stress gives 141.3 bps CET1 burn
2. Remaining cushion: 164 bps (above 100 bps prudent minimum)
3. **Interpretation:** Even at 95% pessimistic tail case, capital remains adequate
4. **Conclusion:** 74/26 weights are SUSTAINABLE from capital perspective

---

## If Capital Stress Were Used to Calibrate Probability

**Hypothetical approach (NOT USED):**

If CET1 cushion drops below 120 bps, increase tail probability:
- Current cushion: 164 bps → No adjustment
- If cushion < 120 bps → Increase tail weight +5-10%
- If cushion < 80 bps → Increase tail weight +15-20%

**Why we DON'T use this:**
- Circular logic: Capital stress depends on NCO assumptions
- FDIC breach frequency is more objective
- Capital stress used for validation only

---

## Summary

**Capital Stress Role:**
- **Validation:** Confirms 74/26 weights produce sustainable capital outcomes
- **NOT Calibration:** Doesn't set the probability weights directly
- **Check:** 164 bps cushion at 74/26 → Adequate (no probability adjustment needed)

**If capital stress showed cushion < 100 bps at 74/26:**
- Would signal tail weight too low
- Would trigger review of NCO assumptions
- Might justify higher tail probability

**Current state:** 164 bps cushion validates 74/26 weights as reasonable.

---

**Generated:** 2025-10-19 05:50 PT
**Method:** Capital stress validation of probability weights
**Conclusion:** No probability adjustment needed (cushion adequate)
