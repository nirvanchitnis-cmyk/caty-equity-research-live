## Board Resubmission Plan — Q3 2025

Audience: CFA Board / IRC judges

Status: Publication Gate ACTIVE — NOT RATED. Targets shown for reference only.

—

### Gating Criteria (must be GREEN before rating)

- Deposit betas (product‑level, last 3 quarters) extracted from Q3 10‑Q [OWNER: Data]
- Peer regression (≥8 West‑Coast regionals) with coefficients + R² [OWNER: Valuation]
- COE triangulation (CAPM, FF3, DDM) refreshed with market data [OWNER: Valuation]

### Scope of Work (mapped to repo)

1) Deposit Betas & NIM Bridge
- Extract product‑level betas from Q3 10‑Q (NOW/MM/Savings/Time; NIB vs IB)
- Build Q2→Q3→Normalized NIM bridge (asset yields, funding costs, betas)
- Files: `scripts/extract_deposit_betas_q10.py` (new), `data/caty05_calculated_tables.json` (update), `CATY_05_nim_decomposition.html` (refresh)

2) Peer Regression (expand to ≥8)
- Universe: EWBC, CVBF, HAFC, COLB, WAFD, PPBI, HOPE, BANC (+ OPBK if clean)
- Publish scatter + coefficients; Cook’s D diagnostics; document exclusions
- Files: `data/caty11_peers_normalized.json`, `CATY_11_peers_normalized.html`

3) Credit Scenarios (EPS/TBVPS impact)
- Three paths: benign (25 bps), base (30 bps), severe (60 bps) with CRE overlays
- Tie provisions to ACL roll‑forward; show TBV erosion and EPS deltas
- Files: `data/caty07_credit_quality.json`, `CATY_07_loans_credit_quality.html`

4) COE Triangulation
- CAPM (Rf, beta, MRP) + FF3 cross‑check; publish inputs/sources
- Align normalized Gordon with COE and growth
- Files: `data/caty16_coe_triangulation.json`, `CATY_16_coe_triangulation.html`

5) Methodology & Reconciliation
- Document formulas and assumptions per model; ensure statement tie‑outs
- Files: `analysis/VALUATION_RECONCILIATION.md`, `analysis/ESG_MATERIALITY_MATRIX.md`

6) ESG Evidence
- Replace narrative claims with quantified, sourced adjustments or remove
- Files: `CATY_17_esg_kpi_dashboard.html`, `data/caty17_esg_kpi.json`

7) Sensitivities
- Valuation per 10 bp changes in NIM, deposit betas, credit cost, COE
- Files: `data/valuation_outputs.json` (extend), `index.html` (new table)

—

### Deliverable Order of Operations
1. Gate check (analysis/publication_gate.py) — must pass
2. Update data (`scripts/update_all_data.py`) and rebuild site
3. Run reconciliation guard (CI + local)
4. Flip rating to BUY/HOLD/SELL per policy in `analysis/rating_policy.md`

### SLA
- Deposit betas ≤ 24h post 10‑Q
- Peer regression + COE ≤ 48h after last peer files

