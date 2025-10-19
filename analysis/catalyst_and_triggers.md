# CATY Catalyst & Kill-Switch Framework (Draft)

**Generated:** 2025-10-19
**Purpose:** Give Claude a concrete monitoring playbook that supports a HOLD call and defines when to pivot. All dates and ownership assignments should be validated before publication.

---

## Near-Term Catalysts (0-3 Months)

| Timing | Catalyst | Evidence To Capture | Thesis Impact |
|--------|----------|---------------------|---------------|
| ~Oct 28 2025 (est.) | Q3'25 earnings release & call | 10-Q, transcript, slide deck (if issued) | Update provision trajectory, deposit beta guidance, CRE commentary |
| Week of Nov 10 2025 | Fed Senior Loan Officer Opinion Survey | Survey PDF (CRE, C&I, lending standards) | If CRE underwriting is tightening, increases probability of normalization scenario |
| Nov 2025 | FDIC SDI data refresh (Q3 2025 call report) | Download RC-C & charge-off schedules | Re-baseline CRE balances, owner-occupied mix |
| Late Nov 2025 | KBW / Piper investor conferences | Speaker remarks or deck | Any public commitment to de-risk CRE would lower normalization probability |
| Dec 2025 | FOMC meeting & SEP | Fed statement, SEP projections | Funding cost outlook; adjust deposit beta elasticity |

## Medium-Term Catalysts (3-12 Months)

| Timing | Catalyst | Evidence To Capture | Thesis Impact |
|--------|----------|---------------------|---------------|
| Jan 2026 | Q4'25 earnings / FY guidance | 10-K, transcript | Capital actions for 2026, reserve build plans |
| Feb-Mar 2026 | Regulatory stress test / capital plan submission | Public FR Y-9C excerpts (if available) | Confirmation of CET1 guardrails |
| Semi-annual | CRE portfolio analytics (Trepp, RCA) | Rent rolls, occupancy data by office subtype | Validates or falsifies CRE loss severity |
| Quarterly | Moody's / Fitch outlook updates | Rating agency action notices | Downgrade risk = higher COE assumption |

## Kill-Switch Metrics

| Metric | Threshold | Data Source | Action |
|--------|-----------|-------------|--------|
| Total loan NCO ratio (quarterly annualized) | >35 bps for 2 consecutive quarters *or* trailing-4q average >30 bps | FDIC call report / 10-Q | Shift probability weighting ≥70% normalization; revisit HOLD vs SELL |
| CRE concentration | <45% of loans | FDIC RC-C, management disclosure | Reduce CRE premium assumption; re-open BUY debate |
| Deposit beta | >55% cumulative beta since 2022 | Company disclosures, call Q&A | Increase provisioning of funding drag; consider SELL if combined with higher NCO |
| CET1 ratio | <10.0% pro forma after buybacks | Capital stress workbook | Force buyback suspension assumption; tighten valuation multiple |
| Office occupancy trend (core markets) | Vacancy improves ≥200 bps YoY | CBRE / Trepp data | Use as disconfirming signal; lower normalization probability |

## Monitoring Checklist

1. **Quarterly (earnings week):**
   - Refresh `analysis/nco_probability_analysis.py` with new FDIC data
   - Update ACL bridge and reserve walk
   - Record management guidance on credit costs, CRE strategy, capital allocation
2. **Monthly:**
   - Track CRE market data (CBRE, Trepp) for CA/NY office segments
   - Log deposit pricing moves from rate sheets / competitor filings
3. **Ad-hoc:**
   - Capture any regulatory or rating agency actions immediately in `evidence/README.md`
   - Document disconfirming evidence (e.g., loan growth capped, CRE run-off plan)

## Ownership & Next Steps

| Deliverable | Owner | Due | Notes |
|-------------|-------|-----|-------|
| Update catalyst calendar with confirmed dates | Claude | Oct 22 2025 | Verify IR website / investor relations contacts |
| Build CDS / spread monitor (if data accessible) | Nirvan / Derek | TBD | Requires Bloomberg or ICE access |
| Integrate kill-switch metrics into executive summary | Claude | Next Derek submission | Add to HOLD rationale section |
| Automate FDIC pull & probability table post-quarter | Claude | With next 10-Q | Extend `nco_probability_analysis.py` to accept dynamic quarter |

---

**Usage:** Claude can now cite the tables above when Derek asks for catalysts and kill-switch triggers. Update this document whenever a catalyst fires or thresholds are crossed; append evidence links in `evidence/README.md` for auditability.
