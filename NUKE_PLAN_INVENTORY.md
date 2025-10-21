# PROJECT NUKE: Template Conversion Inventory

**Status:** In Progress (11/60 sections completed ~18%)
**Last Updated:** October 21, 2025 00:15 UTC

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
| 829-869 | Valuation Deep Dive | market_data_current.json → calculated_metrics | ✅ DONE |
| 871-913 | Scenario Analysis Table | market_data_current.json → calculated_metrics | ✅ DONE |
| 1710+ | Investment Risks | market_data_current.json → investment_risks | ✅ DONE |
| 2201-2206 | Footer Timestamp | market_data_current.json → report_metadata | ✅ DONE |

**Total: 11 sections auto-generate from JSON**

---

## Sections REMAINING (Hardcoded) ⚠️

### High Priority (Embedded Facts):

| Line Range | Section | Hardcoded Facts | JSON Source Needed | Priority |
|------------|---------|-----------------|-------------------|----------|
| ~150-250 | Company Overview | Market cap, shares, fiscal year | market_data_current.json | HIGH |
| ~700-900 | Positive Catalysts | NIM targets, efficiency goals | data/catalysts.json (NEW) | HIGH |
| ~1400-1600 | Peer Positioning | Peer metrics comparison | data/caty11_peers_normalized.json | MEDIUM |
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

1. **data/catalysts.json** - Forward-looking drivers
   - NIM expansion targets
   - Efficiency ratio goals
   - Texas branch expansion timeline

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

### Phase 5: Company Overview + Catalysts (Next)
- Lines 150-250, 700-900
- Create catalysts.json
- Est: 2 hours (Codex)

### Phase 6: Peer Positioning + Historical
- Lines 1400-1600, 1650-1800
- Use existing peer JSON + create historical JSON
- Est: 1.5 hours (Codex)

### Phase 7: Final Cleanup
- Remove any remaining stale refs
- Full end-to-end test
- Est: 30 min

**Total Remaining: ~4 hours**

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

**Current State: 18% complete (11/60 sections). Phase 4 delivered by Codex. Momentum strong.**
