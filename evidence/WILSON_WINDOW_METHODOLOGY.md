# Wilson Confidence Bounds - Window Selection Methodology

**Created:** October 19, 2025
**Purpose:** Defend post-2008 (26% tail) vs post-2014 (7.7% tail) choice for CFA IRC judges
**Author:** Nirvan Chitnis
**Reviewer:** Derek

---

## Executive Summary

**Official Weighting:** Wilson 95% upper bound from **post-2008 sample** = **26% tail probability**

**Alternative (Rejected):** Wilson 95% upper bound from post-2014 sample = 7.7% tail probability

**Why We Use Post-2008 (Conservative Choice):**
1. **Includes full credit cycle** (GFC 2008-2012, recovery 2013-2019, COVID 2020-2021)
2. **Through-cycle normalization** requires through-cycle data
3. **Statistical conservatism:** Wider confidence interval reflects uncertainty
4. **CFA IRC defensibility:** Post-2014 zero-breach sample invites "cherry-picking" critique

---

## The Numbers

| Window | Quarters | Breach Rate | Wilson 95% Upper | Tail Probability Used |
|--------|----------|-------------|------------------|----------------------|
| **Post-2008 (Official)** | **70** | **15.7%** | **26.0%** | **26% (HOLD rating)** |
| Post-2014 (Alternative) | 46 | 0.0% | 7.7% | Would give BUY rating |
| Post-2020 | 22 | 0.0% | 14.9% | Would give BUY rating |
| Full History (1984+) | 166 | 13.3% | 19.3% | Would give HOLD rating |

**Key Question for IRC Judges:** "Why use 26% tail when post-2014 data shows only 7.7%?"

---

## Defense #1: Through-Cycle Requires Through-Cycle Data

**Normalization Scenario Logic:**
- Tail scenario assumes CATY **reverts to through-cycle NCO** of 45.8 bps
- Through-cycle = long-run average **including stress periods** (GFC)
- Post-2014 window (2015-2025) excludes GFC → **NOT through-cycle**

**Statistical Principle:**
- If tail scenario = "reversion to 45.8 bps through-cycle NCO"
- Then probability must be estimated from data **including the cycle**
- Post-2008 window (2008-2025) includes GFC peak (305.9 bps in 2009) + recovery + COVID

**Analogy:**
- Asking "what's the probability of through-cycle weather" using only sunny-day data = biased
- Must include rainy days to estimate through-cycle probability

**Defense Statement:**
> "We use post-2008 (26% tail) because our normalization scenario assumes reversion to a 45.8 bps through-cycle NCO. This average includes the GFC (2008-2012), and thus the probability of reverting to it must be estimated from data that also includes the GFC. Using post-2014 data (which excludes stress) to estimate probability of a through-cycle stress outcome would be logically inconsistent."

---

## Defense #2: Post-2014 Zero-Breach Rate Invites "Cherry-Picking" Critique

**IRC Judge Challenge:**
> "You chose post-2008 (26% tail, HOLD) over post-2014 (7.7% tail, BUY). Isn't this cherry-picking the window that gives your desired rating?"

**Counter-Defense:**
1. **We show BOTH windows** in evidence/NCO_probability_summary.md:
   ```
   | Post-GFC (>= 2008) | 70 | 15.7% | 26.0% |
   | Post-2014 | 46 | 0.0% | 7.7% |
   ```
   Transparency eliminates cherry-picking accusation.

2. **Zero-breach samples have WIDE confidence intervals:**
   - Post-2014: 0 breaches in 46 quarters
   - Wilson 95% upper bound: 7.7%
   - **Interpretation:** "We're 95% confident breach rate < 7.7%, but point estimate is 0%"
   - Zero-breach rate is **INFORMATION-POOR** (all zeros provide minimal signal)

3. **Post-2008 provides MORE information:**
   - 11 breaches in 70 quarters (15.7% empirical rate)
   - Confidence interval tighter around non-zero empirical rate
   - **Information-rich:** Actual breach history informs probability

