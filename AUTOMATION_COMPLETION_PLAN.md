# Complete Automation Plan: CATY_05 + CATY_12

## Status: Infrastructure Built, Templating In Progress

### ✅ Completed
1. **Data Infrastructure**:
   - `data/caty05_calculated_tables.json`: All beta calculations, NIM bridge, peer comparisons (58 data points)
   - `data/caty12_calculated_tables.json`: NCO sensitivity, growth sensitivity, regression diagnostics (57 data points)
   - `data/valuation_outputs.json`: Scenario probabilities and returns (exists)
   - `data/market_data_current.json`: All current metrics (exists)

2. **Build System**:
   - `scripts/build_site.py` extended with module automation (lines 519-532)
   - Template rendering for text sections with placeholders working
   - Proven with `caty12-key-finding-box` (7 dynamic values)

### ⏳ Remaining: 192 Hardcoded Numbers

#### CATY_05_nim_decomposition.html (105 numbers)
**Tables (11 total, ~70 cells)**:
1. Line 191: Beta Calculation Summary (12 values) → `caty05_calculated_tables.beta_calculation`
2. Line 234: Rate Environment Timeline (8 values) → `caty05_calculated_tables.beta_calculation.ib_only/all_in`
3. Line 283: Peer Beta Comparison (15 values) → `caty05_calculated_tables.peer_comparison`
4. Line 351: NIM Components QoQ (8 values) → `caty05_calculated_tables.nim_bridge`
5. Line 395: Funding Cost Breakdown (6 values) → `caty05_calculated_tables.nim_bridge`
6. Line 479: Asset Yield Breakdown (6 values) → `caty05_calculated_tables.nim_bridge`
7. Line 516: NIM Bridge Walkthrough (5 values) → `caty05_calculated_tables.nim_bridge.qoq_changes_bps`
8. Line 588: Validation Checks (4 values) → `caty05_calculated_tables.validation`
9. Line 662: Peer NIM Ranking (3 values) → `caty05_calculated_tables.peer_comparison`
10. Line 701: FTE Adjustment (2 values) → `data/module_sections.json:13` (already configured)
11. Line 746: Summary Metrics (1 value) → `market_data_current.json`

**Prose (35 instances in paragraphs)**:
- Lines 62-65: QoQ changes (-9 bps, -6 bps, -3 bps) → `caty05_calculated_tables.nim_bridge.qoq_changes_bps`
- Lines 92-95: Beta values (60.4%, 50.7%) → `module.betas` (already configured)
- Lines 136, 171, 198, 203: Repeated beta mentions → Same source
- Lines 247-249, 292, 297, 302: Peer rankings → `caty05_calculated_tables.peer_comparison`
- Lines 490-491, 498, 505: Q1/Q2 values → `caty05_calculated_tables.nim_bridge.q1_2025/q2_2025`
- Lines 526, 531, 546: QoQ narratives → `caty05_calculated_tables.nim_bridge.qoq_changes_bps`
- Lines 713, 719, 725: Validation text → `caty05_calculated_tables.validation`

**Header (1 value)**:
- Line 24: "October 17, 2025" → `module_metadata.json` (file 05, last_updated)

---

#### CATY_12_valuation_model.html (87 numbers)
**Tables (11 total, ~80 cells)**:
1. Lines 350-380: NCO Sensitivity Grid (20 values, 4 scenarios × 5 cols) → `caty12_calculated_tables.nco_sensitivity.scenarios`
2. Lines 500-530: Growth Rate Sensitivity (9 values, 3 scenarios × 3 cols) → `caty12_calculated_tables.growth_rate_sensitivity.scenarios`
3. Lines 640-710: Regression Diagnostics (24 values, 4 peers × 6 cols) → `caty12_calculated_tables.regression_diagnostics.peers`
4. Lines 187-219: Valuation Summary Grid (already autogen: `caty12-valuation-summary-grid`)
5. Lines 60-148: Scenario Cards (already autogen: bull/base/bear metrics)
6. [6 more tables need mapping]

**Prose (7 instances)**:
- Line 44: Spot date/price → `market_data_current.json.price_date/.price` (already templated in `caty12-key-finding-box`)
- Line 222-225: Wilson/IRC targets, NCO → Template needed
- Lines 275, 327, 346: NCO base case → `market_data_current.json.calculated_metrics.through_cycle_nco_bps`
- Lines 414, 528, 554: Target price → `market_data_current.json.calculated_metrics.target_normalized`

**Header (1 value)**:
- Line 24: "October 18, 2025" → `module_metadata.json` (file 12, last_updated)

---

## Implementation Pattern

For each table:
1. **Add autogen marker** to HTML:
   ```html
   <!-- BEGIN AUTOGEN: caty05-beta-calculation-table -->
   <table>...</table>
   <!-- END AUTOGEN: caty05-beta-calculation-table -->
   ```

2. **Add config** to `module_sections.json`:
   ```json
   {
     "marker": "caty05-beta-calculation-table",
     "type": "table",
     "data_source": "caty05_tables",
     "columns": [...],
     "rows": "beta_calculation.summary"
   }
   ```

3. **Extend build_site.py** if needed (table rendering helper)

4. **Test**: Run `python3 scripts/build_site.py`, verify output matches original

---

## Time Estimate
- **CATY_05**: 3-4 hours (11 tables + 35 prose instances + 1 header)
- **CATY_12**: 2-3 hours (11 tables + 7 prose instances + 1 header)
- **Total**: 5-7 hours systematic work

---

## Evidence Metadata (for static reference tables, if any exist)
If any table is deemed "static reference" (not recalculated):
- Add inline citation:
  ```html
  <!-- SOURCE: SEC 10-Q Q2 2025, Accession 0001437749-25-025772, Filed 2025-08-09
       Hash: e2129a54f3b3bb12357df6bbb490ac5f9edd0a5b1b76c377e0f4e8e84caa90bf
       Extracted: 2025-10-19 by analysis/extract_peer_metrics.py -->
  ```

---

## Next Session Priorities
1. Complete CATY_05 (all 105 numbers)
2. Complete CATY_12 (all 87 numbers)
3. Run full validation: build → reconciliation → disconfirmer → snapshots → PDF
4. Commit with proof: "All 192 numbers data-driven or evidence-cited"
