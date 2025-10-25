# CATY — Equity Research Live

<!-- CANONICAL-REMINDER:BEGIN -->
## Canonical Reminder for All Agents (CATY) (Ever-Green Anchor)

**Non-negotiable:** We operate under canonical provenance. Integrity, clarity, and accountability govern this project.

| Modern standard / principle | Gospel anchor | Bridge (ethic → control) |
|---|---|---|
| **Control environment: integrity & ethical values** ([COSO]) | "Faithful in very little… faithful in much" (Luke 16:10); "Let your 'Yes' be yes" (Matt 5:37) | Tone-at-the-top = truthfulness + consistency. Ethical culture underpins reliable reporting. |
| **Risk assessment & planning** ([COSO], [ISA200]) | "Who builds a tower without first **counting the cost**?" (Luke 14:28) | Identify, analyze, and plan for risks before committing—budgeting, scenarios, materiality. |
| **Segregation of duties / two-person controls** ([COSO]) | Sent them out **two by two** (Mark 6:7); "two or three witnesses" (Matt 18:16) | Dual custody, maker–checker, approvals reduce error/fraud; corroboration matters. |
| **Audit evidence—sufficient & appropriate** ([AS1105]) | "The testimony of **two witnesses** is true." (John 8:17) | Corroboration > assertion. Reliability hierarchy & triangulation reflect the "two-witness" principle. |
| **Documentation / workpapers** ([AS1215]) | "I decided to write an **orderly account**…" (Luke 1:3–4) | Workpapers tell a complete, organized story so an independent reviewer can re-perform the logic. |
| **Monitoring & vigilance** ([COSO]) | "**Be on guard; be alert**." (Mark 13:33) | Ongoing/periodic evaluations and KPI reviews embody watchfulness. |
| **Independence / objectivity & due care** ([AS1000]) | "You **cannot serve two masters**." (Matt 6:24) | Freedom from conflicts + professional skepticism and judgment. |
| **ICFR & integrated audits** ([AS2201], [SOX404]) | "Render to Caesar…" (Mark 12:17) | Management designs/assesses controls; auditors opine on effectiveness. |
| **Information & communication** ([COSO], [AS1301]) | "Let your 'Yes' be yes…" (Matt 5:37) | Clear, timely, accurate communication—especially with audit committees—supports control effectiveness. |
| **Prudence + skepticism under pressure** | "Be **wise as serpents**, innocent as doves." (Matt 10:16) | Shrewd risk awareness with integrity—skeptical, not cynical. |

**Usage:** This table **must** remain in the public `README.md` of agent-facing repos. Do not paraphrase.
**Governance:** Changes require approval and version bump in this section.

<!-- Refs: authoritative links -->
[COSO]: https://www.coso.org/guidance-on-ic
[ISA200]: https://www.ibr-ire.be/docs/default-source/fr/documents/reglementation-et-publications/normes-et-recommandations/isa/isa-english-version/isa-200_en.pdf
[AS1105]: https://pcaobus.org/oversight/standards/auditing-standards/details/AS1105
[AS1215]: https://pcaobus.org/oversight/standards/auditing-standards/details/AS1215
[AS1000]: https://pcaobus.org/oversight/standards/auditing-standards/details/as-1000--general-responsibilities-of-the-auditor-in-conducting-an-audit
[AS2201]: https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201
[AS1301]: https://pcaobus.org/oversight/standards/auditing-standards/details/AS1301
[SOX404]: https://www.sec.gov/info/smallbus/404guide.pdf
<!-- CANONICAL-REMINDER:END -->

---

## Project Overview

**What:** CFA Institute Research Challenge (IRC) equity research dashboard for Cathay General Bancorp (NASDAQ: CATY)

**Goal:** Audit-grade, fully automated equity research with provenance metadata tracing every number to SEC/FDIC APIs

**Ethos:** Building in public, failing forward, continuous improvement

**Live Dashboard:** https://nirvanchitnis-cmyk.github.io/caty-equity-research-live/

**Repository:** https://github.com/nirvanchitnis-cmyk/caty-equity-research-live

---

## Quick Start

### Run Validation Gates (Pre-Commit Checks)
```bash
python3 analysis/reconciliation_guard.py
python3 analysis/disconfirmer_monitor.py
python3 analysis/publication_gate.py
```

All three must return exit code 0 before pushing to main.

### Rebuild Site After Data Changes
```bash
python3 scripts/build_site.py
```

