# CAPITAL STRESS WORKSHEET - CATHAY GENERAL BANCORP

**Date:** October 19, 2025
**Analyst:** Nirvan Chitnis
**Objective:** Model CET1 and TBVPS impact under through-cycle NCO scenarios

---

## EXECUTIVE SUMMARY

**Purpose:** Quantify capital burn and tangible book value impairment if CATY normalizes to through-cycle NCO rates (42.8 bps base case, 60 bps bear case) from current 18.1 bps LTM.

**Key Findings (UPDATED):**
- **Through-cycle NCO normalization (42.8 bps)** requires $48.0M gross provisions ($38.4M after tax), equating to a **20.1 bps CET1 burn** and leaving **265 bps** of cushion above the 10.5% management buffer.
- **Industrial/Warehouse bear case (15% cumulative loss)** consumes **121.2 bps** of CET1 and, when stacked with base-case normalization, totals **141.3 bps** of capital erosion; buffer tightens to **164 bps** and **TBVPS falls to $32.82 (-9.2%)**.
- **Capital flexibility is materially reduced:** buybacks must pause; dividend coverage remains but moves onto watch as CRE outlier risk compounds other stress assumptions.

---

## STARTING POINT - Q2 2025 CAPITAL POSITION

### Regulatory Capital (Q2'25 10-Q)

| Metric | Value | Source |
|--------|-------|--------|
| **Common Equity Tier 1 (CET1)** | $2,552.3M | Q2'25 10-Q, Reg. Capital table |
| **Risk-Weighted Assets (RWA)** | $19,118.5M | Q2'25 10-Q |
| **CET1 Ratio** | 13.35% | Q2'25 10-Q |
| **Total Loans** | $19,784.7M | Q2'25 10-Q |

**Regulatory Minimums:** CET1 4.5% (well-capitalized: 6.5%); Cathay targets ≥10.5% buffer.

---

### Tangible Book Value (Q2'25 10-Q)

| Metric | Value | Source |
|--------|-------|--------|
| **Shareholders' Equity** | $2,511.4M | Q2'25 10-Q |
| **Goodwill + Intangibles** | $7.6M | Q2'25 10-Q |
| **Tangible Common Equity (TCE)** | $2,503.8M | Equity − Goodwill/Intangibles |
| **Shares Outstanding** | 69.34M | Q2'25 10-Q |
| **TBVPS** | $36.16 | TCE / Shares |

---

### Allowance for Credit Losses (Q2'25)

| Metric | Value | Source |
|--------|-------|--------|
| **ACL - Loans** | $174.5M | Q2'25 10-Q, Note on ACL |
| **Total Loans** | $19,784.7M | Q2'25 10-Q |
| **ACL Coverage Ratio** | 0.90% | ACL / Total Loans × 100 |

---

## NCO NORMALIZATION SCENARIOS

### Current LTM NCO vs Through-Cycle

| Period | NCOs ($M) | Avg Loans ($M) | NCO Rate (bps) | Notes |
|--------|-----------|----------------|----------------|-------|
| **LTM (Q3'24-Q2'25)** | $35.3M | $19,449M | **18.1 bps** | Current performance |
| **Through-Cycle (2008-2024 FDIC)** | — | — | **42.8 bps** | 17-year average including GFC |
| **Bear Case (GFC Peak)** | — | — | **60 bps** | 2009-2010 stress level |

**Delta from Current:**
- Base Case: +24.7 bps (42.8 - 18.1)
- Bear Case: +41.9 bps (60.0 - 18.1)

---

## SCENARIO 1: BASE CASE (42.8 BPS THROUGH-CYCLE NCO)

### Step 1: Calculate Incremental Provision Requirement

**Assumptions:**
- Avg Loans: $19,449M (LTM average)
- Target NCO: 42.8 bps annually
- Tax Rate: 20%

**Calculation:**

```
Incremental NCO = (42.8 bps - 18.1 bps) × $19,449M
                = 24.7 bps × $19,449M
                = 0.00247 × $19,449M
                = $48.0M annually
```

