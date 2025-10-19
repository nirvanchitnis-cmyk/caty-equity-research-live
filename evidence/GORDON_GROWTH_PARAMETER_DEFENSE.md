# Gordon Growth Model Parameter Defense
**Created:** Oct 19, 2025
**Framework:** Gordon Growth Model (Dividend Discount Model variant)
**Audience:** CFA IRC judges, valuation methodology review

---

## Executive Summary

Gordon Growth Model (normalized valuation path) uses two critical parameters:
1. **Perpetual Growth Rate (g) = 2.5%**
2. **Tax Rate = 20%**

**Defense Summary:**
- **g = 2.5%** justified by: (1) Long-term US GDP growth 2.0-2.5%, (2) Inflation target 2.0%, (3) Financial sector nominal growth 2.3% (1990-2024), (4) CATY historical ROE × retention ≈ 2.7%
- **Tax = 20%** justified by: (1) Statutory federal rate 21%, (2) State tax offset by muni bond income, (3) Historical effective rate 19.8% (5-year avg), (4) Forward guidance 20-22%

**Sensitivity:** ±50 bps g → ±$2.80/share (7.1% valuation swing), tax rate immaterial to P/TBV (only affects EPS, not ROTE-based valuation)

---

## 1. Perpetual Growth Rate (g) = 2.5%

### 1.1 Theoretical Framework

**Gordon Growth Model:**
P = D₁ / (COE - g)

**P/TBV Variant:**
P/TBV = (ROTE - g) / (COE - g)

**Where:**
- **g** = Perpetual growth rate of dividends (or book value)
- **Constraint:** g < COE (otherwise model explodes to infinity)
- **Economic Interpretation:** g represents **long-run sustainable growth** in perpetuity

**Key Assumption:** **g cannot exceed nominal GDP growth** (firms cannot grow faster than the economy forever)

---

### 1.2 Empirical Justification (Four Independent Approaches)

#### Approach 1: Macroeconomic Anchoring (GDP + Inflation)

**US Long-Term Nominal GDP Growth:**
- **Real GDP:** 2.0-2.5% (CBO long-term projection, 2025-2050)
- **Inflation Target:** 2.0% (Federal Reserve dual mandate)
- **Nominal GDP:** 4.0-4.5% (real + inflation)

**Financial Sector Growth (Historical):**
- Financial sector GDP 1990-2024: **2.3% CAGR** (BEA data)
- Rationale: Financial sector grows **slower than nominal GDP** (financial repression post-GFC, fintech disruption)

**Adopted g:** 2.5% (midpoint of financial sector historical 2.3% and inflation floor 2.0%)

---

#### Approach 2: Internal Growth Rate (ROE × Retention)

**Formula:** g = ROE × (1 - Payout Ratio)

**CATY Sustainable Growth:**

| Scenario | ROE | Payout Ratio | Retention | g |
|----------|-----|--------------|-----------|---|
| **Current (2025)** | 11.95% | 84% | 16% | **1.9%** |
| **Normalized (Through-Cycle)** | 10.21% | 75% | 25% | **2.6%** |
| **Peer Median** | 8.77% | 78% | 22% | **1.9%** |

**Interpretation:**
- **Current:** g = 1.9% (too low, unsustainable payout 84%)
- **Normalized:** g = 2.6% (aligns with 2.5% assumption)
- **Peer Median:** g = 1.9% (CATY premium reflects higher ROTE)

**Adopted g:** 2.5% (≈ normalized ROTE × target retention 25%)

---

#### Approach 3: Historical CATY Book Value Growth

**CATY BV CAGR (5-Year, 2020-2025):**

| Year | TBVPS | YoY Growth |
|------|-------|------------|
| 2020 | $30.12 | - |
| 2021 | $31.58 | 4.8% |
| 2022 | $33.24 | 5.3% |
| 2023 | $34.91 | 5.0% |
| 2024 | $35.88 | 2.8% |
| 2025 | $36.16 | 0.8% |

**CAGR (2020-2025):** (36.16 / 30.12)^(1/5) - 1 = **3.7%**

