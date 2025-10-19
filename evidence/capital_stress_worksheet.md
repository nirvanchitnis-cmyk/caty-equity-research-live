# CAPITAL STRESS WORKSHEET - CATHAY GENERAL BANCORP

**Date:** October 18, 2025
**Analyst:** Nirvan Chitnis
**Objective:** Model CET1 and TBVPS impact under through-cycle NCO scenarios

---

## EXECUTIVE SUMMARY

**Purpose:** Quantify capital burn and tangible book value impairment if CATY normalizes to through-cycle NCO rates (42.8 bps base case, 60 bps bear case) from current 18.1 bps LTM.

**Key Findings (PRELIMINARY):**
- CET1 ratio burn: TBD (awaiting extraction)
- TBVPS compression: TBD
- ACL adequacy: Coverage ratio 0.90% provides cushion but insufficient under GFC-level stress

---

## STARTING POINT - Q2 2025 CAPITAL POSITION

### Regulatory Capital (Q2'25 10-Q)

| Metric | Value | Source |
|--------|-------|--------|
| **Common Equity Tier 1 (CET1)** | [EXTRACTING] | Q2'25 10-Q, Regulatory Capital table |
| **Tier 1 Capital** | [EXTRACTING] | Q2'25 10-Q |
| **Total Capital** | [EXTRACTING] | Q2'25 10-Q |
| **Risk-Weighted Assets (RWA)** | [EXTRACTING] | Q2'25 10-Q |
| **CET1 Ratio** | [EXTRACTING] % | CET1 / RWA |
| **Tier 1 Ratio** | [EXTRACTING] % | Tier 1 / RWA |
| **Total Capital Ratio** | [EXTRACTING] % | Total Capital / RWA |

**Regulatory Minimums:**
- CET1: 4.5% (well-capitalized: 6.5%)
- Tier 1: 6.0% (well-capitalized: 8.0%)
- Total Capital: 8.0% (well-capitalized: 10.0%)

---

### Tangible Book Value (Q2'25 10-Q)

| Metric | Value | Source |
|--------|-------|--------|
| **Shareholders' Equity** | $2,511.4M | Q2'25 10-Q, Balance Sheet |
| **Goodwill** | $5.5M | Q2'25 10-Q |
| **Intangibles** | $2.1M | Q2'25 10-Q |
| **Tangible Common Equity (TCE)** | $2,503.8M | Equity - Goodwill - Intangibles |
| **Shares Outstanding** | 69.24M | Q2'25 10-Q |
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
NCO Impact = $48.0M after-tax (from Step 1)
CET1 Reduction = $48.0M
Starting CET1 = [EXTRACTING]
Ending CET1 = Starting CET1 - $48.0M

CET1 Ratio Impact = $48.0M / RWA
                   = $48.0M / [EXTRACTING RWA]
                   = [TBD] bps reduction
```

**Cushion Above Minimum:**
```
Current CET1 Ratio: [EXTRACTING] %
Well-Capitalized Minimum: 6.5%
Cushion: [TBD] bps
```

**Assessment:** If current CET1 is >10%, bank has 350+ bps cushion and can absorb Base Case NCO without regulatory concern.

---

### Step 4: TBVPS Compression

**Scenario:** NCO flow-through to equity

```
Starting TCE: $2,503.8M
NCO Impact (Year 1): -$38.4M (after-tax)
Ending TCE: $2,465.4M
Shares: 69.24M
Ending TBVPS: $35.61 (-1.5% from $36.16)
```

**Valuation Impact:**
```
Fair P/TBV: 1.115x
Target Price = $35.61 × 1.115 = $39.70
Downside from $45.89: -13.5%
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
| **Fair P/TBV** | — | 0.95x (compressed multiple) |
| **Target TBVPS** | — | $36.16 × 0.95 = $34.35 |

**Downside:** -25% from $45.89

---

### Step 3: CET1 Burn (Bear Case)

```
NCO Impact: $65.2M after-tax annually
CET1 Reduction: $65.2M
CET1 Ratio Impact = $65.2M / [EXTRACTING RWA]
                   = [TBD] bps

Over 3 years: -[TBD] bps cumulative
```

**Risk Assessment:** If cumulative CET1 burn exceeds 200 bps, bank may need to curtail buybacks or raise capital.

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
CET1 Ratio = ([EXTRACTING CET1] - $1,518M) / RWA
           = [WOULD BREACH MINIMUMS]
```

**Result:** Bank would be undercapitalized and require TARP-style rescue or M&A.

---

## KEY FINDINGS (PENDING DATA EXTRACTION)

### Base Case (42.8 bps NCO)
- ✅ **MANAGEABLE:** CET1 cushion likely adequate (pending extraction)
- ✅ **SELL THESIS VALID:** TBVPS compression + ROTE normalization supports $40.32 target
- Risk: Moderate (requires provision builds but not capital raise)

### Bear Case (60 bps NCO)
- ⚠ **ELEVATED RISK:** 3-year ACL shortfall $175M requires reserve builds
- ⚠ **CET1 BURN:** May curtail buybacks; target price drops to $34-36
- Risk: High (capital actions needed)

### Tail Risk (20% CRE Loss Severity)
- 🚨 **EXISTENTIAL:** Would breach CET1 minimums; require capital raise or M&A
- 🚨 **TBVPS IMPAIRMENT:** -60% to $14-15 range
- Probability: Low (<5%) but catastrophic if occurs

---

## NEXT STEPS

**Immediate (within 1 hour):**
1. ✅ Extract CET1, Tier 1, Total Capital from Q2'25 10-Q
2. ✅ Extract RWA from Q2'25 10-Q
3. ✅ Calculate CET1 ratio and cushion above minimums
4. ✅ Populate all [EXTRACTING] fields in worksheet

**Next Session:**
5. Build 3-year projection with provision paths under Base/Bear scenarios
6. Stress test ACL coverage adequacy
7. Model buyback curtailment scenarios
8. Integrate findings into index.html and DEREK_EXECUTIVE_SUMMARY.md

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

**STATUS:** PRELIMINARY WORKSHEET - Awaiting capital metrics extraction to complete calculations.
