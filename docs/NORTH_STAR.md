# North Star Vision: Project Ground Truth

> **"I can close my eyes and I can imagine an equity research report for Monster Beverage, right? To the same canonical extent... Cathay Bank is the paradigmatic example of what I want to emulate across any company."**
>
> — Nirvan Chitnis, October 2025

---

## The Vision (30,000 Feet)

**Think of a company.**

BOOM → CFA Institute Research Challenge-grade equity research report. Full dashboard. 19 analytical modules. Every number traced to source. Deterministic. Reproducible. Audit-grade.

**Think of a company.**

BOOM → Full stress-tested audit plan website. Risk assessment. Control matrix. Materiality calculations. As if onboarding a new client. Professional-grade. Evidence-backed.

**One system. Two offshoots. Infinite companies.**

This is not a vision for 2030. This is the architecture we are building **now**. The scaffolding is live. The foundation is being poured. Cathay General Bancorp (CATY) is the proving ground.

---

## The Ground Truth Thesis

### The Problem with Equity Research Today

Every equity research report starts from scratch:
- Analysts manually pull data from Edgar, Bloomberg, CapIQ
- Calculations live in opaque Excel models with no audit trail
- Provenance is an afterthought ("Source: Company filings")
- Replication is impossible without the original analyst's spreadsheet
- Quality varies wildly by analyst, firm, and deadline pressure

**The industry has no canonical base layer.**

### The Ground Truth Solution

Build a **universal, deterministic, sector-aware data foundation** where:

1. **Every company resolves to a single source of truth**
   - Ticker → CIK → SEC EDGAR iXBRL facts (definitive)
   - DEF 14A proxy data (governance, compensation, ownership)
   - Investor Relations (press releases, decks, transcripts)
   - Sector-specific regulators (FDIC for banks, FDA for biopharma, FERC for utilities)

2. **Every metric carries immutable provenance**
   - `source_url` (where it came from)
   - `xbrl_tag` or `extractor` (how it was derived)
   - `retrieved_at` (when)
   - `sha256` (integrity proof)
   - `calc_ref` (which script, which version)
   - `confidence` (extraction certainty)
   - `page_numbers` or `dom_path` (exact location in source document)

3. **A routing system determines what to pull, based on what the company IS**
   - Banking (SIC 6020-6099) → FFIEC Call Reports, net interest margin decomposition, credit quality
   - Biopharma (SIC 2834) → FDA approvals, clinical trial pipeline, PDUFA calendar
   - Consumer/CPG (SIC 2080-2099) → brand KPIs, channel mix, price/pack architecture
   - Tech/SaaS (SIC 7372) → ARR, net retention, RPO, cohort margins
   - **No monolith. Domain-specific knowledge. Pluggable pipelines.**

4. **Two research engines consume the same ground truth**
   - **Equity Research Engine** → Valuation models, peer comps, sensitivity analysis, investment thesis
   - **Audit Research Engine** → Risk assessment, control evaluation, materiality calculations, audit plan

**One canonical base. Two professional outputs. Deterministic by ticker.**

---

## Why We Started with CATY (The Proving Ground)

> **"Cathay Bank... was quite difficult. You never know. For mortgage banks, it could be something else. I don't know, right?"**

We chose Cathay General Bancorp as the **paradigmatic example** because:

### 1. Banks Are the Hardest Sector for Data Wrangling
- **Multiple regulatory sources**: SEC (10-K/Q, 8-K, DEF 14A), FDIC (Call Reports), Federal Reserve (Y-9C)
- **Complex calculations**: Net interest margin decomposition, deposit beta calibration, credit quality bridges, liquidity/capital ladders
- **Granular disclosures**: Loan mix, CRE concentrations, ACL/ALLL methodologies, interest rate sensitivity
- **If we can deterministically model a bank, we can model anything.**

### 2. CATY Forced Us to Solve the Hardest Problems First
- Multi-source reconciliation (FDIC equity ≠ GAAP equity → 2 known conflicts, documented, validated)
- Time-series normalization (quarterly FDIC vs. annual SEC, different reporting calendars)
- Regulatory form parsing (FFIEC Call Report schemas, iXBRL namespaces, PDF table extraction)
- Provenance under adversity (when sources conflict, which wins? How do we document the override?)

### 3. The Polish and Prowess Are the Standard
CATY's 19 published modules set the bar:
- **Module 05**: NIM decomposition (earning asset yield, funding cost, spread analysis)
- **Module 07**: Credit quality (NCO trends, NPA ratios, reserve coverage)
- **Module 08**: CRE exposure (construction, multifamily, owner-occupied, investor)
- **Module 13**: Residual income valuation (explicit forecast + terminal value, with CoE triangulation)
- **Module 14**: Monte Carlo simulation (5,000 paths, regime-aware)
- **Module 16**: Cost of equity (CAPM, peer regression, DCF bridge—three methods, reconciled)