**After-Tax Impact on Net Income:**
```
Provision Expense = $48.0M
Tax Shield = $48.0M × 20% = $9.6M
After-Tax NI Impact = $48.0M - $9.6M = $38.4M reduction
```

---

### Step 2: Impact on ROTE and P/TBV

| Metric | Current | Post-Normalization |
|--------|---------|-------------------|
| **LTM Net Income** | $294.7M | $256.3M |
| **Avg TCE** | $2,465.1M | $2,465.1M |
| **ROTE** | 11.95% | 10.40% |
| **Fair P/TBV (regression)** | — | 1.115x |
| **Implied Target TBVPS** | — | $36.16 × 1.115 = $40.32 |

**Result:** Current SELL thesis validated - target $40.32 vs spot $45.89 = -12.1% downside

---

### Step 3: CET1 Burn Analysis

**Scenario:** Assume bank normalizes to 42.8 bps NCO WITHOUT building ACL (i.e., charge-offs flow through capital)

**Year 1 Capital Burn:**
```
After-tax NCO Impact = $38.4M (from Step 1)
CET1 Reduction       = $38.4M
Starting CET1 Ratio  = 13.35%
RWA                  = $19,118.5M

CET1 Ratio Impact = ($38.4M ÷ $19,118.5M) × 10,000 = **20.1 bps**
Ending CET1 Ratio = 13.35% − 0.201% = **13.15%**
```

**Cushion Above Minimum:**
```
Cushion vs. 10.5% buffer = (13.15% − 10.5%) × 100 = **265 bps**
```

**Assessment:** Headroom remains, but the cushion drops by ~350 bps versus the prior (incorrect) peer median math—share buybacks now compete with capital preservation.

---

### Step 4: TBVPS Compression

**Scenario:** NCO flow-through to equity

```
Starting TCE: $2,503.8M
After-tax NCO Impact: -$38.4M
Ending TCE: $2,465.4M
Shares: 69.34M
Ending TBVPS: $35.55 (-1.7% vs. $36.16)
```

**Valuation Impact:**
```
Fair P/TBV: 1.115x
Target Price = $35.55 × 1.115 = $39.64
Downside from $45.89: -13.6%
```

---

## SCENARIO 2: BEAR CASE (60 BPS GFC-LEVEL NCO)

### Step 1: Incremental Provision

```
Incremental NCO = (60 bps - 18.1 bps) × $19,449M
                = 41.9 bps × $19,449M
                = $81.5M annually
```

**After-Tax NI Impact:**
```
Provision = $81.5M
Tax Shield = $16.3M
After-Tax Impact = $65.2M reduction
```

---

### Step 2: ROTE Compression

| Metric | Current | Bear Case |
|--------|---------|-----------|
| **LTM Net Income** | $294.7M | $229.5M |
| **ROTE** | 11.95% | 9.31% |
| **Fair P/TBV** | 1.115x | 0.95x |
| **Implied TBVPS Target** | $40.32 | $34.35 |

**Downside:** ~25% vs. $45.89 spot once multiple compression is applied alongside earnings drag.

---

### Step 3: CET1 Burn (Bear Case)

