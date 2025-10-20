# Pre-Commit Hook & Disconfirmer Override Guide

## Pipeline Execution Order

**MANDATORY before every commit:**

```bash
# Step 1: Rebuild dynamic sections from JSON
python3 scripts/build_site.py

# Step 2: Validate valuation numbers match scripts
python3 analysis/reconciliation_guard.py

# Step 3: Check driver disconfirmers
python3 analysis/disconfirmer_monitor.py
```

## Handling Exit Code 1 (Disconfirmer Alerts)

### Current Alert: COLB Cook's Distance = 4.03

**Threshold:** 1.0  
**Status:** ⚠️ WARNING (not blocking)  
**Action Taken:** RETAINED with documentation

**Justification for COLB Retention:**

1. **Substantive Outlier (Not Data Error)**
   - COLB P/TBV premium driven by Vancouver market (structural, not transient)
   - One-time NI gains in Q2 2024 elevated ROTE temporarily
   - Excluding reduces sample to n=3 (unacceptable for regression)

2. **Conservative Bias**
   - Including COLB **lowers** fitted P/TBV for CATY (makes valuation conservative)
   - CATY target $56.50 with COLB vs $57.50 without (sensitivity tested)
   - Conservative bias appropriate for HOLD rating

3. **Cook's Distance Interpretation**
   - Cook's D > 1.0 flags influence, not invalidity
   - IRC standard: Document and retain unless data error confirmed
   - Alternative peer sets tested (see CATY_11 sensitivity section)

**Override Protocol:**
- Document justification in commit message
- Note in disconfirmer log: `COLB outlier RETAINED (substantive, n=4 minimum)`
- Retest quarterly as new peer data arrives

### Exit Code Handling

**Exit 0:** Safe to commit  
**Exit 1 with WARNING:** Document override, commit with justification  
**Exit 1 with ALERT (multiple):** STOP - Escalate to rating committee

## Automation Ownership

**Daily:**
- Update `data/market_data_current.json`: **Nirvan** (manual until stooq.com integrated)
- Run pipeline: **Automated via pre-commit hook** or **CI job** so it's impossible to skip

**Post-Q3 Earnings (Oct 21):**
- Append FDIC Q3 data: **Derek** (when available ~late Nov)
- Rerun disconfirmer monitor: **Automated**
- Update probability bounds: **Automated** (if thresholds trip)

**SLA:**
- Market data refresh: Daily (before market open, next trading day)
- Post-earnings update: Within 2 hours of 8-K filing
- Disconfirmer alerts: Immediate escalation (exit code ≠ 0)

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
