# PROJECT GROUND TRUTH - Fixing the Foundation

**Date:** October 21, 2025 05:20 UTC
**Status:** INITIATED - Post COVID Test Failure
**Goal:** Wire valuation calculations into automation pipeline

---

## GHCP ARCHITECTURAL GUIDANCE (Integrated)

### Root Problem Identified:
**Valuation targets and returns are hardcoded in JSON, not calculated by scripts.**

### GHCP's 4 Critical Findings:

1. **Valuation scripts exist but aren't called by update_all_data.py**
   - analysis/valuation_bridge_final.py (ORPHANED)
   - analysis/probability_weighted_valuation.py (ORPHANED)
   - Scripts only print to console, outputs never integrated

2. **No provenance audit for calculated metrics**
   - market_data_current.json has targets/returns with no source mapping
   - Can't trace which script generated which value

3. **Valuation metadata lacks per-method freshness**
   - valuation_outputs.json has single "last_updated" timestamp
   - No way to know if Wilson, Regression, Monte Carlo are current

4. **COVID crash regression test doesn't exist in CI**
   - Failure scenario documented, but not automated
   - No guarantee future changes won't break recalculation

---

## GHCP RECOMMENDED ARCHITECTURE

### Data Flow (Correct):
```
1. Fetch live price (scripts/fetch_live_price.py)
2. Pull SEC/FDIC/peer data (update_all_data.py steps 1-3)
3. Merge to canonical JSONs (merge_data_sources.py)
4. *** NEW *** Run valuation orchestrator → calculate targets/returns
5. Update evidence metadata
6. Build site (build_site.py)
7. Reconciliation guard
```

### Key Principle:
**market_data_current.json is OUTPUT of calculations, not INPUT**

Current (wrong):
- Targets hardcoded in JSON
- Scripts read JSON, print results, don't write back

Correct (GHCP):
- Scripts calculate targets from fundamentals
- Scripts WRITE results to JSON
- Templates render calculated values

---

## IMPLEMENTATION PLAN (GHCP-Guided)

### Phase 1: Ground Truth Audit (6 hours)

**Task 1.1: Inventory market_data_current.json (2 hours)**
```
Goal: Map every field to source

For each field in calculated_metrics:
- Source: API (yfinance, SEC, FDIC) or Calculated (script name) or Manual
- Update Frequency: Daily, Quarterly, Annual
- Calculation Logic: Formula or script reference
- Dependencies: Which other fields required

Output: data/field_provenance.json
```

**Task 1.2: Audit valuation scripts (2 hours)**
```
Scripts to audit:
- analysis/valuation_bridge_final.py
- analysis/probability_weighted_valuation.py
- analysis/nco_probability_analysis.py (if relevant)
- analysis/valuation_sensitivity.py (if relevant)

For each script:
- What does it calculate?
- What are inputs?
- What are outputs?
- Where do outputs go? (currently: nowhere)
- Is it idempotent (safe to re-run)?

Output: VALUATION_SCRIPTS_AUDIT.md
```

**Task 1.3: Document missing integrations (2 hours)**
```
Identify gaps:
- Which calculated metrics have NO source script?
- Which scripts produce outputs not consumed anywhere?
- Which metrics are duplicated across multiple files?

Output: INTEGRATION_GAPS.md
```

### Phase 2: Assumptions Layer (8 hours)

**Task 2.1: Build Valuation Orchestrator (4 hours - CODEX)**
```
Create: scripts/calculate_valuation_metrics.py

Responsibilities:
1. Load current price from market_data_current.json
2. Load fundamentals (ROTE, TBVPS, NCO, etc.) from merged data
3. Call valuation functions:
   - calculate_regression_target() → regression analysis
   - calculate_normalized_target() → Gordon Growth with through-cycle NCO
   - calculate_wilson_bounds() → Wilson score probability weighting
   - calculate_monte_carlo() → if available
4. Calculate ALL returns: (target - price) / price
5. Generate timestamps for each method
6. Write outputs to:
   - data/valuation_outputs.json (detailed method results)
   - data/market_data_current.json.calculated_metrics (summary for templates)
7. Exit code 0 on success, non-zero on failure

Success Criteria:
- Changing price → running orchestrator → all returns update correctly
- COVID test passes: $47 → $28.20 → returns show +84.5%, +100%, +39%
```

