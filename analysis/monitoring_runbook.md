# Monitoring Runbook - Post-Q3 Earnings

**Event:** Q3 2025 Earnings Release
**Expected Date:** October 21, 2025 (after market close)
**Owner:** Derek review desk

---

## Pre-Earnings Preparation

**Timing:** October 19-20, 2025 (Weekend before Oct 21 earnings)

1. Review current probability dashboard (evidence/probability_dashboard.md)
2. Note current Wilson bounds: 74/26 (26% upper bound)
3. Prepare questions for management:
   - Q3 NCO rate and trends
   - CRE portfolio updates
   - Reserve adequacy commentary
   - Capital allocation plans
4. **CRITICAL:** EWBC reports same day (Oct 21, 2pm PT) - see `analysis/rapid_memo_workflow_oct21.md` for 60-minute speed-read protocol
5. Monitor peer filings: `python3 analysis/fetch_peer_filings.py EWBC --cutoff 2025-10-20` (check Oct 21 morning)

---

## Post-Earnings Execution

**Timing:** October 21, 2025 (after market close)

**CRITICAL NOTE:** FDIC Q3 data will NOT be available until late November (~55 days after Sept 30). Use 10-Q reported NCO initially.

### Step 1: Data Collection
- Download Q3 2025 10-Q from SEC EDGAR
- Extract Q3 NCO rate from financials
- Note any CRE-related disclosures
- Capture management commentary on credit

### Step 2: FDIC Data Update
- Wait for FDIC Q3 2025 call report (typically 30-45 days after quarter-end)
- Expected availability: Mid-November 2025
- Download updated NTLNLSCOQR field
- Append to evidence/raw/fdic_CATY_NTLNLSCOQR_timeseries.csv

### Step 3: Probability Recalculation
**Script:** `python3 analysis/nco_probability_analysis.py`

**Actions:**
1. Update script with Q3 data point
2. Rerun Wilson 95% confidence intervals
3. Calculate new breach probabilities:
   - Post-2014 rate
   - Post-2008 rate
4. Update upper bound (currently 26%)

### Step 4: Valuation Refresh
**Script:** `python3 analysis/probability_weighted_valuation.py`

**Actions:**
1. Input new Wilson upper bound
2. Recalculate expected returns:
   - Data-anchored (85/15 or updated)
   - Wilson 95% upper (74/26 or updated)
3. Compare to +15% BUY threshold

### Step 5: Rating Decision
**Policy:** analysis/rating_policy.md

**Decision Tree:**
- If Wilson upper bound < 21.5% tail: **Entire band > +15% → UPGRADE TO BUY**
- If Wilson upper bound 21.5-35% tail: **HOLD (current)**
- If Wilson upper bound > 35% tail: **Consider SELL**

**Auto-Flip Trigger:**
```
IF (1 - wilson_upper_bound) × target_current + wilson_upper_bound × target_normalized > current_price × 1.15
THEN rating = BUY
```

### Step 6: Documentation
1. Update evidence/probability_dashboard.md with new numbers
2. Add SHA256 hash to evidence/README.md
3. Update DEREK_EXECUTIVE_SUMMARY.md if rating changes
4. Update index.html rating badge if needed
5. **Run reconciliation guard:** `python3 analysis/reconciliation_guard.py`
   - Validates published numbers match script outputs
   - Must pass (exit code 0) before committing
   - If fails, fix discrepancies in README.md/index.html
6. **Regenerate site sections:** `python3 scripts/build_site.py`
   - Rebuilds valuation dashboard, module navigation, and evidence provenance table from JSON sources
   - Appends run status to `logs/automation_run.log`
7. **Execute disconfirmer monitor:** `python3 analysis/disconfirmer_monitor.py`
   - Exit code ≠ 0 means a driver breached threshold—remediate and rerun before publishing
8. Git commit with timestamp
9. Push to GitHub

### Step 7: Notification
**If rating changes:**
- Update site immediately
- Document in commit message
- Notify Derek review desk

**If rating unchanged:**
- Update dashboard only
- Log in evidence/README.md

---

## Kill-Switches (Immediate Action)

**If Q3 shows:**
- NCO >35 bps: Run emergency stress test, consider SELL
- CET1 <10.5%: Review capital adequacy, adjust tail weight
- Classified loans spike >25%: Increase normalization probability

---

## Owner Assignment

**Primary:** Derek review desk
**Scripts:** Claude (execution as directed)
**Evidence Archive:** Claude (SHA256 logging)
**Rating Sign-Off:** Derek

---

## Continuous Improvement Backlog (Commit-Driven)

### ✅ Completed (October 18, 2025)
- ✅ **HTML Companions Created:** CATY_13 (RIM), CATY_14 (Monte Carlo), CATY_15 (ESG), CATY_16 (COE) - all IRC appendices now web-accessible
- ✅ **Scenario Tables Refreshed:** index.html and CATY_12_valuation_model.html now include IRC Blended ($51.39) + Wilson 95% ($51.74) + 42.8 bps NCO base
- ✅ **Reconciliation Guard Built:** `analysis/reconciliation_guard.py` validates published numbers vs script outputs (wired into Step 6 above)

### ✅ Completed (Oct 19, 2025 - Automation Sprint)
- ✅ **Pre-Commit Hook Installed:** `.git/hooks/pre-commit` auto-validates valuation numbers, blocks commits with discrepancies (see `analysis/PRE_COMMIT_HOOK_GUIDE.md`)
- ✅ **ESG KPI Dashboard Delivered:** `analysis/esg_kpi_dashboard.py` + `evidence/esg_kpi_data.json` quantify material ESG drivers and valuation impact
- ✅ **Peer Question Bank Constructed:** `analysis/peer_preearnings_questionbank.md` covers Oct 17-21 peer calls with triggers to update CATY probabilities

### ✅ Completed (Oct 19, 2025 - CI Integration)
- ✅ **CI Reconciliation Guard:** `.github/workflows/reconciliation-guard.yml` validates valuation numbers on every push/PR (required check, blocks merge on failure)

### ✅ Completed (Oct 19, 2025 - ESG & Peer Prep)
- ✅ **ESG Dashboard Surfaced:** `CATY_17_esg_kpi_dashboard.html` + index summary cards expose valuation impact on-site
- ✅ **Peer Monitoring Template:** `analysis/peer_preearnings_monitoring_template.md` structured for Oct 17 EWBC/COLB read-through

### 🔄 Pending
- Populate peer question bank responses with real-time takeaways as EWBC/COLB report (target: Oct 17 end-of-day).
- Stand up rapid-turnaround memo workflow (template + checklist) for distributing Oct 17 insights within 2 hours.

---

**Next Execution:** October 21, 2025 (after market close, post Q3 earnings)
**Generated:** 2025-10-19 05:52 PT