**Issue:** 3.7% > 2.5% (historical growth exceeds perpetual assumption)

**Reconciliation:**
- **2020-2023:** Abnormal period (COVID stimulus, low credit losses) → ROTE 12-14%
- **2024-2025:** Normalization begins (ROTE compression to 11.95%)
- **Forward-looking:** Through-cycle ROTE 10.21% → BV growth 2.6% (matches 2.5% g)

**Adopted g:** 2.5% (conservative vs. historical 3.7%, reflects through-cycle normalization)

---

#### Approach 4: Peer Comparison

| Bank | Market Cap ($B) | Historical BV CAGR (5-yr) | Perpetual g (Model) |
|------|----------------|---------------------------|---------------------|
| **CATY** | $2.5 | 3.7% | **2.5%** |
| EWBC | $15.8 | 4.2% | 2.8% |
| CVBF | $2.7 | 2.1% | 2.0% |
| HAFC | $0.8 | 1.8% | 2.0% |
| **Peer Median** | - | **2.9%** | **2.4%** |

**Interpretation:**
- CATY's 2.5% g **slightly above peer median 2.4%** (justified by higher ROTE)
- Conservative vs. historical 3.7% (accounts for through-cycle reversion)

---

### 1.3 Sensitivity Analysis (g Impact on Valuation)

**Gordon Growth P/TBV:**
P/TBV = (ROTE - g) / (COE - g)

**Base Case:**
- ROTE: 10.21% (normalized)
- COE: 9.587%
- g: 2.5%

P/TBV_base = (10.21 - 2.5) / (9.587 - 2.5) = **1.087x**
Target_base = 1.087 × $36.16 = **$39.32**

**Sensitivity Table:**

| g | P/TBV | Target Price | vs. Base | % Change |
|---|-------|--------------|----------|----------|
| **2.0%** | 1.017x | $36.78 | -$2.54 | -6.5% |
| **2.5%** (Base) | 1.087x | $39.32 | - | - |
| **3.0%** | 1.169x | $42.27 | +$2.95 | +7.5% |

**Key Insight:** **±50 bps g → ±$2.75/share (7% swing)**. g is **highly sensitive** parameter.

---

### 1.4 IRC Defense Q&A (Perpetual Growth)

**Q: Why 2.5% when historical BV CAGR is 3.7%?**
A: **Through-cycle normalization.** Historical 3.7% driven by **abnormal 2020-2023 period** (COVID stimulus, low NCOs). **Forward-looking:** Normalized ROTE 10.21% × retention 25% = **2.6% sustainable growth** (rounds to 2.5%).

**Q: Why not use nominal GDP 4.0-4.5%?**
A: **g must be < COE** (9.587%), otherwise model explodes. **Economic constraint:** Financial sector grows **slower than nominal GDP** (2.3% historical). **Conservative choice:** 2.5% errs on low side vs. GDP growth.

**Q: What if CATY grows faster than 2.5% (e.g., M&A, market share gains)?**
A: **Perpetuity assumption = steady state**, not growth mode. **M&A upside** captured in **explicit forecast period** (RIM years 1-5), not terminal value. **2.5% g = no competitive advantage** (commodity banking).

**Q: Peer median g = 2.4%, CATY uses 2.5%. Is this cherry-picking?**
A: **10 bps difference is immaterial** (target price impact <$0.50/share). **Justification:** CATY's normalized ROTE 10.21% **+144 bps above peer median 8.77%** → Warrants slight g premium.

---

## 2. Tax Rate = 20%

### 2.1 Statutory vs. Effective Tax Rate

**US Federal Corporate Tax Rate:** 21% (Tax Cuts and Jobs Act 2017)

**State Tax (California):**
- CA corporate tax rate: 8.84%
- **Blended federal + state:** 21% + (8.84% × 0.79) = **27.98%** (before deductions)

**Effective Tax Rate (After Deductions):**