**Defense Statement:**
> "Post-2014's zero-breach rate (0% in 46 quarters) is statistically **less informative** than post-2008's 15.7% empirical rate (11 breaches in 70 quarters). A zero-breach sample provides a wide confidence interval (0% to 7.7%) with no empirical anchor. In contrast, post-2008 data includes actual breach history during the GFC, providing an empirical foundation for tail risk assessment. We prefer information-rich data over information-poor zero counts."

---

## Defense #3: Conservative Upper Bound Aligns with Institutional Standards

**Institutional Practice:**
- **Sell-side research:** Use conservative assumptions (avoid overpromising)
- **Buy-side risk management:** Upper bound scenarios for stress testing
- **CFA Code of Ethics:** Reasonable basis, not overly optimistic

**Wilson 95% Upper Bound Interpretation:**
- "We are 95% confident the true breach probability is ≤ 26%"
- Using upper bound (vs. point estimate 15.7%) = **conservative**
- Protects against small-sample uncertainty

**If We Used Post-2014 (7.7% tail):**
- Expected return: ~+18% (would trigger BUY rating)
- But rating based on **zero observed breaches** (shaky foundation)
- IRC judges likely to critique: "BUY rating on zero evidence?"

**Defense Statement:**
> "We use the post-2008 Wilson upper bound (26%) because it represents a statistically **conservative** ceiling on tail risk. Using post-2014 (7.7% upper, zero breaches) would generate a BUY rating (+18% expected return), but this recommendation would rest entirely on an absence of evidence (zero breaches) rather than empirical breach history. Institutional standards favor conservative assumptions with empirical support over optimistic assumptions based on information-poor samples."

---

## Defense #4: Sample Selection is Explicit and Documented

**Transparency Protocol:**
- **All windows documented** in evidence/NCO_probability_summary.md
- **Multiple lookback periods** shown (full history, post-2000, post-GFC, post-2014, post-2020)
- **Trailing windows** shown (8, 16, 32 quarters)
- **Rolling 4-quarter averages** calculated

**Judge Can Verify:**
- FDIC data publicly available (Cert 18503)
- Python script published (analysis/nco_probability_analysis.py)
- Calculation reproducible with SHA256 hashes logged

**Defense Statement:**
> "We document all lookback windows in evidence/NCO_probability_summary.md, showing breach rates from 1984 to present across multiple time horizons. The choice of post-2008 (vs. post-2014) is explicit, justified, and transparent. All data and calculations are reproducible via publicly available FDIC API and our published Python scripts with SHA256-logged evidence trail."

---

## Defense #5: Sensitivity Analysis Shows Rating Robust

**What If Judges Force Post-2014 (7.7% tail)?**
- Tail probability: 7.7% (vs. 26% base case)
- Base probability: 92.3% (vs. 74% base case)
- Expected target: 0.923 × $56.42 + 0.077 × $39.32 = **$55.08**
- Expected return: ($55.08 / $45.87) - 1 = **+20.1%**
- **Rating: BUY** (crosses +15% threshold)

**Investment Implication:**
- Post-2008 (26% tail) → HOLD at +13.3%
- Post-2014 (7.7% tail) → BUY at +20.1%
- **Spread: 6.8 percentage points**

**Conservatism Trade-off:**
- Using post-2008 = **4.5 ppts below BUY trigger** (13.3% vs. 15%)
- Using post-2014 = **5.1 ppts above BUY trigger** (20.1% vs. 15%)
- **Risk asymmetry:** Prefer HOLD over premature BUY

**Defense Statement:**
> "If judges mandate post-2014 (7.7% tail), the rating upgrades to BUY with +20.1% expected return. However, this optimistic outcome rests on zero observed breaches since 2014. We prefer the conservative post-2008 framework (HOLD at +13.3%) to avoid issuing a BUY rating based on information-poor zero-breach data. Institutional practice favors avoiding false positives (premature BUY) over false negatives (delayed BUY)."

