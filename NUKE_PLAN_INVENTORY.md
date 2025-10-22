# PROJECT NUKE: Template Conversion Inventory

**Status:** In Progress (15/60 sections completed ~25%) - ALL DATA SECTIONS COMPLETE
**Last Updated:** October 21, 2025 03:05 UTC

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
| 866-952 | Peer Positioning | data/caty11_peers_normalized.json → peers | ✅ DONE |
| 871-913 | Scenario Analysis Table | market_data_current.json → calculated_metrics | ✅ DONE |
| 1599-1730 | Positive Catalysts | data/catalysts.json → positive_catalysts | ✅ DONE |
| 1619-1718 | Historical Context | data/historical_context.json → milestones/performance | ✅ DONE |
| 1710+ | Investment Risks | market_data_current.json → investment_risks | ✅ DONE |
| 2201-2206 | Footer Timestamp | market_data_current.json → report_metadata | ✅ DONE |

**Total: 15 sections auto-generate from JSON**

---

## Sections REMAINING (Hardcoded) ⚠️

### High Priority (Embedded Facts):

| Line Range | Section | Hardcoded Facts | JSON Source Needed | Priority |
|------------|---------|-----------------|-------------------|----------|
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

2. **data/historical_context.json** ✅ COMPLETE
   - 6 historical milestones (1962, 1997, GFC, COVID, 2021, 2025)
   - Through-cycle performance metrics
   - Key strengths from track record
   - Created: October 21, 2025

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

### Phase 6: Peer Positioning ✅ COMPLETE
- Lines 866-952 (peer comparison table + insights)
- Wired to existing data/caty11_peers_normalized.json
- Renderer: render_peer_positioning()
- Completed: October 21, 2025 (Codex delivery)

### Phase 7: Historical Context ✅ COMPLETE
- Lines 1619-1718 (historical milestones timeline + performance)
- Created data/historical_context.json with 6 milestones
- Renderer: render_historical_context()
- Completed: October 21, 2025 (Codex delivery)

### Phase 8: Final Cleanup (Next)
- Remove any remaining stale refs
- Full end-to-end test
- Est: 30 min

**Total Remaining: ~30 minutes (cleanup only)**

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

**Current State: 25% complete (15/60 sections). ALL DATA SECTIONS COMPLETE. Phases 4-7 delivered by Codex. Only cleanup remains (~30 min).**