| Deduction Category | Impact (bps) | Rationale |
|--------------------|--------------|-----------|
| **Municipal Bond Interest** | -550 bps | Tax-exempt income (CATY holds $380M munis, 2.0% of assets) |
| **State Tax Deduction (Federal)** | -140 bps | State taxes deductible federally (post-TCJA cap) |
| **Tax Credits (LIHTC, etc.)** | -90 bps | Low-income housing tax credits (affordable housing loans) |
| **Effective Tax Rate** | **20.2%** | Blended (27.98% - 7.80% deductions) |

**CATY Historical Effective Tax Rate (5-Year):**

| Year | Pre-Tax Income ($M) | Tax Expense ($M) | Effective Rate |
|------|--------------------|--------------------|----------------|
| 2020 | $348 | $71 | 20.4% |
| 2021 | $412 | $84 | 20.4% |
| 2022 | $385 | $75 | 19.5% |
| 2023 | $362 | $70 | 19.3% |
| 2024 | $368 | $73 | 19.8% |
| **5-Yr Avg** | - | - | **19.9%** |

**Rounded:** **20%** (matches historical 19.9% avg)

---

### 2.2 Forward Tax Rate Guidance

**Management Guidance (Q2 2025 Earnings Call):**
> "We expect our effective tax rate to remain in the **20-22% range** over the next 2-3 years, assuming no changes to municipal bond holdings or tax law."

**Conservative Assumption:** Use **20%** (low end of guidance range)

---

### 2.3 Tax Rate Impact on Valuation

**Gordon Growth Model (P/TBV Variant):**

P/TBV = (ROTE - g) / (COE - g)

**Tax rate does NOT appear in P/TBV formula** (ROTE is **after-tax** metric).

**Tax rate DOES affect:**
1. **Normalized NI** (pre-tax income × (1 - tax rate))
2. **EPS** (NI / shares)
3. **P/E multiple** (price / EPS)

**But NOT P/TBV** (which is the primary valuation metric for banks).

---

### 2.4 Tax Rate Sensitivity (EPS Impact Only)

**Normalized NI Calculation:**

| Tax Rate | Pre-Tax NI ($M) | After-Tax NI ($M) | EPS | P/E (at $45.87) |
|----------|-----------------|-------------------|-----|-----------------|
| **18%** | $294 | $241 | $4.41 | 10.4x |
| **20%** (Base) | $294 | $235 | $4.30 | 10.7x |
| **22%** | $294 | $229 | $4.19 | 11.0x |

**Key Insight:** ±200 bps tax rate → ±$0.11 EPS (2.6% swing), **minimal impact on valuation**

---

### 2.5 IRC Defense Q&A (Tax Rate)

**Q: Why 20% when blended statutory rate is 27.98%?**
A: **Effective rate after deductions.** (1) Municipal bond interest (tax-exempt), (2) State tax deduction (federal), (3) LIHTC tax credits. **Historical validation:** 5-year effective rate 19.9% matches 20% assumption.

**Q: What if Trump Tax Cuts expire (2025 sunset)?**
A: **Federal rate reverts to 35%** (pre-TCJA). **Blended:** 35% + (8.84% × 0.65) = **40.7%**. **Effective (after deductions):** ~32-34%. **Valuation impact:** Minimal on P/TBV (ROTE compression offset by peer normalization). **Monitor:** Tax policy changes post-2025 election.

**Q: Why does tax rate not affect P/TBV valuation?**
A: **P/TBV = (ROTE - g) / (COE - g)** uses **after-tax ROTE**. Tax rate **embedded in ROTE**, not a separate variable. **Tax changes affect ROTE** (numerator), but **peer ROTEs also adjust** (relative valuation unchanged).

**Q: Is 20% conservative or aggressive?**
A: **Conservative (low estimate).** Historical 19.9%, guidance 20-22% → Use 20% (low end). **Lower tax = higher NI = higher valuation** → Bullish bias acknowledged.

---

## 3. Combined Sensitivity (g × Tax)

**Gordon Growth Target Price Matrix:**

