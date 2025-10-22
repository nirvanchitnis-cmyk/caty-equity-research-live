#!/usr/bin/env python3
"""
Build EPS and TBV/share sensitivities to NIM (±50 bps) and loan growth (±2%).

This is a transparent, first-order bridge to make elasticities explicit.
All inputs are parameterized at the top for quick tuning once Q3 10-Q drops.

Outputs:
  - analysis/sensitivities.json
  - CATY_18_sensitivity_analysis.html (lightweight static page)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "analysis" / "sensitivities.json"
OUT_HTML = ROOT / "CATY_18_sensitivity_analysis.html"


def _ensure_dirs() -> None:
    (ROOT / "analysis").mkdir(parents=True, exist_ok=True)


# Baseline assumptions (update from 10-Q when available)
BASE = {
    "avg_interest_earning_assets": 22000e6,  # $22.0B
    "shares_out": 68.7e6,                    # shares
    "nim": 0.0331,                           # 3.31%
    "tax_rate": 0.23,                        # 23%
    "non_interest_items_eps": 0.15,          # per quarter EPS from non-interest + minus opex after taxes (net), rough
    "quarterly_eps": 1.13,                   # baseline EPS (quarter)
    "tbvps": 41.00,                          # approx TBV/share
}


def eps_from_nim(nim: float, base=BASE) -> float:
    # NII = IEA * NIM (quarterly), EPS impact = (ΔNII * (1 - tax)) / shares
    nii = base["avg_interest_earning_assets"] * nim / 4.0
    eps_nim_only = (nii * (1 - base["tax_rate"])) / base["shares_out"]
    # Add non-interest items approximation (net)
    return eps_nim_only + base["non_interest_items_eps"]


def eps_sensitivity(nim_shift_bps: int, loan_growth_pct: float, base=BASE) -> float:
    # Adjust IEA by loan growth
    adj_iea = base["avg_interest_earning_assets"] * (1 + loan_growth_pct)
    # Adjust NIM by bps shift
    adj_nim = base["nim"] + (nim_shift_bps / 10000.0)
    tmp_base = dict(base)
    tmp_base["avg_interest_earning_assets"] = adj_iea
    return eps_from_nim(adj_nim, base=tmp_base)


def tbvps_sensitivity(buyback_spend_m: float = 0.0, base=BASE) -> float:
    # Simple TBVPS bridge: assume buyback at price ~ P0 reduces shares, TBV moves by (TBV - Price) * shares repurchased / shares
    # This is a placeholder; populate from cash flow statement upon 10-Q.
    return base["tbvps"]


def build_grid() -> Dict:
    grid: List[Dict] = []
    for nim_bps in [-50, -25, 0, 25, 50]:
        row = {"nim_bps": nim_bps}
        for lg in [-0.02, 0.0, 0.02]:
            eps = eps_sensitivity(nim_bps, lg)
            row[f"eps_{int(lg*100)}pct"] = round(eps, 2)
        grid.append(row)
    return {"base": BASE, "grid": grid}


def render_html(payload: Dict) -> str:
    rows = []
    for r in payload["grid"]:
        rows.append(
            f"<tr><td>{r['nim_bps']:+d}</td><td class='numeric'>{r['eps_-2pct']:.2f}</td>"
            f"<td class='numeric'>{r['eps_0pct']:.2f}</td><td class='numeric'>{r['eps_2pct']:.2f}</td></tr>"
        )
    html = f"""<!DOCTYPE html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>CATY - EPS/TBV Sensitivities</title>
<link rel=\"stylesheet\" href=\"styles/caty-equity-research.css\"></head>
<body>
<a href=\"index.html\" class=\"back-button\">← Back to Main Report</a>
<div class=\"container\">
<h1>EPS Sensitivities to NIM and Loan Growth</h1>
<p>Baseline EPS (quarter): {BASE['quarterly_eps']:.2f} | NIM: {BASE['nim']*100:.2f}% | IEA: ${BASE['avg_interest_earning_assets']/1e9:.1f}B | Shares: {BASE['shares_out']/1e6:.1f}M</p>
<table>
<thead><tr><th>Δ NIM (bps)</th><th class=\"numeric\">EPS @ -2% Loans</th><th class=\"numeric\">EPS @ 0%</th><th class=\"numeric\">EPS @ +2% Loans</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody></table>
<p class=\"text-small text-secondary\">Method: First-order bridge EPS = (IEA×NIM/4×(1-tax))/shares + non-interest net. Update BASE from 10-Q.</p>
</div></body></html>"""
    return html


def main() -> int:
    _ensure_dirs()
    payload = build_grid()
    OUT_JSON.write_text(json.dumps(payload, indent=2))
    OUT_HTML.write_text(render_html(payload))
    print(f"Wrote {OUT_JSON} and {OUT_HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

