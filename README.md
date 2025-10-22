## CATY Equity Research Automation – Q3 2025 Operating Playbook

**Status (22 Oct 2025):** Site is live, publication gate currently **CLEAR**, valuation cards remain hidden under “NOT RATED” until refreshed Q3 inputs (deposit betas, COE, peer regression) are published alongside the sensitivity suite. Peer regression now runs on the eight-bank universe, and deposit betas are captured directly from inline XBRL via the new extractor. Remaining board asks (sensitivities, NIM bridge integration, evidence pack) are locked to the SLAs below.

Live dashboard: https://nirvanchitnis-cmyk.github.io/caty-equity-research-live/  
Repository: https://github.com/nirvanchitnis-cmyk/caty-equity-research-live  
Local root: `/Users/nirvanchitnis/caty-equity-research-live`

---

### 1. Board-Facing Snapshot

| Item | Current Position | Next Action & SLA |
|------|------------------|-------------------|
| **Rating** | **NOT RATED** (valuation cards show “Hidden until inputs final”) | Reinstate within **24 h** of the Q3 10‑Q once sensitivities, COE, and deposit betas are refreshed |
| **Peer Regression** | 8-bank fit: P/TBV = 0.4812 + 0.0693×ROTE, R² = 0.599, Cook’s D < 0.30 for all retained peers | Narrative + diagnostics embedded in Module 11; update coefficients immediately post filing |
| **Deposit Betas** | `data/deposit_beta_history.json` holds the latest three quarters from the new extractor | Wire history into the Q2→Q3→Normalized NIM bridge within **48 h** of the 10‑Q |
| **Sensitivities** | Table scaffolded (Δ columns marked TBA) | Calculate ΔNIM / ΔEPS / ΔFair Value within **24 h** of the filing using refreshed regression & COE |
| **Evidence Pack** | Core CATY files staged; expanded peer documents pending | Stage OPBK/BANC/COLB documents under `evidence/raw/` and link in UI before the gate flips |

Progress against these deliverables is tracked in `BOARD_RESUBMIT_PLAN.md`.

---

### 2. Since the Oct 22 Commit (`af3937f`)

* Peer regression rebuilt on the expanded universe (EWBC, CVBF, HAFC, COLB, WAFD, PPBI, BANC, OPBK) with refreshed prices and fundamentals (`data/caty11_peers_normalized.json`).
* Module 11 visuals and commentary now expose the updated slope/intercept, Cook’s D metrics, and residuals (`CATY_11_peers_normalized.html`, `scripts/charts.js`).
* Added `scripts/extract_deposit_betas_q10.py` to parse average-balance tables from inline XBRL; output lands in `data/deposit_beta_history.json` and feeds Module 05.
* Publication gate upgraded to require ≥3 quarters of product-level deposit history before ratings can publish (`analysis/publication_gate.py`).
* NIM module now references the deposit-rate history metadata (latest interest-bearing rate, all-in rate, and DDA mix) pending bridge integration (`data/caty05_calculated_tables.json`).

---

### 3. Automation Flow

```
SEC Submissions API ─┐
FDIC BankFind / Call Reports ─┬─> scripts/fetch_*.py ─┐
Market data (stooq) ───────────┘                     │
                                                     ├─> data/*.json (with provenance tags)
Deposit beta extractor ─ scripts/extract_deposit_betas_q10.py ─┘

data/*.json ──> scripts/build_site.py ──> HTML modules + index.html
                                      └─> CI guardrails (reconciliation, disconfirmer, publication gate)
```

**One-command refresh**
```bash
python3 scripts/update_all_data.py
```

**Validation stack (must all return exit code 0 before pushing)**
```bash
python3 scripts/build_site.py
python3 analysis/reconciliation_guard.py
python3 analysis/disconfirmer_monitor.py
python3 analysis/publication_gate.py
```

GitHub Actions reruns the same checks on every commit. No pushes to `main` if any guard fails.

---

### 4. Module Coverage (17 / 17 automated)