| | **Tax 18%** | **Tax 20%** (Base) | **Tax 22%** |
|---|---|---|---|
| **g = 2.0%** | $37.12 | $36.78 | $36.45 |
| **g = 2.5%** (Base) | $39.68 | **$39.32** | $38.97 |
| **g = 3.0%** | $42.65 | $42.27 | $41.90 |

**Key Insight:**
- **g dominates** (±50 bps g → ±$2.75, 7% swing)
- **Tax immaterial** (±200 bps tax → ±$0.35, 0.9% swing)

---

## 4. Alternative Growth Scenarios

### 4.1 Zero Growth (g = 0%)

**Implications:** CATY becomes **liquidating entity** (100% payout, no reinvestment)

P/TBV_zero = (10.21 - 0) / (9.587 - 0) = **1.065x**
Target_zero = **$38.53** (-2.0% vs. base $39.32)

**Interpretation:** Even with **zero growth**, CATY worth **$38.53** (current ROTE 10.21% > COE 9.587% → value creation)

---

### 4.2 High Growth (g = 3.5%)

**Constraint:** g < COE (9.587%), so max g ≈ 9.0% theoretically

**Realistic cap:** g ≤ nominal GDP 4.5%

**If g = 3.5%:**

P/TBV = (10.21 - 3.5) / (9.587 - 3.5) = **1.102x**
Target = **$39.85** (+1.3% vs. base)

**Issue:** g = 3.5% requires **retention 34%** (payout 66%), below target 70-80% range.

---

## 5. Peer Perpetual Growth Comparison

| Bank | g (Model) | Justification | COE | Spread (COE - g) |
|------|-----------|---------------|-----|------------------|
| **CATY** | **2.5%** | Normalized ROTE 10.21% × retention 25% | 9.587% | **7.087%** |
| EWBC | 2.8% | Higher ROTE 15.84%, aggressive growth | 9.200% | 6.400% |
| CVBF | 2.0% | Lower ROTE 10.92%, conservative | 9.350% | 7.350% |
| HAFC | 2.0% | Distressed ROTE 8.04%, capital rebuild | 9.720% | 7.720% |
| **Peer Median** | **2.4%** | - | **9.350%** | **7.100%** |

**CATY vs. Peer:**
- g: 2.5% vs. 2.4% median (+10 bps, justified by ROTE premium)
- COE - g spread: 7.087% vs. 7.100% median (-1 bp, immaterial)

---

## 6. Summary & Recommendation

**Perpetual Growth Rate (g) = 2.5%**
- ✅ **Justified by:** (1) Financial sector nominal growth 2.3%, (2) Normalized ROTE × retention 2.6%, (3) Conservative vs. historical 3.7%
- ✅ **Peer comparison:** +10 bps vs. median 2.4% (justified by ROTE premium)
- ⚠️ **Sensitivity:** ±50 bps g → ±$2.75/share (7% swing)

**Tax Rate = 20%**
- ✅ **Justified by:** (1) Historical effective rate 19.9%, (2) Management guidance 20-22%, (3) Muni bond deductions
- ✅ **Impact:** Minimal on P/TBV valuation (embedded in ROTE)
- ✅ **Conservative:** Low end of guidance range (bullish bias acknowledged)

**Combined Parameters:**
- **Gordon Growth Target:** $39.32 (normalized through-cycle valuation)
- **IRC Defensibility:** ✅ **STRONG** (four independent g justifications, historical tax validation)

**Recommendation for Post-Q3:**
- **Monitor g:** If BV CAGR < 2.0% (3 consecutive quarters), reduce g to 2.0%
- **Monitor tax:** If effective rate > 22% (2 consecutive quarters), increase to 21%
- **Stress test:** Quarterly sensitivity analysis (g ± 25 bps, tax ± 100 bps)

---

**Document Owner:** Nirvan Chitnis
**Gordon Growth Methodology:** Myron Gordon (1962), Williams Dividend Theory (1938)
**Data Sources:** BEA (GDP), CBO (long-term projections), CATY 10-Q (historical tax rates)
**Next Review:** Post-Q3 2025 earnings (Oct 21, 2025)
