---
title: Scenario Provenance
generated_at: 2025-10-22T22:40:05Z
---

# Rate Path Inputs

- **Data source:** CME FedWatch (ZQ Fed Funds futures) harvested via manual snapshot and captured in `analysis/fedwatch_snapshot.json`.
- **Contracts:**  
  - `ZQH26` (Mar-2026 settlement) – weight 60%  
  - `ZQU26` (Sep-2026 settlement) – weight 40%
- **Snapshot timestamp:** 2025-10-22 19:10:40 UTC (pre-close)  
- **Refresh cadence:** pull at 21:30 UTC daily; rebuild probability grid if any bucket shifts by ≥5 percentage points.

| Δ Fed Funds (bps) | Probability | Source Contract Mix | Notes |
| --- | --- | --- | --- |
| -100 | 8% | ZQH26/ZQU26 blend | Implies two cuts by Sep-26 |
| -50 | 22% | ZQH26/ZQU26 blend | Base easing path |
| -25 | 20% | ZQH26/ZQU26 blend | Mild easing |
| 0 | 25% | ZQH26/ZQU26 blend | Hold scenario |
| +25 | 15% | ZQH26/ZQU26 blend | Hawkish |
| +50 | 10% | ZQH26/ZQU26 blend | Hawkish tail |

> **Decision rule:** `scripts/build_probabilistic_scenarios.py` will be re-run automatically when the rolling FedWatch pull detects any bucket shift ≥5 ppts or when market close prints a new CATY spot.

# Credit Severity Mix

- **Data source:** `analysis/credit_stress_scenarios.json` (guardrail derived from FDIC NTLNLSCOQR).  
- **Distribution rationale:** Watchlist review (movie-theatre exposures) and through-cycle NCO history.

| Scenario | Weight | NCO (bps) | Incremental Provision ($M) | Evidence |
| --- | --- | --- | --- | --- |
| Base LTM | 50% | 18.1 | 0.0 | Q3 2025 8-K Exhibit 99.1 |
| Guardrail | 30% | 42.8 | 12.4 | FDIC NTLNLSCOQR 90th percentile |
| Stress | 15% | 85.0 | 33.6 | Watchlist migration (movie theatre loans) |
| Severe | 5% | 120.0 | 51.2 | GFC analogue tail |

> **Refresh SLA:** Update credit mix once Q3 10-Q discloses criticized-loan migration. If watchlist migration ≥20% or provision trend breaches `analysis/credit_stress_scenarios.json` guardrail, rerun mix within 6 hours.

# Automation Hooks

- **Pricing trigger:** `scripts/fetch_live_price.py` → `analysis/probabilistic_outlook.json` (rebuild immediately after market close).  
- **Deposit beta pipeline:** Q3 10-Q filing window monitored via EDGAR RSS; schedule `scripts/extract_deposit_betas_q10.py` + `scripts/compute_deposit_beta_regressions.py` + `scripts/build_probabilistic_scenarios.py` at **2025-10-30 02:00 UTC** (or within 4 hours of filing).  
- **Audit trail:** regenerated JSON artefacts are captured in Git with timestamps; see commit metadata for run logs.