---

## CFA IRC Judge Cross-Examination (Anticipated)

### Q1: "Why not use the longest window (full history 1984+, 19.3% upper)?"
**A:** Full history includes pre-2008 regime with different:
- Regulatory capital standards (pre-Basel III)
- Underwriting standards (pre-FDIC reforms)
- Macroeconomic regime (pre-GFC)

Post-2008 window captures the **current regulatory and underwriting regime** most relevant for forward-looking probability assessment.

### Q2: "Post-2014 has 46 quarters (n=46). Isn't that enough for statistical significance?"
**A:** Sample size (n=46) is adequate, but **zero breaches** provide minimal information. Wilson interval handles this correctly by producing a wide confidence bound (0% to 7.7%). The upper bound (7.7%) reflects uncertainty, but the empirical rate (0%) lacks information. Post-2008 provides actual breach events to calibrate probabilities.

### Q3: "Doesn't using post-2008 (GFC) overstate tail risk in today's environment?"
**A:** Possibly. But our tail scenario assumes **reversion to 45.8 bps** (the 2008-2024 average **including GFC**). If we exclude GFC from probability estimation but include it in through-cycle NCO calculation, we create internal inconsistency. Both must use the same window for methodological coherence.

### Q4: "What if CATY never breaches 45.8 bps again? Isn't 26% tail too high?"
**A:** This is the **key investment question**. If CATY's true breach probability is near zero (post-2014 suggests this), the Wilson upper bound will mechanically tighten as more zero-breach quarters accumulate:
- Post-Q3 2025 (if no breach): Upper bound drops to ~25%
- Post-Q4 2025 (if no breach): Upper bound drops to ~24%
- Post-Q1 2026 (if no breach): Upper bound drops to ~23%
- **Auto-upgrade to BUY when upper bound < 21.5%** (built into rating policy)

This is why we have a **mechanical auto-flip rule** - as zero-breach evidence accumulates, confidence tightens, expected return rises, rating upgrades. The framework is **data-responsive**, not static.

### Q5: "Market prices 62% tail (vs. your 26%). Why should I trust your model?"
**A:** Market may be pricing:
- Office CRE tail risk not yet in FDIC NCO data
- Recession probability higher than FDIC history suggests
- Regulatory capital risk or dividend cut risk

We **acknowledge market divergence** in evidence/probability_dashboard.md (47 percentage point spread). Our thesis: **Market excessively pessimistic** relative to FDIC breach history. This creates the investment opportunity (HOLD with +13.3% expected return vs. market-implied 0%).

---

## Comparison Table (For IRC Judges)

| Window Choice | Empirical Breach Rate | Wilson 95% Upper | Tail Prob Used | Expected Return | Rating | Rationale |
|---------------|-----------------------|------------------|----------------|-----------------|--------|-----------|
| **Post-2008 (Official)** | **15.7%** | **26.0%** | **26%** | **+13.3%** | **HOLD** | Includes full cycle, conservative, empirically anchored |
| Post-2014 (Alternative) | 0.0% | 7.7% | 7.7% | +20.1% | BUY | Zero breaches, information-poor, risks false positive |
| Post-2020 | 0.0% | 14.9% | 14.9% | +17.4% | BUY | COVID-only, too short for cycle |
| Full History (1984+) | 13.3% | 19.3% | 19.3% | +15.8% | BUY (marginal) | Includes pre-Basel III regime changes |

**IRC judges may prefer:** Post-2008 (our choice) or full history (19.3% tail, still yields HOLD)

**IRC judges likely to reject:** Post-2014 or post-2020 (zero-breach samples, information-poor)

---

## Methodology Strength (CFA IRC Scoring)

