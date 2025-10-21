# PROJECT NUKE: Template Conversion Inventory

**Status:** In Progress (13/60 sections completed ~22%)
**Last Updated:** October 21, 2025 01:40 UTC

---

## Sections COMPLETED (Template-Driven) ✅

| Line Range | Section | JSON Source | Status |
|------------|---------|-------------|--------|
| 6-8 | Page Title | market_data_current.json → report_metadata | ✅ DONE |
| 51-58 | Report Metadata Header | market_data_current.json → report_metadata | ✅ DONE |
| 325+ | Price Target Grid | market_data_current.json → calculated_metrics | ✅ DONE |
| 375-387 | Investment Thesis Paragraph | market_data_current.json → narrative_prose | ✅ DONE |
| 380+ | Key Findings Bullets | market_data_current.json → calculated_metrics | ✅ DONE |
| 420-500 | Reconciliation Dashboard | Valuation scripts (dynamic) | ✅ DONE |
| 630+ | Recent Developments | data/recent_developments.json | ✅ DONE |
| 643-667 | Company Overview | data/catalysts.json → company_overview | ✅ DONE |
| 829-869 | Valuation Deep Dive | market_data_current.json → calculated_metrics | ✅ DONE |
| 871-913 | Scenario Analysis Table | market_data_current.json → calculated_metrics | ✅ DONE |
| 1599-1730 | Positive Catalysts | data/catalysts.json → positive_catalysts | ✅ DONE |
| 1710+ | Investment Risks | market_data_current.json → investment_risks | ✅ DONE |
| 2201-2206 | Footer Timestamp | market_data_current.json → report_metadata | ✅ DONE |

**Total: 13 sections auto-generate from JSON**

---

## Sections REMAINING (Hardcoded) ⚠️

### High Priority (Embedded Facts):

| Line Range | Section | Hardcoded Facts | JSON Source Needed | Priority |
|------------|---------|-----------------|-------------------|----------|
| ~1400-1600 | Peer Positioning | Peer metrics comparison | data/caty11_peers_normalized.json | HIGH |
| ~1650-1800 | Historical Context | Past performance, inflection points | data/historical_context.json (NEW) | LOW |
| ~1950-2100 | Appendix / Methodology | Formula explanations | Static (OK to keep hardcoded) | LOW |

### Pure Commentary (Can Stay Hardcoded):

| Line Range | Section | Type | Action |
|------------|---------|------|--------|
| ~100-140 | Introduction Prose | Pure commentary | KEEP AS-IS |
| ~2050-2150 | Disclosures | Legal/compliance | KEEP AS-IS |
| ~2150-2200 | Data Sources List | Methodology | KEEP AS-IS |

---

## Data Files Needed (NEW):

1. **data/catalysts.json** ✅ COMPLETE
   - Company overview facts (market cap, shares, branches)
   - 5 positive catalysts (NIM, efficiency, Texas, credit, digital)
   - Created: October 21, 2025

2. **data/historical_context.json** - Past inflection points
   - GFC survival (no TARP)
   - 2020 pandemic pivot
   - Key milestones

3. **Scenario Analysis** - Already in market_data_current.json
   - Just needs renderer function in build_site.py

---

## Phased Approach (Remaining Work):

### Phase 4: Scenario Analysis + Valuation Deep Dive ✅ COMPLETE
- Lines 829-869 (valuation deep dive), 871-913 (scenario table)
- Renderers: render_scenario_analysis_table(), render_valuation_deep_dive()
- Completed: October 21, 2025 (Codex delivery)

### Phase 5: Company Overview + Catalysts ✅ COMPLETE
- Lines 643-667 (company overview), 1599-1730 (catalysts)
- Created data/catalysts.json with 5 catalysts
- Renderers: render_company_overview(), render_positive_catalysts()
- Completed: October 21, 2025 (Codex delivery)

### Phase 6: Peer Positioning (Next)
- Lines ~1400-1600
- Use existing data/caty11_peers_normalized.json
- Est: 1 hour (Codex)

### Phase 7: Historical Context
- Lines 1650-1800
- Create data/historical_context.json
- Est: 45 min (Codex)

### Phase 8: Final Cleanup
- Remove any remaining stale refs
- Full end-to-end test
- Est: 30 min

**Total Remaining: ~2.5 hours**

---

## Success Criteria (Final):

**Test:**
```bash
# Change price to $50.00
python3 -c "import json; d=json.load(open('data/market_data_current.json')); d['price']=50.00; json.dump(d, open('data/market_data_current.json','w'), indent=2)"

# Rebuild everything
python3 scripts/update_all_data.py

# Verify ZERO hardcoded instances remain
grep '\$47.00\|47.00\|$45.89\|45.89' index.html  # Should return ZERO (or only in comments)

# Revert
python3 scripts/fetch_live_price.py
python3 scripts/update_all_data.py
```

**Pass Criteria:**
- ✅ 100% of facts update when JSON changes
- ✅ Zero manual edits to index.html required
- ✅ Browser shows all sections current

---

**Current State: 22% complete (13/60 sections). Phases 4-5 delivered by Codex. Momentum excellent. ~2.5 hours to 100%.**