| Module | Focus | Hard-coded values | Sources |
|--------|-------|-------------------|---------|
| CATY_01 | Company Profile | 0 | SEC XBRL |
| CATY_02 | Income Statement | 0 | SEC XBRL |
| CATY_03 | Balance Sheet | 0 | SEC XBRL |
| CATY_04 | Cash Flow | 0 | SEC XBRL |
| CATY_05 | NIM & Deposit Betas | 0 (history auto-loaded) | SEC XBRL + FDIC |
| CATY_06 | Deposits & Funding | 0 | FDIC |
| CATY_07 | Credit Quality | 0 | FDIC + SEC |
| CATY_08 | CRE Exposure | 0 | SEC |
| CATY_09 | Capital & Liquidity | 0 | SEC |
| CATY_10 | Capital Actions | 0 | SEC |
| CATY_11 | Peer Analysis | 0 | SEC + market data |
| CATY_12 | Valuation Model | 0 | Calculated |
| CATY_13 | Residual Income | 0 | Calculated |
| CATY_14 | Monte Carlo | 0 | Calculated |
| CATY_15 | ESG Materiality | 0 | SEC + curated evidence |
| CATY_16 | COE Triangulation | 0 | Market data |
| CATY_17 | ESG KPI Dashboard | 0 | Governance/Evidence pack |

---

### 5. Pending Deliverables & Deadlines

| Deliverable | Owner | Deadline | Notes |
|-------------|-------|----------|-------|
| Sensitivity table (ΔNIM / ΔEPS / Δ Fair Value) | Valuation | **T+24 h** post 10‑Q | Use refreshed regression slope, updated COE, and credit-cost scenarios |
| NIM bridge integration | Asset/Liability | **T+48 h** post 10‑Q | Drive the Q2→Q3→Normalized bridge off `deposit_beta_history.json` with charted yield/cost/mix effects |
| Evidence pack expansion | Data | Before gate clears | Stage primary docs for OPBK, BANC, COLB, WAFD, PPBI under `evidence/raw/` and reference them in modules |
| Peer regression narrative | Valuation | Complete | Module 11 now details slope interpretation, Cook’s D, and peer inclusion rationale |
| Gate clearance & rating reinstatement | Lead analyst | **T+24 h** once inputs final | No placeholders once deposit betas, peer regression, and COE are refreshed |

---

### 6. Key Scripts

* `scripts/extract_deposit_betas_q10.py` – Pull product-level averages from inline XBRL (secures ≥3-quarter history). Example:
  ```bash
  python3 scripts/extract_deposit_betas_q10.py --quarters 2025Q2 2025Q1 2024Q3
  ```
* `scripts/fetch_peer_banks.py` – CompanyFacts ingestion for CATY + peers (OPBK added, HOPE retained for medians only).
* `scripts/generate_peer_snapshot.py` – Builds the audit CSV consumed by Module 11 and evidence tables.
* `scripts/build_site.py` – Regenerates HTML autogen sections; run after any data change.

All scripts honor SEC rate limits (custom User-Agent + 0.4 s throttle). No secrets or credentials required.

---

### 7. Evidence & Provenance Expectations

* Primary filings live under `evidence/raw/` (to be expanded with OPBK/BANC CRE disclosures before the gate flips).
* Workpapers and reconciliations live in `evidence/workpapers/`.
* Every figure in the dashboard points to a JSON key with accession, XBRL tag, and timestamp metadata.
* DEF14A governance pipeline (7/8 peers) verified with SHA256 manifests (`analysis/derek_def14a_verifier.py`).

Upcoming evidence targets:
- OPBK 10‑Q CRE segmentation & criticized loans schedule
- BANC allowance roll-forward and criticized loan breakout
- Updated transcripts for the expanded peer cohort once earnings calls post

---

### 8. Push / Deployment Checklist

1. `python3 scripts/update_all_data.py`
2. Inspect diffs (`git diff`, `git status`)
3. `python3 analysis/publication_gate.py`
4. `python3 analysis/reconciliation_guard.py`
5. `python3 analysis/disconfirmer_monitor.py`
6. `git add …` / `git commit` (pre-commit reruns guards)
7. `git push origin main`

GitHub Pages deploys within ~60 seconds of the push.

---

### 9. Ops Notes

* SEC User-Agent: `CATY Research Team (research@analysis.com)`
* Market data fall-back: stooq.com daily CSV (latest close 21 Oct 2025)
* Coordination docs: `BOARD_RESUBMIT_PLAN.md`, `AUTOMATION_COMPLETION_PLAN.md`, `CFA_Q3_2025_READINESS_CHECKLIST.md`
* SLA reiteration: Sensitivities T+24 h, NIM bridge integration T+48 h, evidence pack populated before gate clears, rating reinstated within 24 h once inputs finalize. Zero tolerance for slippage.

The repo is ready to execute the post‑filing sprint: scripts are updated, guardrails enforced, and commitments locked. Stay disciplined once the 10‑Q hits.