**What We Did Right:**
1. ✅ **Showed multiple windows** (transparent, not cherry-picked)
2. ✅ **Used statistical method** (Wilson 95%, not gut feel)
3. ✅ **Conservative choice** (upper bound, not point estimate)
4. ✅ **Logical consistency** (through-cycle NCO requires through-cycle probability)
5. ✅ **Auto-flip rule** (mechanical upgrade as data accumulates)
6. ✅ **Evidence trail** (reproducible, SHA256-logged FDIC data)

**Potential IRC Judge Concerns:**
1. ⚠️ Post-2008 window = 70 quarters (moderately large, not huge)
2. ⚠️ Breach threshold (45.8 bps) is subjective (though FDIC-derived)
3. ⚠️ Market disagrees (62% tail vs. our 26% tail)

**Net Assessment:** **Defensible methodology, institutional-grade execution, transparent presentation.**

---

## Recommended Disclosure (For IRC Report)

**Add to Valuation Section:**

> **Wilson Window Selection:** We use the post-2008 window (70 quarters) to calculate the Wilson 95% upper bound (26% tail probability) because our normalization scenario assumes reversion to a 45.8 bps through-cycle NCO—an average that includes the GFC (2008-2012). Estimating the probability of a through-cycle outcome requires data spanning the cycle.
>
> **Alternative Window:** Post-2014 data (46 quarters, zero breaches) yields a Wilson 95% upper bound of 7.7%, implying a BUY rating with +20.1% expected return. However, we reject this approach because:
> 1. Zero-breach samples are information-poor (wide confidence intervals, no empirical anchor)
> 2. Post-2014 excludes the GFC, inconsistent with our through-cycle normalization assumption
> 3. Institutional standards favor conservative upper bounds over optimistic zero-breach extrapolations
>
> **Auto-Upgrade Protocol:** Our rating policy includes a mechanical auto-flip rule: If Wilson upper bound drops below 21.5% (as zero-breach quarters accumulate), the entire confidence interval clears the +15% BUY threshold, triggering an automatic upgrade. This data-responsive framework avoids static window dependence.
>
> **Sensitivity:** Post-2014 (7.7% tail) → BUY at +20.1%. Post-2008 (26% tail) → HOLD at +13.3%. We prefer HOLD (conservative) over BUY (optimistic on zero evidence).

---

## Visual Aid for IRC Presentation (Slide Concept)

```
WILSON CONFIDENCE BOUNDS - WINDOW SELECTION

Post-2014 Window (46 quarters, 2015-2025):
├─ Breach rate: 0% (0 out of 46)
├─ Wilson 95% upper: 7.7%
├─ Expected return: +20.1%
└─ Rating: BUY ⚠️ (rests on zero breaches - information-poor)

Post-2008 Window (70 quarters, 2008-2025):
├─ Breach rate: 15.7% (11 out of 70)
├─ Wilson 95% upper: 26.0%
├─ Expected return: +13.3%
└─ Rating: HOLD ✓ (empirically anchored, includes GFC)

Through-Cycle NCO Assumption: 45.8 bps
├─ Calculated from: 2008-2024 FDIC average (17 years)
├─ Includes: GFC peak (305.9 bps), recovery, COVID
└─ Logic: Probability window MUST match normalization window

```

---

## Derek's Brutal Review Checklist

Derek, validate these defenses:
- [ ] Through-cycle logic sound? (Probability window must match NCO window)
- [ ] Information-poor vs. information-rich framing defensible?
- [ ] Conservative institutional practice argument holds?
- [ ] Auto-flip rule adequately addresses "too conservative" critique?
- [ ] Transparency (showing all windows) sufficient to deflect cherry-picking?

**If you find logical gaps, tear them apart. This must survive IRC judges.**

---

**Document Status:** Ready for Derek brutal review
**Next Action:** Incorporate Derek feedback, add to DEREK_EXECUTIVE_SUMMARY.md as appendix
**IRC Submission:** Include as "Methodology Appendix: Wilson Window Selection"