### Fetch Latest Data
```bash
python3 scripts/update_all_data.py
```
- Runs market data refresh, proxy fact extraction (via `tools.def14a_extract`), SEC/FDIC pulls, site rebuild, and validation gates end-to-end.

### Pull Proxy Statement Facts On-Demand
```bash
python3 -m tools.def14a_extract.cli facts --ticker CATY --year 2025 \
  --facts meeting_date,ceo_pay_ratio,audit_fees --provenance --output data/def14a_facts_latest.json
```
- Produces deterministic DEF 14A fact packs with provenance JSON written to `data/def14a_facts_latest.json`.
- Use `--refresh` to bypass cache or omit `--facts` to return the full registry (≥25 canonical facts).

---

## Repository Structure

```
caty-equity-research-live/
├── index.html                    # Landing page, navigation hub
├── CATY_01_company_profile.html  # 19 published dashboard pages
├── CATY_02_income_statement.html
├── ... (CATY_03 through CATY_18)
├── README.md                     # This file
│
├── analysis/                     # Analysis scripts and methodologies
│   ├── reconciliation_guard.py   # Valuation validation (pre-commit hook)
│   ├── disconfirmer_monitor.py   # Driver invalidation checks
│   ├── publication_gate.py       # Release control automation
│   ├── valuation_bridge_final.py # DDM bridge calculation
│   ├── ... (14 more Python scripts)
│   └── methodologies/            # Methodology documentation
│       ├── RESIDUAL_INCOME_VALUATION.md
│       ├── MONTE_CARLO_VALUATION.md
│       ├── ESG_MATERIALITY_MATRIX.md
│       └── ... (14 more .md files)
│
├── data/                         # All structured data (JSON)
│   ├── caty01_company_profile.json
│   ├── caty02_income_statement.json
│   ├── ... (all module data files)
│   ├── peer_comparables.json
│   └── proxy/                    # Proxy statement extractions
│
├── docs/                         # 📁 NEW: Organized documentation
│   ├── README.md                 # Documentation index
│   ├── governance/               # Canonical frameworks
│   ├── planning/                 # Project plans & checklists
│   ├── process/                  # Workflow guides (handoffs, git safety)
│   ├── accountability/           # Performance tracking
│   ├── postmortems/              # Failure analysis
│   ├── journal/                  # Daily summaries & reflections
│   ├── inventory/                # Content catalogs
│   └── archive/                  # Historical artifacts
│
├── evidence/                     # Audit trail & source documents
│   ├── primary_sources/          # SEC filings (10-Q, 10-K, 8-K)
│   ├── raw/                      # Raw XBRL, call reports
│   ├── workpapers/               # Audit workpapers
│   └── ... (68 evidence files)
│
├── scripts/                      # Automation & site building
│   ├── build_site.py             # Main site generator
│   ├── fetch_fdic_data.py        # FDIC data fetching
│   ├── build_peer_comparables.py # Peer analysis automation
│   ├── charts.js                 # Chart rendering
│   └── adhoc/                    # One-off utility scripts
│
├── tools/                        # Automation toolkits
│   └── def14a_extract/           # DEF 14A fact extraction suite (CLI + API + tests)
│
├── styles/                       # Canonical design system
│   └── caty-equity-research.css  # Master stylesheet
│
└── ... (assets/, logs/, schemas/, tools/)
```

---

## Dashboard Modules (19 Total)

| Module | Focus | Data Sources |
|--------|-------|--------------|
| **CATY_01** | Company Profile | SEC XBRL |
| **CATY_02** | Income Statement | SEC XBRL |
| **CATY_03** | Balance Sheet | SEC XBRL |
| **CATY_04** | Cash Flow | SEC XBRL |
| **CATY_05** | NIM Decomposition | SEC XBRL + FDIC |
| **CATY_06** | Deposits & Funding | FDIC Call Reports |
| **CATY_07** | Loans & Credit Quality | FDIC + SEC |
| **CATY_08** | CRE Exposure | SEC disclosures |
| **CATY_09** | Capital & Liquidity | SEC XBRL |
| **CATY_10** | Capital Actions | SEC XBRL + DEF14A |
| **CATY_11** | Peer Analysis | SEC + Yahoo Finance |
| **CATY_12** | DDM Valuation Model | Calculated (reconciliation-guarded) |
| **CATY_13** | Residual Income Valuation | Calculated |
| **CATY_14** | Monte Carlo Valuation | 10,000-path simulation |
| **CATY_15** | ESG Materiality Matrix | SASB/TCFD framework |
| **CATY_16** | Cost of Equity Triangulation | CAPM + Fama-French + market-implied |
| **CATY_17** | ESG KPI Dashboard | Governance data + evidence |
| **CATY_18** | Sensitivity Analysis | Driver elasticities |
| **CATY_SOCIAL_SENTIMENT** | Social Sentiment Analysis | Community banking moat |

