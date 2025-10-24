# PROJECT NUKE: Complete Template Conversion Plan

**Status:** APPROVED - Execution Starting
**Timeline:** 3 hours
**Goal:** Convert index.html from 60+ hardcoded instances to 100% template-driven architecture

---

## Problem Statement

**Current:** index.html contains hardcoded facts. Every price update requires 60 manual edits.
**Target:** 100% regeneration from JSON. One command updates everything.

---

## What We Keep (Proven Work)

✅ All data pipelines (fetch_live_price.py, SEC EDGAR, FDIC, DEF14A)
✅ All JSON data files (market_data_current.json with live $47.00)
✅ All validation scripts (reconciliation_guard, disconfirmer_monitor)
✅ All schemas (def14a.schema.json)
✅ build_site.py template engine (expand, don't rebuild)
✅ CATY_01-17 module files (audit separately)
✅ All CSS, charts.js, theme-toggle.js

---

## What We Nuke

❌ Hardcoded narrative paragraphs in index.html (lines 1-600)
❌ Stale timestamps (60+ instances)
❌ Any section without autogen markers

---

## Execution Phases

### Phase 1: Systematic Audit (30 min)
- Map every hardcoded section to JSON source
- Identify pure commentary vs fact-based sections
- Output: NUKE_PLAN_INVENTORY.md

### Phase 2: Template Expansion (2 hours - Codex)
- Add autogen markers for ALL index.html sections
- Expand module_sections.json configs
- Update build_site.py rendering functions
- Test: grep for "$45.89\|1.269" returns zero

### Phase 3: Validation (30 min)
- Run: python3 scripts/update_all_data.py
- Verify: 100% regenerated, no stale data
- Browser check: All dates Oct 20, price $47.00
- Push to live

---

## Success Criteria

**Before:** 60 manual edits per price update
**After:** 1 command regenerates everything

---

**Execution starting. Updates posted to GitHub.**
