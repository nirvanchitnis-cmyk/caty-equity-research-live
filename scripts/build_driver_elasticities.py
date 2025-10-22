#!/usr/bin/env python3
"""Generate an explicit driver-to-financial bridge for EPS sensitivity analysis."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
DEPOSIT_SCENARIOS_PATH = ROOT / "analysis" / "deposit_rate_scenarios.json"
CREDIT_SCENARIOS_PATH = ROOT / "analysis" / "credit_stress_scenarios.json"
INCOME_SNAPSHOT_PATH = ROOT / "data" / "caty02_income_statement.json"
MARKET_DATA_PATH = ROOT / "data" / "market_data_current.json"
OUTPUT_PATH = ROOT / "analysis" / "driver_elasticities.json"

# Rate / credit combinations to surface in the bridge.
BRIDGE_CASES = [
    {"name": "Base run-rate", "fed_delta_bps": 0, "credit": "Base LTM"},
    {"name": "Rate cut 50 bps", "fed_delta_bps": -50, "credit": "Base LTM"},
    {"name": "Credit guardrail", "fed_delta_bps": 0, "credit": "Guardrail"},
    {"name": "Cut 50 bps + guardrail credit", "fed_delta_bps": -50, "credit": "Guardrail"},
    {"name": "Credit stress (85 bps)", "fed_delta_bps": 0, "credit": "Stress"},
]


def load_json(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def load_base_snapshot() -> Dict:
    income_payload = load_json(INCOME_SNAPSHOT_PATH)["q3_2025_snapshot"]
    market_payload = load_json(MARKET_DATA_PATH)
    base = {
        "net_interest_income_m": income_payload["net_interest_income_millions"],
        "noninterest_income_m": income_payload["noninterest_income_millions"],
        "noninterest_expense_m": income_payload["noninterest_expense_millions"],
        "provision_m": income_payload["provision_millions"],
        "net_income_m": income_payload["net_income_millions"],
        "eps": income_payload["eps_diluted"],
        "tax_rate": income_payload["effective_tax_rate_pct"] / 100.0,
        "shares_out_m": market_payload["calculated_metrics"]["shares_outstanding_millions"],
    }
    return base


def index_rate_scenarios() -> Dict[int, Dict]:
    payload = load_json(DEPOSIT_SCENARIOS_PATH)
    return {item["fed_change_bps"]: item for item in payload["scenarios"]}


def index_credit_scenarios() -> Dict[str, Dict]:
    payload = load_json(CREDIT_SCENARIOS_PATH)
    return {item["scenario"]: item for item in payload["scenarios"]}


def compute_bridge() -> Dict:
    base = load_base_snapshot()
    rate_map = index_rate_scenarios()
    credit_map = index_credit_scenarios()

    bridges: List[Dict] = []
    for case in BRIDGE_CASES:
        rate_case = rate_map.get(case["fed_delta_bps"])
        credit_case = credit_map.get(case["credit"])
        if rate_case is None:
            raise KeyError(f"Missing rate scenario for {case['fed_delta_bps']} bps")
        if credit_case is None:
            raise KeyError(f"Missing credit scenario '{case['credit']}'")

        nii = base["net_interest_income_m"] + rate_case["nii_delta_m"]
        provision = base["provision_m"] + credit_case["incremental_provision_m"]
        noninterest_income = base["noninterest_income_m"]
        noninterest_expense = base["noninterest_expense_m"]
        pre_tax = nii + noninterest_income - noninterest_expense - provision
        tax = pre_tax * base["tax_rate"]
        net_income = pre_tax - tax
        eps = net_income / base["shares_out_m"]

        bridge = {
            "name": case["name"],
            "fed_change_bps": case["fed_delta_bps"],
            "credit_scenario": case["credit"],
            "financials": {
                "net_interest_income_m": round(nii, 2),
                "noninterest_income_m": round(noninterest_income, 2),
                "noninterest_expense_m": round(noninterest_expense, 2),
                "provision_m": round(provision, 2),
                "pre_tax_income_m": round(pre_tax, 2),
                "tax_expense_m": round(tax, 2),
                "net_income_m": round(net_income, 2),
                "eps": round(eps, 2),
            },
            "deltas": {
                "nii_delta_m": round(rate_case["nii_delta_m"], 2),
                "interest_expense_delta_m": round(rate_case["interest_expense_delta_m"], 2),
                "provision_delta_m": round(credit_case["incremental_provision_m"], 2),
                "eps_delta": round(eps - base["eps"], 2),
            },
            "inputs": {
                "net_interest_income_base_m": base["net_interest_income_m"],
                "noninterest_income_base_m": base["noninterest_income_m"],
                "noninterest_expense_base_m": base["noninterest_expense_m"],
                "provision_base_m": base["provision_m"],
                "tax_rate": round(base["tax_rate"], 4),
                "shares_out_m": round(base["shares_out_m"], 2),
            },
        }
        bridges.append(bridge)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_snapshot": base,
        "bridge_cases": bridges,
        "metadata": {
            "sources": {
                "net_interest_income": "Form 8-K Exhibit 99.1 (Q3 2025)",
                "deposit_betas": "analysis/deposit_rate_scenarios.json",
                "credit": "analysis/credit_stress_scenarios.json",
                "shares": "data/market_data_current.json",
            }
        },
    }


def main() -> int:
    payload = compute_bridge()
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