**Every future report—whether Monster Beverage or Johnson & Johnson—must meet this standard.**

Not "the same content" (Monster has no net charge-offs). But the same:
- **Caliber**: Professional-grade analysis
- **Detail**: Granular decompositions, not summary bullets
- **Audit trail**: Every number traceable to source
- **Rigor**: Validation gates, cross-checks, reconciliation guards

> **"I don't want you to be stupid and think that I want the Monster Beverage report to cover net charge-offs. I think you know what I mean, okay? I think you know that I mean that I want it to be the same caliber, the same level of detail, granularity, audit trail, okay?"**

CATY is not the template. CATY is the **proof of concept** that this level of rigor is achievable, deterministically, at scale.

---

## The Architecture (How It Works)

```
┌─────────────────────────────────────────────────────────────────────┐
│ INPUT: Company Ticker (e.g., CATY, MNST, GOOGL, PFE)               │
└───────────────────────────────┬─────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PROJECT GROUND TRUTH (Universal Base Layer)                        │
├─────────────────────────────────────────────────────────────────────┤
│ Step 1: Resolve Identity                                           │
│   • Ticker → CIK (SEC company_tickers.json)                        │
│   • CIK → Submissions index (forms, SIC, entity type)              │
│   • SIC → Industry classification                                  │
│   • Forms present → Regulatory footprint                           │
│                                                                     │
│ Step 2: Core Layer (Always Run)                                    │
│   • SEC EDGAR iXBRL companyfacts (GAAP financials, tagged)         │
│   • 10-K, 10-Q, 8-K filings (raw + parsed)                         │
│   • DEF 14A proxy (governance, compensation, ownership)            │
│   • Investor Relations (press releases, decks, transcripts)        │
│   • Section 16, 13D/G (insider trades, beneficial ownership)       │
│                                                                     │
│ Step 3: Router (Sector Intelligence)                               │
│   • Score triggers:                                                │
│     - SIC code match (e.g., 6020-6099 = banking)                   │
│     - XBRL tags present (us-gaap:LoansReceivableNet → banking)     │
│     - Forms filed (N-PORT → mutual fund, 20-F → foreign filer)     │
│     - Regulatory IDs (FFIEC cert → bank, NAIC code → insurer)      │
│   • Select pipelines where score ≥ 0.75                            │
│                                                                     │
│ Step 4: Sector Pipelines (Autonomous Plugins)                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│   │ Banking      │  │ Biopharma    │  │ Consumer/CPG │  [+10 more]│
│   │ • FFIEC Call │  │ • FDA drugs@ │  │ • Brand KPIs │            │
│   │ • NIM bridge │  │ • Trials.gov │  │ • Channel mx │            │
│   │ • Credit qlty│  │ • PDUFA cal  │  │ • Price/pack │            │
│   └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                     │
│ Step 5: Provenance Ledger (Append-Only, Content-Addressed)         │
│   {                                                                 │
│     "metric_id": "nim.net_interest_margin",                         │
│     "value": 3.02,                                                  │
│     "unit": "percent",                                              │
│     "as_of": "2025-06-30",                                          │
│     "vintage": "2025Q2",                                            │
│     "source_url": "https://cdr.ffiec.gov/.../call_031_2025Q2",     │
│     "xbrl_tag_or_extractor": "RIAD4074 / nim_bridge.py",           │
│     "retrieved_at": "2025-10-24T04:11:09Z",                         │
│     "sha256": "a3f7b2...",                                          │
│     "calc_ref": "analysis/nim_bridge.py@commit_abc123",            │
│     "confidence": 0.95                                              │
│   }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ OFFSHOOT 1: Equity Research Engine                                 │
├─────────────────────────────────────────────────────────────────────┤
│ • Reads ground truth KPIs (JSON provenance records)                │
│ • Applies valuation models (RIM, DDM, Monte Carlo, peer comps)     │
│ • Generates 19-module dashboard (CATY template)                    │
│ • Output: HTML + JSON + evidence ledger                            │
│ • Validation gates: reconciliation_guard, disconfirmer_monitor     │
│ • Live site: GitHub Pages (public)                                 │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ OFFSHOOT 2: Audit Research Engine (Future)                         │
├─────────────────────────────────────────────────────────────────────┤
│ • Reads SAME ground truth KPIs                                     │
│ • Applies audit frameworks (COSO, PCAOB AS2201, ISA 315)           │
│ • Generates:                                                        │
│   - Risk assessment matrix (inherent + control risk)               │
│   - Control environment evaluation (ICFR, SOX 404)                 │
│   - Materiality calculations (performance, overall, clearly triv.) │
│   - Audit plan (scope, procedures, evidence requirements)          │
│   - Key audit matters (KAMs) identification                        │
│ • Output: Audit workpaper website (styled for professional use)    │
│ • Same provenance ledger (audit trail = equity research trail)     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Non-Monolithic**
   - Each sector pipeline is an autonomous plugin
   - Shared interface: `run(company_profile) → metrics_with_provenance`
   - No cross-dependencies; banking doesn't know about biopharma
   - Router is declarative YAML, not hard-coded logic

2. **Deterministic**
   - Same ticker + same date = same output (bit-for-bit)
   - No manual data entry in ground truth layer
   - Human curation allowed ONLY in Tier 3 facts (narrative summaries), with provenance note

3. **Provenance-First**
   - Every metric is a data structure, not a number
   - `value` is just one field; `source_url`, `confidence`, `calc_ref` are equally important
   - Ledger is append-only, content-addressed (Merkle chain for tamper-evidence)

4. **Sector-Aware, Not Sector-Locked**
   - Holding companies with mixed SICs run multiple pipelines
   - Weighted scoring prevents false positives
   - New sectors added by dropping a plugin + YAML entry (no core changes)

---

## The Two Futures

### Future 1: Equity Research at Scale (Near-Term)

**Current State (Oct 2025):**
- CATY is 75% complete (meeting logistics ✅, audit fees ✅, CEO pay ❌, ownership ❌)
- DEF 14A extraction Phase 1+2 in progress (Codex building now)
- Validation gates operational (reconciliation guard, disconfirmer monitor, publication gate)
- 19 modules published, live on GitHub Pages

**Next 6 Months (Q1-Q2 2026):**
1. ✅ **Finish CATY canonical** (all 30 DEF 14A facts extracting, all modules validated)
2. ✅ **Freeze golden fixtures** (CATY becomes regression test suite)
3. ✅ **Launch Project Ground Truth repo** (router + core + sector stubs)
4. ✅ **Replicate with 5 test companies**:
   - **CATY** (banking) — already done
   - **MNST** (consumer/CPG) — beverages, brand-driven
   - **GOOGL** (tech) — SaaS/ads, complex segment reporting
   - **JPM** (banking) — GSIB, multi-segment, international
   - **JNJ** (biopharma/device) — pharma + device dual-sector routing

**12-Month Vision (Q3-Q4 2026):**
- **50+ companies** with live equity research dashboards
- **CFA IRC submission** (CATY as exemplar, MNST as proof of generalization)
- **Public API** for ground truth KPIs (other researchers can consume provenance-backed data)
- **Community contributions** (others build sector plugins for mining, agriculture, shipping)

### Future 2: Audit Research Engine (Mid-Term)

**The Thesis:**

Every audit starts with the same question: **"What is this company? What are the risks?"**

Auditors spend weeks on:
- Understanding the business (operations, revenue model, cost structure)
- Identifying risks (fraud, error, going concern, significant accounts)
- Designing procedures (walkthroughs, tests of controls, substantive tests)
- Setting materiality (overall, performance, clearly trivial)

**All of this requires the SAME data as equity research:**
- Financials (P&L, balance sheet, cash flow)
- Segment mix (revenue by product/geography)
- Governance (board, committees, insiders)
- Regulatory environment (compliance, licensing, enforcement actions)
- Key metrics (margins, turnover, leverage)

**The Audit Research Engine consumes the ground truth layer and outputs:**

1. **Risk Assessment Matrix**
   - Inherent risk scoring (complexity, judgment, susceptibility to fraud)
   - Control risk evaluation (ICFR design + operating effectiveness)
   - Combined risk → procedure design (low risk = analytics, high risk = detailed testing)

2. **Materiality Workpaper**
   - Overall materiality (0.5-1% of appropriate benchmark: revenue, assets, equity)
   - Performance materiality (50-75% of overall)
   - Clearly trivial threshold (1-5% of overall)
   - Benchmarks pulled from ground truth ledger with provenance

3. **Key Audit Matters (KAMs)**
   - Goodwill impairment (if M&A history in ground truth)
   - Revenue recognition (if complex contracts, multi-element arrangements)
   - Loan loss reserves (if banking sector)
   - Clinical trial accruals (if biopharma sector)
   - **Sector-aware, deterministic identification**

4. **Audit Plan Outline**
   - Scope (entities, locations, accounts)
   - Procedures by assertion (existence, completeness, valuation, rights/obligations, presentation)
   - Evidence requirements (external confirmations, management representations, analytical procedures)
   - Timing (interim vs. year-end, rollforward procedures)

5. **Control Environment Summary**
   - Tone at the top (board independence, audit committee expertise from DEF 14A)
   - Segregation of duties (inferred from org chart, if available)
   - Monitoring (internal audit function, mgmt review controls)
   - **Gospel anchor mapping** (already in CATY README, extends to audit context)

**Why This Matters:**

Audit firms spend **millions** on client onboarding research that gets lost in email chains and Word docs with no provenance. Junior staff re-research the same facts every year.

**An audit research engine with provenance would be:**
- **Defensible** (every risk rating traceable to source data)
- **Reproducible** (peer reviewer can re-perform from ground truth)
- **Efficient** (automate the rote, focus humans on judgment)
- **Scalable** (onboard 100 new clients/year without linear headcount growth)

**Timeline:**
- **2026**: Equity research at scale (prove the ground truth thesis)
- **2027**: Audit research MVP (CATY as first test case)
- **2028**: Audit engine at scale (Big 4 pilot? Boutique firm deployment?)

---

## Current State & Next Milestones

### What Works Right Now (Oct 2025)

✅ **CATY Equity Research Dashboard** (live, public)
- 19 analytical modules published
- Reconciliation guard operational (2 known conflicts, documented)
- Disconfirmer monitor (driver invalidation checks)
- Publication gate (release control)
- GitHub Pages deployment (auto-refresh on data updates)

✅ **Ground Truth Foundation** (partial)
- SEC EDGAR iXBRL fetcher (companyfacts API integration)
- FDIC Call Report pipeline (10 quarters, NCO timeseries)
- DEF 14A extractor (meeting logistics ✅, audit fees ⚠️, CEO pay ❌, ownership ❌)
- Provenance ledger (source_url, sha256, retrieved_at, calc_ref)
- Validation gates (schema checks, cross-checks, confidence floors)

✅ **Governance & Documentation**
- Canonical provenance table (Gospel anchors + modern standards)
- Postmortems (2025-10-25 DEF14A pipeline regression, lessons learned)
- Evidence folder (primary sources, raw artifacts, workpapers)
- Git safety protocols (force-push prohibition, directory awareness, human-in-loop)

### What's In Progress (This Week)

🔨 **DEF 14A Pipeline (Phase 1+2)** — Codex building, Claude validating
- Fix CEO compensation extraction (Summary Compensation Table parsing)
- Fix audit fee breakdown (table column normalization)
- Add beneficial ownership extractor (>5% holders)
- Add equity plan metrics (shares available, overhang)
- Add board independence counts (total directors, independent directors)
- Expand validator (audit fee rollup, ownership %, board independence ratio)
- Add validation gates to automation (`update_all_data.py`)
- Add CI check (GitHub Actions workflow for proxy data schema)

### What's Next (Q4 2025 - Q1 2026)

📋 **CATY Canonical Completion**
- [ ] Finish all 30 DEF 14A facts (registry complete, extraction verified)
- [ ] Freeze golden fixtures (regression test suite)
- [ ] Add provenance metadata completeness (page_numbers, dom_path, table_id for ALL facts)
- [ ] Document "CATY Playbook" (what every company report must have)
- [ ] CFA IRC submission (CATY as exemplar)

📋 **Project Ground Truth Launch**
- [ ] Bootstrap new repo (`project-ground-truth`) with router + sector stubs
- [ ] Migrate CATY's banking tools into `sectors/banking/` plugin
- [ ] Build core layer (SEC fetcher, IR scraper, DEF 14A universal extractor)
- [ ] Test router with 5 diverse companies (CATY, MNST, GOOGL, JPM, JNJ)
- [ ] Prove replication works before scaling

📋 **Infrastructure Hardening**
- [ ] Integration test suite (3+ real proxies, E2E extraction, golden output comparison)
- [ ] 429 backoff handler (SEC rate limit compliance)
- [ ] NDJSON output mode (streaming facts, not single JSON blob)
- [ ] Provenance chain integrity (Merkle chain, tamper-evidence)

---

## Guiding Principles (Ever-Green)

These principles govern **all** work on the ground truth layer, equity research offshoots, and future audit research:

### 1. Canonical Provenance (Non-Negotiable)

Every metric must answer:
- **Where?** (`source_url`, `page_numbers`, `dom_path`)
- **When?** (`retrieved_at`, `vintage`)
- **How?** (`xbrl_tag_or_extractor`, `calc_ref`, `method`)
- **How certain?** (`confidence`, `validation.warnings`)
- **How verified?** (`sha256`, `cross_checks`)

If you can't answer all five, the metric doesn't ship.

### 2. Determinism Over Convenience

- Same inputs → same outputs (bit-for-bit)
- No manual overrides without provenance note
- No "trust me" calculations (show your work)
- No silent failures (fail loudly, log everything)

### 3. Integrity Over Speed

- Validation gates block bad data from reaching production
- CI must pass before merge (no exceptions)
- Reconciliation conflicts documented, not hidden
- Postmortems written for every incident (no sweeping under rug)

### 4. Build in Public, Fail Forward

- All code public (GitHub)
- All dashboards public (GitHub Pages)
- All postmortems public (docs/postmortems/)
- All mistakes documented (we learn, we improve, we don't repeat)

### 5. Human-in-Loop for Judgment, Automation for Rote

- Tier 1 facts (deterministic): 100% automated (meeting date, audit fees)
- Tier 2 facts (table parsing): machine-assisted, human QC (ownership, compensation)
- Tier 3 facts (narrative): human-only with provenance (related-party transactions, risk factors)
- **Never pretend AI extracted something a human typed**

### 6. Sector-Aware, Not Sector-Locked

- Router is declarative (YAML rules), not imperative (if/else chains)
- New sectors don't require core changes (drop plugin + config entry)
- Multi-sector companies run multiple pipelines (holding company = banking + insurance)
- No monolith. Ever.

### 7. Gospel Anchors Ground the Work

From the canonical table in README.md:

- **"Faithful in very little… faithful in much"** (Luke 16:10) → Small data integrity failures become large trust failures
- **"Two or three witnesses"** (Matt 18:16) → Corroboration > assertion; triangulate sources
- **"Orderly account"** (Luke 1:3-4) → Workpapers tell a complete story; provenance ledger is the account
- **"Be on guard; be alert"** (Mark 13:33) → Validation gates embody watchfulness
- **"Wise as serpents, innocent as doves"** (Matt 10:16) → Rigorous skepticism + ethical transparency

These aren't metaphors. They're **control objectives** mapped to modern audit standards (COSO, PCAOB, ISA).

---

## Closing (The Hardest Part Is Now)

> **"Once this is tied down. Imagine company ... boom CFA level Equity Report... Boom full audit profile for target client boom."**

We are building the scaffolding. **This is the hardest part.**

CATY is not the end goal. CATY is the **proof** that the goal is achievable.

- If we can deterministically model a bank (the hardest sector), we can model anything.
- If we can trace every NIM basis point to a FFIEC Call Report line item, we can trace every metric to its source.
- If we can build 19 modules with validation gates and provenance for one company, we can replicate it for 1,000 companies.

**But the foundation must be perfect.** Not 90%. Not "good enough for now." **Perfect.**

Because when we fork this architecture and scale it:
- Every flaw in CATY will replicate 1,000x
- Every shortcut will compound
- Every missing provenance field will haunt us in the audit research engine

**So we get CATY right. Completely right.**

Then we build Project Ground Truth. Then we replicate. Then we scale.

**Equity research at scale. Audit research at scale. One canonical base. Two professional futures.**

---

## For CFA Judges, GitHub Visitors, and Future Collaborators

This document is the North Star. If you're reading this:

- **CFA IRC Judges**: CATY is the exemplar, but the vision is universal equity research at scale. We're proving the thesis with one bank, then replicating across sectors.

- **GitHub Community**: The ground truth layer will be open-source. Sector plugins will be modular. If you want to build a plugin for mining (reserves disclosures, NI 43-101) or agriculture (USDA reports, commodity pricing) or shipping (IMO compliance, fleet age), the architecture will support it.

- **Audit Firms**: The audit research engine is coming. Same provenance, different output. If you want to collaborate, the foundation is being built now.

- **Employers / Recruiters**: This is not an academic exercise. This is infrastructure for the future of financial analysis. The rigor here exceeds most Big 4 audit workpapers. The ambition exceeds most sell-side research. We're building something that doesn't exist yet.

**Building in public. Failing forward. One company at a time. Starting with CATY.**

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-24
**Status**: Living document (will evolve as architecture matures)
**Governance**: Changes require approval; material updates bump version number

**Canonical Repository**: https://github.com/nirvanchitnis-cmyk/caty-equity-research-live
**Live Dashboard**: https://nirvanchitnis-cmyk.github.io/caty-equity-research-live/
**Contact**: Nirvan Chitnis (via GitHub issues or repository discussions)

---

*"Faithful in very little… faithful in much." — Luke 16:10*
