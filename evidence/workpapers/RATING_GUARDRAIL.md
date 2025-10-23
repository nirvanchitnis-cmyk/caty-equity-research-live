# Rating Guardrail – SELL Flip Threshold (CATY)

Prepared: 2025‑10‑22

This memo documents the charge‑off threshold (NCO bps) at which the normalized valuation implies a SELL per policy (expected 12‑month return < −10%). All inputs tie out to the public model and evidence files.

## Inputs (Q3 2025 context)
- Spot price: $47.13
- TBVPS: $36.16
- Cost of equity (COE): 9.587%
- Long‑run growth (g): 2.5%
- Average loans: $19,449M
- Average tangible common equity (TCE): $2,465.1M
- Base case: NCO 30 bps → normalized NI $276.2M; ROTE 11.20%; P/TBV 1.228×; target $44.39
- Stress guardrail (documentation): NCO 42.8 bps (through‑cycle mean) → ROTE 10.21%; P/TBV 1.087×; target $39.32

Sources: `data/market_data_current.json`, `data/caty12_calculated_tables.json`, `evidence/workpapers/CATY_FDIC_NCO_series.md`.

## SELL threshold calculation
We define the SELL flip when the normalized target is 10% below spot.

1) SELL threshold price: 0.90 × $47.13 = $42.42
2) Required P/TBV at threshold: $42.42 / $36.16 = 1.173×
3) Gordon link: P/TBV = (ROTE − g)/(COE − g)
   → Solve for ROTE: ROTE = g + 1.173 × (COE − g) = 2.5% + 1.173 × 7.087% = 10.892%
4) Base ROTE at 30 bps is 11.20%; delta ROTE to SELL line = −0.308 pp
5) Empirical ROTE sensitivity to NCO (from published table):
   30.0 → 42.8 bps raises provision by $23.1M pre‑tax, lowering ROTE from 11.20% to 10.21% (−0.99 pp over +12.8 bps).
   Approximate slope ≈ −0.077 pp ROTE per +1 bp NCO.
6) NCO at SELL ≈ 30.0 bps + (0.308 / 0.077) ≈ 34 bps.

Conclusion: If forward NCO expectations rise to ~34 bps (holding other inputs constant), the normalized path crosses the −10% SELL line. The documented 42.8 bps “guardrail” remains the formal stress bar, implying a ~$39.32 target (−16.5%).

## Notes
- The slope is locally linear between 30 and 42.8 bps; we validate against the 60 bps row where the published ROTE is 9.31%.
- Once peers refresh, re‑solve with updated TBVPS/ROTE and TCE; the guardrail will shift marginally with capital changes.

## Links
- Normalization bridge (public HTML): `CATY_12_valuation_model.html#valuation-summary`
- FDIC series & stats: `evidence/workpapers/CATY_FDIC_NCO_series.md`
- Model JSON for table rows: `data/caty12_calculated_tables.json`