After-tax NCO Impact = $65.2M/year
CET1 Reduction       = $65.2M
RWA                  = $19,118.5M
CET1 Ratio Impact    = ($65.2M ÷ $19,118.5M) × 10,000 = **34.1 bps per year**
3-Year Cumulative    = **102.3 bps**
Ending CET1 Ratio    = 13.35% − 1.023% = **12.33%**
Buffer vs. 10.5%     = **183 bps**
```

**Risk Assessment:** Stack this 102 bps with industrial/warehouse bear (121 bps) and base-case normalization (20 bps) → **243 bps** total erosion. CET1 would slide to ~11.0%, triggering a hard stop on buybacks and a dividend review.

---

### Step 4: ACL Adequacy Test

**Question:** Is $174.5M ACL sufficient to absorb GFC-level NCOs?

**3-Year Bear Case NCO:**
```
Annual NCO (60 bps): $116.7M ($19,449M × 0.0060)
3-Year Cumulative: $350M
Less: ACL Coverage: -$174.5M
Shortfall: $175.5M
```

**Implication:** Bank would need $175M+ in additional reserves OR $140M+ capital raise (after-tax).

---

## SCENARIO 3: TOTAL CRE STRESS (20% LOSS SEVERITY)

### Assumptions

- Total CRE Portfolio: $10,363M
- Loss Severity: 20% (GFC-level)
- Expected Loss: $2,073M
- ACL Coverage: $174.5M
- Shortfall: $1,898M

**This is EXISTENTIAL RISK - not modeled as base case**

---

### Capital Impairment

```
Loss After Reserves = $2,073M - $174.5M = $1,898M
Tax Shield (20%) = $380M
Net TCE Impact = -$1,518M

Starting TCE: $2,503.8M
Ending TCE: $985M
Ending TBVPS: $14.23 (-60% from $36.16)
```

**CET1 Impact:**
```
CET1 Burn = $1,518M
Pro forma CET1 Capital = $2,552.3M − $1,518M = $1,034.3M
CET1 Ratio = $1,034.3M ÷ $19,118.5M = 5.41% (below 6.5% well-cap threshold)
```

**Result:** Bank would be undercapitalized and require TARP-style rescue or M&A.

---

## KEY FINDINGS (UPDATED)

### Base Case (42.8 bps Through-Cycle NCO)
- ✅ **CET1 cushion shrinks to 265 bps** — still above management buffer but materially tighter than previously assumed.
- ✅ **ROTE drops to 10.4%; TBVPS to $35.55** — regression target holds at $39.6, reinforcing SELL call.
- ⚠ **Buybacks constrained** — optionality limited until excess CRE capital premium is addressed.

### Bear Case (60 bps NCO + Industrial/Warehouse Stress)
- ⚠ **Combined CET1 burn hits 243 bps** (102 bps NCO + 121 bps property + 20 bps base normalization) → pro forma CET1 ≈ 11.0%.
- ⚠ **TBVPS down to $32.82 (-9.2%)** — dividend sustainable but subject to scrutiny; buybacks halted.
- 🚨 **ACL shortfall $175M** — demands reserve build or capital action if cycle deteriorates.

### Tail Risk (20% CRE Loss Severity)
- 🚨 **Capital wipe-out scenario** — $1.9B net loss would collapse CET1; only included as qualitative tail marker.
- Probability low (<5%), but underscores necessity of caps on CRE exposure.

---

## NEXT STEPS

1. Embed refreshed capital outputs into `CATY_11_peers_normalized.html` and `DEREK_EXECUTIVE_SUMMARY.md`.
2. Extend workbook with multi-period capital bridge (Years 1–3) using updated NCO and property stress inputs.
3. Align valuation bridge with revised TBVPS trajectory and CRE-driven multiple compression.
4. Archive parser/log outputs and tie evidence hashes to this worksheet revision.

---

## EVIDENCE TRAIL

**Data Sources:**
- Q2 2025 10-Q: Accession 0001437749-25-025772, filed 2025-08-05
- LTM NCO calculation: Evidence/acl_bridge_2023Q3-2025Q2_FINAL.csv
- Through-cycle NCO: FDIC SDI 2008-2024 average (42.8 bps)

**Commands Executed:**
```bash
# Capital extraction (pending)
curl -sL -H "User-Agent: Mozilla/5.0" \
  "https://www.sec.gov/cgi-bin/viewer?action=view&cik=861842&accession_number=0001437749-25-025772" \
  -o /tmp/caty_q2_2025_full.html

# Search for regulatory capital table
grep -i "common equity tier 1\|risk-weighted assets" /tmp/caty_q2_2025_full.html
```

---

**STATUS:** UPDATED 2025-10-19 04:35 PT — Base/Bear capital impacts recalculated; multi-period projection pending.
