# DEF14A Pipeline Regression — Postmortem (2025-10-25)

## Executive Summary
- **What happened:** We shipped a major DEF 14A extraction overhaul (commit `8b50ee2`) that promised materiality-gated refreshes and provenance logging. In production the new CLI ran, but returned an empty fact payload (`{}`), leaving automation consumers without record dates, meeting logistics, or auditor context.
- **Detection:** The failure was caught only after deployment when the user asked for a critical self-review. No automated guardrails flagged the missing facts.
- **Impact:**  
  - Automated dashboards lost key proxy metadata, eroding confidence in the “one-click refresh” narrative.  
  - Downstream agents were blocked (no facts to reconcile, no materiality threshold to evaluate).  
  - We published public claims (README + postmortem) that were inaccurate at the time of release.
- **Duration:** From initial push on 2025-10-24 21:20 UTC until remediation work in this session (≈24 hours of bad state for anyone pulling main).
- **Severity:** High — functionality regression with incorrect public messaging and zero automated detection.

## Timeline (UTC)
| Time | Event |
| --- | --- |
| 2025-10-24 21:20 | Automation run commits new toolkit; CLI outputs `{}`. No alarms. Push to `main`. |
| 2025-10-24 21:30 | User requests readiness check; I confirm push is live without verifying data fidelity. |
| 2025-10-25 04:24 | Post-commit validation gates re-run (reconciliation, disconfirmer) — all PASS (they don’t inspect proxy data). |
| 2025-10-25 04:30 | User requests critical self-review; notes live pipeline still empty. Incident opened. |
| 2025-10-25 04:35–05:30 | Root-cause: heading detection returning no spans; meeting extraction regex too brittle; table matcher pulling irrelevant tables. |
| 2025-10-25 05:40 | Implemented fixes (HTML heading parsing, improved normalization, tests). CLI now returns deterministic meeting facts + record date. |
| 2025-10-25 05:50 | Automation rerun with fixed toolkit; facts populated locally; outstanding gaps (CEO pay ratio, audit fee table normalization) documented. |

## Root Cause Analysis
1. **Section locator blind to inline XBRL markup:** Original implementation scanned raw text lines; the CATY proxy is Inline XBRL where headings are nested inside `<div><strong>` etc. Result: locator produced zero spans, so downstream extractors skipped work.
2. **Regex assumptions too narrow:** Meeting extractor required the string `"Meeting will be held on"` with month format `May 12, 2025` and no weekday. The actual prose contained `"The annual meeting will be held on Monday, May 12, 2025..."`. Similar rigidity blocked record date extraction.
3. **Table extractor shotgun approach:** Without DOM anchoring we attempted to parse every table in the filing for each section. Even once spans existed we risked selecting irrelevant tables (first table in doc rather than summary compensation table).
4. **Test coverage gap:** No unit/integration tests exercised HTML proxies. Only API smoke tests existed, so the regression sailed through despite returning `{}`.
5. **Process miss:** I declared “push live” success without verifying `data/def14a_facts_latest.json`. No automated or manual check looked at payload cardinality before deployment.

## Remediation & Fixes Implemented
- **DOM-aware SectionLocator** (`section_locator.py`): Parses HTML with lxml, captures XPath `dom_path` for each heading (h1-h6, bold paragraphs, role=heading) and feeds that into section spans.
- **Targeted table extraction** (`table_extraction.py`): Uses `dom_path` to fetch only the first few tables following a section heading (rather than every table in the document).
- **HTML-normalized text extraction** in meeting/audit/compensation modules: we run `html_normalizer.normalize_html` to expand Inline XBRL text without raw tag fragments.
- **Robust meeting parser** (`meeting.py`): Flexible patterns for weekday-inclusive dates, record-date phrasing (`"record date on/as of"`), meeting format inference, dedicated helper tests.
- **Ownership table sanitization** (`ownership.py`): Coerces non-string headers prior to normalization.
- **Regression tests** (`tests/test_section_locator.py`): Validates DOM-path-aware section detection and ensures meeting extractor returns parsed dates/URLs on a mini proxy fixture.
- **Automation rerun** (`scripts/update_all_data.py`): Verified pipeline now writes meeting metadata & record date to `data/def14a_facts_latest.json`.

## Remaining Gaps / Follow-up Actions
1. **CEO pay ratio & SCT extraction still missing.** Inline XBRL splits text/values; we need dedicated parsing (likely via XPath + numeric tags) and structural table matching. _Owner: Codex agent — TODO._
2. **Audit fee breakdown validation.** Current table heuristic picks first post-heading table; needs column scoring + validator per spec (audit vs audit-related). _Owner: Codex agent — TODO._
3. **Confidence calibration.** Meeting facts currently return ~0.59 confidence (product of heuristic weights). Revisit weighting once validators confirm provenance. _Owner: Research automation._
4. **Materiality gate re-validation.** Refresh script still requests `ceo_pay_ratio` and `audit_fees`; until those facts exist, materiality logic cannot fire. Add fallback messaging when facts missing. _Owner: Automation._
5. **Monitoring / gating.** Add CI assertion that `data/def14a_facts_latest.json` contains ≥ required schema before allowing pushes. Consider `analysis/publication_gate` extension for proxy data. _Owner: Engineering enablement._

## Preventive Measures
- Expand unit coverage for each fact extractor (meeting, ownership, audit, compensation) using real-world fixture snippets (HTML + inline XBRL).
- Introduce integration smoke test that runs the CLI against at least one cached DEF 14A and asserts non-empty fact map with key items present.
- Add a publication guard to fail builds if `data/def14a_facts_latest.json` lacks mandatory facts (meeting date, record date, access URL, etc.).
- Incorporate a “sanity diff” in `scripts/update_all_data.py` that logs before/after fact counts and warns if facts vanish.
- Update runbooks to require manual review of `data/def14a_facts_latest.json` (or generated report) prior to declaring success.

## Lessons Learned
- Shipping infra without fixture-backed tests invites regressions, especially when parsing SEC Inline XBRL HTML.
- “Success” messaging is meaningless without payload inspection; automation must validate outputs, not just return codes.
- DOM heuristics + provenance are vital when dealing with SEC formatting variance—treat raw text scanning as a last resort.
- Public documentation (README, prior postmortems) must be verified against current behavior before publishing claims.

## Current Status
- Meeting logistics (date/time/timezone/virtual URL/record date) now populate correctly.
- Proxy pipeline still lacks compensation/audit outputs; materiality gate cannot yet evaluate significance. Work tracked as TODO above.
- This postmortem is published to keep all agents aware of the regression, fixes, and remaining obligations.