---

## Validation Architecture

### Three-Gate System (All Must Pass)

#### 1. Reconciliation Guard (`analysis/reconciliation_guard.py`)
- **Purpose:** Verify published valuation numbers match calculated outputs
- **Tolerance:** ±$0.50
- **Checks:** Wilson target, regression target, normalized target, IRC blended
- **Exit Code:** 0 = PASS, 1 = FAIL (blocks commit)

#### 2. Disconfirmer Monitor (`analysis/disconfirmer_monitor.py`)
- **Purpose:** Detect when key drivers fall outside tolerance (invalidating assumptions)
- **Checks:**
  - Through-cycle NCO normalization (threshold: 45.80 bps)
  - Deposit beta trajectory (threshold: 0.45)
  - Peer regression outliers (Cook's Distance > 1.0)
  - Wilson/market probability divergence (threshold: 40 ppts)
  - ESG discount integration
- **Exit Code:** 0 = PASS (all drivers within tolerance)

#### 3. Publication Gate (`analysis/publication_gate.py`)
- **Purpose:** Block publishing ratings until minimum data requirements met
- **Requirements:** ≥3 quarters of product-level deposit history
- **Exit Code:** 0 = CLEAR (safe to publish), 1 = BLOCKED

### Pre-Commit Hook Integration
All three gates run automatically via Git pre-commit hook. No commits allowed unless all pass.

---

## Data Provenance

Every number in the dashboard includes:
1. **Source URL:** SEC EDGAR accession number or FDIC API endpoint
2. **Extraction Method:** Regex parsing, table extraction, or XBRL tag
3. **Calculation Logic:** Git commit hash referencing the script
4. **Vintage Timestamp:** When data was fetched

Example provenance metadata:
```json
{
  "value": 1.303,
  "source": "https://www.sec.gov/cgi-bin/viewer?action=view&cik=0000700564&accession_number=0000700564-25-000045",
  "xbrl_tag": "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
  "extracted_at": "2025-10-23T00:00:00Z",
  "calculation": "data/caty03_balance_sheet.json",
  "vintage": "2025Q2"
}
```

---

## Automation Flow

```
SEC Submissions API ────┐
FDIC BankFind / Call Reports ─┬─> scripts/fetch_*.py ──┐
Yahoo Finance ─────────────────┘                         │
                                                          ├─> data/*.json (with provenance)
Deposit beta extractor ─ scripts/extract_deposit_betas_q10.py ─┘
                                                          │
data/*.json ──> scripts/build_site.py ──> HTML modules + index.html
                                      └─> Validation gates (reconciliation, disconfirmer, publication)
```

---

## Key Scripts

### Site Building
- `scripts/build_site.py` - Regenerates HTML autogen sections from data/*.json

### Data Fetching
- `scripts/update_all_data.py` - One-command refresh for all data sources
- `scripts/refresh_market_data.py` - Spot price refresh via yfinance with before/after logging, materiality gate, and site rebuild
- `scripts/fetch_fdic_data.py` - FDIC Call Report data
- `scripts/fetch_peer_filings.py` - SEC EDGAR peer company data
- `scripts/extract_deposit_betas_q10.py` - Product-level deposit averages from XBRL

### Validation & Controls
- `analysis/reconciliation_guard.py` - Valuation reconciliation (±$0.50 tolerance)
- `analysis/disconfirmer_monitor.py` - Driver invalidation detection
- `analysis/publication_gate.py` - Minimum data requirements check

### Analysis
- `analysis/valuation_bridge_final.py` - DDM bridge calculation
- `analysis/probability_weighted_valuation.py` - Wilson confidence interval automation
- `analysis/CAPM_beta.py` - Cost of equity estimation
- `analysis/nco_probability_analysis.py` - Credit risk scenarios

---

## Evidence & Documentation

### Evidence Trail
- **Primary filings:** `evidence/primary_sources/` (10-Q, 10-K, 8-K, DEF14A)
- **Raw extractions:** `evidence/raw/` (XBRL, call reports)
- **Workpapers:** `evidence/workpapers/` (NCO bridge, buyback analysis, CET1 headroom)
- **Methodologies:** `evidence/` (68+ markdown/HTML evidence pages)

### Documentation
- **Process guides:** `docs/process/` (git safety, handoffs, checklists)
- **Planning:** `docs/planning/` (project plans, readiness checklists)
- **Accountability:** `docs/accountability/` (performance tracking, delivery docs)
- **Postmortems:** `docs/postmortems/` (failure analysis, lessons learned)
- **Governance:** `docs/governance/` (canonical frameworks)

See `docs/README.md` for full documentation index.

---

## Push / Deployment Checklist

1. Verify you're in canonical location:
   ```bash
   pwd  # Should be /Users/nirvanchitnis/caty-equity-research-live
   ```

2. Run validation gates:
   ```bash
   python3 analysis/reconciliation_guard.py
   python3 analysis/disconfirmer_monitor.py
   python3 analysis/publication_gate.py
   ```

3. Inspect changes:
   ```bash
   git status
   git diff
   ```

4. Commit (pre-commit hook reruns all gates):
   ```bash
   git add <files>
   git commit -m "Description"
   ```

5. Push to live site:
   ```bash
   git push origin-live main
   ```

6. Verify deployment (GitHub Pages deploys within ~60 seconds):
   ```bash
   curl -I https://nirvanchitnis-cmyk.github.io/caty-equity-research-live/index.html
   ```

---

## Design System

### Canonical Color Palette
- **Cathay Red:** `#C41E3A`
- **Cathay Gold:** `#D4AF37`
- **Cathay Black:** `#14202D`
- **Success (up/positive):** `#2E6F3E`
- **Danger (down/negative):** `#8C1E33`
- **Info (neutral):** `#2F6690`

See `styles/caty-equity-research.css` for complete design tokens.

**IMPORTANT:** Always use canonical CSS tokens. Never ship Tailwind defaults or improvised colors.

---

## Independence & Compliance

### Auditor Independence Verification
Before building the CATY peer set, auditor independence was verified for all companies:

| Company | Ticker | Auditor |
|---------|--------|---------|
| Cathay General Bancorp | CATY | KPMG LLP |
| East West Bancorp | EWBC | KPMG LLP |
| CVB Financial | CVBF | KPMG LLP |
| Hanmi Financial | HAFC | Crowe LLP |
| Columbia Banking System | COLB | Deloitte & Touche LLP |
| Banc of California | BANC | EY LLP |
| Hope Bancorp | HOPE | Crowe LLP |

**Result:** Zero PwC audit clients in the dataset. Independence maintained.

**Source:** DEF 14A proxy statements (2025). Auditor information extracted via automated parser with human validation. Full provenance: `data/proxy/*_DEF14A_extracted.json`

---

## Ops Notes

- **SEC User-Agent:** `CATY Research Team (research@analysis.com)`
- **SEC Rate Limiting:** 0.4s throttle per request (compliance with SEC guidelines)
- **Market Data Source:** Yahoo Finance (via `yfinance` library)
- **Deployment:** GitHub Pages (static site, auto-deploys from main branch)
- **Pre-Commit Hooks:** All validation gates run automatically (see `.git/hooks/pre-commit`)

---

## Contact & Contribution

**Owner:** Nirvan Chitnis

**Repository:** https://github.com/nirvanchitnis-cmyk/caty-equity-research-live

**Live Site:** https://nirvanchitnis-cmyk.github.io/caty-equity-research-live/

**For Contributors:**
1. Read `docs/README.md` for documentation structure
2. Review `docs/governance/CANONICAL_THOUGHT_HEURISTIC_HIGH_STAKES_DOMAINS.md` for project ethos
3. Check recent `docs/journal/` entries for current state
4. Review `docs/postmortems/` to learn from past failures

**Building in Public:** Every commit, reflection, and incident report is public. We document failures as thoroughly as successes.

---

## Success Criteria

For this project, "done" means:
- ✅ All 19 dashboard modules automated (zero hard-coded values)
- ✅ Every number traceable to authoritative source with provenance metadata
- ✅ Reconciliation guard passing (±$0.50 tolerance)
- ✅ Disconfirmer monitor passing (all drivers within tolerance)
- ✅ Publication gate logic enforced (minimum data requirements)
- ✅ Evidence trail complete (primary sources, workpapers, methodologies)
- ✅ Git history preserves all iterations (no force-pushes, no history rewrites)
- ✅ Independence verified (zero conflicts of interest)

**It can always get better.** This README reflects the current state, not the final state.

---

**Last Updated:** 2025-10-24 (Operation Intuitive File System reorganization)