**Task 2.2: Refactor Existing Scripts to Callable Functions (2 hours - CODEX)**
```
Update analysis/valuation_bridge_final.py:
- Extract logic into calculate_regression() and calculate_normalized() functions
- Return dict with target, method_details, confidence
- Keep main() for CLI compatibility

Update analysis/probability_weighted_valuation.py:
- Extract into calculate_wilson_weighted() function
- Return dict with wilson_target, probabilities, bounds
- Document probability assumptions
```

**Task 2.3: Integrate into update_all_data.py (1 hour - CODEX)**
```
Add between merge (Step 4) and build (Step 6):

# Step 4.5: Calculate valuation metrics
run_step([sys.executable, "scripts/calculate_valuation_metrics.py"], "calculate_valuation_metrics")
append_log("calculate_valuation_metrics.py: Recalculated all valuation targets and returns")

This ensures every update_all_data.py run regenerates valuations.
```

**Task 2.4: Timestamp Propagation (1 hour - CODEX)**
```
Update valuation orchestrator to write:

data/valuation_methods.json:
{
  "methods": [
    {
      "id": "wilson_95",
      "name": "Wilson 95% Upper Bound",
      "last_calculated": "2025-10-21T05:30:00Z",
      "inputs_used": {
        "price": 47.00,
        "regression_target": 56.50,
        "normalized_target": 39.32
      },
      "output": {
        "target": 48.70,
        "return_pct": 10.7
      }
    },
    // ... other methods
  ]
}

This enables reconciliation dashboard to show method freshness.
```

### Phase 3: Build Layer (Already Complete)

**Status:** Templates work correctly, just rendering hardcoded values currently.

**Post-Phase 2:** Templates will automatically render calculated values once orchestrator runs.

### Phase 4: Validate Layer (2 hours)

**Task 4.1: Automated COVID Crash Test (1 hour - CODEX)**
```
Create: scripts/tests/test_covid_crash.py

Test:
1. Save original price
2. Set price to COVID scenario ($28.20, -40%)
3. Run: python3 scripts/update_all_data.py
4. Assert:
   - Wilson return = +84.5% ± 0.5%
   - Regression return = +100.4% ± 0.5%
   - Normalized return = +39.4% ± 0.5%
   - All timestamps = current date
5. Restore original price

Add to CI: Run this test on every PR
```

**Task 4.2: Provenance Validation (1 hour)**
```
Add to reconciliation_guard.py:
- Check all calculated_metrics have source script documented
- Check all timestamps are within 24 hours
- Check valuation methods last_calculated matches current run
```

---

## SUCCESS CRITERIA

### Must Pass COVID Test:
```bash
# Simulate crash
python3 -c "import json; d=json.load(open('data/market_data_current.json')); d['price']=28.20; json.dump(d, open('data/market_data_current.json','w'), indent=2)"

# Run pipeline
python3 scripts/update_all_data.py

# Verify returns recalculated
grep "Wilson.*84.5%\|Regression.*100" index.html

# Must find correct returns
```

### Must Have Full Provenance:
Every field in market_data_current.json must have documented source (API or calculation script).

### Must Have Current Timestamps:
All valuation methods must show today's date after update_all_data.py runs.

---

## TIMELINE

| Phase | Est Time | Dependencies |
|-------|----------|--------------|
| Phase 1: Ground Truth Audit | 6 hours | None |
| Phase 2: Assumptions Layer | 8 hours | Phase 1 complete |
| Phase 3: Build Layer | 0 hours | Already done |
| Phase 4: Validate Layer | 2 hours | Phase 2 complete |

**TOTAL: 16 hours to true automation**

---

## WHAT WE KEEP

✅ HTML templates (31 autogen markers)
✅ Data fetchers (SEC, FDIC, yfinance)
✅ Merge logic (merge_data_sources.py)
✅ Build engine (build_site.py)
✅ Validation scripts (reconciliation_guard, disconfirmer_monitor)
✅ Module files (CATY_01-17)

---

## WHAT WE FIX

❌ Valuation integration (scripts orphaned)
❌ Return calculations (hardcoded, not dynamic)
❌ Timestamp management (stale Oct 18/19 dates)
❌ Provenance documentation (missing source mapping)
❌ COVID test (doesn't exist in CI)

---

## COMMITMENT

**No more "100% complete" claims until:**
1. COVID crash test passes
2. All timestamps current
3. All valuation methods recalculate
4. Full provenance documented

**Realistic Assessment:** 40% complete overall
- Data Fetching: 90% ✅
- Calculations: 10% ❌
- Templates: 80% ✅
- Testing: 0% ❌

---

**Next:** Start Phase 1 - Ground Truth Audit with GHCP + Codex collaboration
