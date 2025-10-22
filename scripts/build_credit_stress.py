#!/usr/bin/env python3
"""Build credit loss stress scenarios translating NCO assumptions into EPS/TBV hits."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
SENS_PATH = ROOT / "analysis" / "sensitivities.json"
OUTPUT_PATH = ROOT / "analysis" / "credit_stress_scenarios.json"

BASE_LOAN_BALANCE = 20.10e9  # Q3 2025 gross loans, USD
BASE_PROVISION_M = 28.7  # Q3 provision, USD millions
BASE_NCO_BPS = 18.1  # LTM NCO from 8-K

SCENARIOS = [
    {"name": "Base LTM", "nco_bps": 18.1, "label": "Q3 run-rate"},
    {"name": "Guardrail", "nco_bps": 42.8, "label": "Through-cycle mean"},
    {"name": "Stress", "nco_bps": 85.0, "label": "2× guardrail"},
]


def load_base() -> Dict:
    payload = json.loads(SENS_PATH.read_text())["base"]
    return payload


def eps_from_additional_provision(base: Dict, extra_provision_m: float) -> float:
    eps_hit = (extra_provision_m * 1e6 * (1 - base["tax_rate"])) / base["shares_out"]
    return round(eps_hit, 2)


def tbv_from_eps(base: Dict, eps: float) -> float:
    payout = base["payout_ratio"]
    retained = eps * (1 - payout)
    baseline_retained = base["quarterly_eps"] * (1 - payout)
    return round(base["tbvps"] + (retained - baseline_retained), 2)


def build_scenarios() -> Dict:
    base = load_base()
    results: List[Dict] = []

    for scenario in SCENARIOS:
        nco_bps = scenario["nco_bps"]
        incremental_bps = max(nco_bps - BASE_NCO_BPS, 0.0)
        incremental_loss = (incremental_bps / 10000.0) * BASE_LOAN_BALANCE / 4.0  # quarterly USD
        incremental_loss_m = incremental_loss / 1e6
        eps_hit = eps_from_additional_provision(base, incremental_loss_m)
        eps = round(base["quarterly_eps"] - eps_hit, 2)
        tbv = tbv_from_eps(base, eps)
        provision = BASE_PROVISION_M + incremental_loss_m
        results.append(
            {
                "scenario": scenario["name"],
                "descriptor": scenario["label"],
                "nco_bps": nco_bps,
                "incremental_bps": round(incremental_bps, 1),
                "provision_m": round(provision, 1),
                "incremental_provision_m": round(incremental_loss_m, 1),
                "eps": eps,
                "eps_hit": eps_hit,
                "tbvps": tbv,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base": {
            "loan_balance_b": round(BASE_LOAN_BALANCE / 1e9, 2),
            "nco_bps": BASE_NCO_BPS,
            "provision_m": BASE_PROVISION_M,
        },
        "scenarios": results,
        "assumptions": {
            "tax_rate": load_base()["tax_rate"],
            "shares_out_m": round(load_base()["shares_out"] / 1e6, 2),
            "payout_ratio": load_base()["payout_ratio"],
        },
    }


def main() -> int:
    payload = build_scenarios()
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
