#!/usr/bin/env python3
"""
Build forward-looking deposit cost and NIM scenarios anchored to regression
outputs in ``analysis/deposit_beta_regressions.json``. Converts beta
coefficients into an explicit bridge from Fed rate moves → deposit costs → NIM →
EPS/TBV so the investment committee can evaluate rate sensitivity without
waiting for the formal 10-Q refresh.

Outputs:
    - analysis/deposit_rate_scenarios.json

Referenced by: CATY_05 (NIM decomposition) and executive summary narrative.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEPOSIT_HISTORY_PATH = ROOT / "data" / "deposit_beta_history.json"
DEPOSIT_REGRESSIONS_PATH = ROOT / "analysis" / "deposit_beta_regressions.json"
SENSITIVITIES_PATH = ROOT / "analysis" / "sensitivities.json"
NIM_META_PATH = ROOT / "data" / "caty05_calculated_tables.json"
OUTPUT_JSON = ROOT / "analysis" / "deposit_rate_scenarios.json"

# Scenarios expressed as Fed funds delta in basis points.
FED_SCENARIOS_BPS = [-100, -75, -50, -25, 0, 25, 50]

# Asset-yield pass-through assumption (delta asset yield / delta Fed funds).
# Calibrated from 2023-2025 NIM disclosures where asset yields lagged Fed moves
# by ~35% on average.
ASSET_BETA = 0.35


@dataclass
class Product:
    code: str
    balance: float  # dollars
    base_rate_pct: float
    beta: float


def load_json(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")
    return json.loads(path.read_text())


def latest_product_snapshot() -> Tuple[Dict[str, Product], float, float]:
    history = load_json(DEPOSIT_HISTORY_PATH)
    quarters: List[Dict] = history["quarters"]
    if not quarters:
        raise RuntimeError("Deposit history dataset is empty")
    latest_metrics = quarters[-1]["metrics"]

    regressions = load_json(DEPOSIT_REGRESSIONS_PATH)["regressions"]

    base_ib_rate_pct = latest_metrics["total_interest_bearing"]["avg_rate_pct"]
    dda_balance = latest_metrics.get("noninterest_demand", {}).get("avg_balance_thousands", 0.0) * 1000.0

    # Anchor to Q3 2025 interest-bearing deposit cost disclosed in the 8-K (3.28%).
    q3_ib_cost_pct = 3.28
    shift = base_ib_rate_pct - q3_ib_cost_pct

    products: Dict[str, Product] = {}
    key_map = {
        "time_deposits": "time_deposits",
        "money_market": "money_market",
        "savings": "savings",
        "interest_bearing_demand": "ib_demand",
    }

    for metrics_key, beta_key in key_map.items():
        metrics = latest_metrics[metrics_key]
        balance = metrics["avg_balance_thousands"] * 1000.0
        adjusted_rate = max(metrics["avg_rate_pct"] - shift, 0.0)
        beta = regressions[beta_key]["beta"]
        products[beta_key] = Product(code=beta_key, balance=balance, base_rate_pct=adjusted_rate, beta=beta)

    return products, q3_ib_cost_pct, dda_balance


def build_eps_helpers():
    base_payload = load_json(SENSITIVITIES_PATH)["base"]

    def eps_from_nim(nim_pct: float) -> float:
        nim = nim_pct / 100.0
        nii = base_payload["avg_interest_earning_assets"] * nim / 4.0
        eps_nim_only = (nii * (1 - base_payload["tax_rate"])) / base_payload["shares_out"]
        return eps_nim_only + base_payload["non_interest_items_eps"]

    def tbv_from_eps(eps: float) -> float:
        payout = base_payload["payout_ratio"]
        retained = eps * (1 - payout)
        baseline_retained = base_payload["quarterly_eps"] * (1 - payout)
        return base_payload["tbvps"] + (retained - baseline_retained)

    return base_payload, eps_from_nim, tbv_from_eps


def load_nim_meta() -> Dict[str, float]:
    nim_meta = load_json(NIM_META_PATH).get("nim_recent", {})
    regressions = load_json(DEPOSIT_REGRESSIONS_PATH)
    return {
        "base_nim_pct": nim_meta.get("net_interest_margin_pct", 3.31),
        "base_asset_yield_pct": nim_meta.get("asset_yield_pct", 5.84),
        "base_funding_cost_pct": nim_meta.get("funding_cost_pct", 3.32),
        "base_fed_funds_pct": regressions["fed_funds_avg"][-1],
    }


def quarterly_interest_expense(balance: float, rate_pct: float) -> float:
    # Return in millions.
    return (balance * (rate_pct / 100.0) / 4.0) / 1e6


def build_scenarios() -> Dict:
    products, base_ib_cost_pct, dda_balance = latest_product_snapshot()
    nim_meta = load_nim_meta()
    base_payload, eps_from_nim, tbv_from_eps = build_eps_helpers()

    total_ib_balance = sum(p.balance for p in products.values())
    total_deposit_balance = total_ib_balance + dda_balance

    base_asset_yield_pct = nim_meta["base_asset_yield_pct"]
    base_fed_pct = nim_meta["base_fed_funds_pct"]
    base_nim_pct = nim_meta["base_nim_pct"]

    base_ib_expense_m = quarterly_interest_expense(total_ib_balance, base_ib_cost_pct)

    scenarios = []
    for delta_bps in FED_SCENARIOS_BPS:
        delta_pct = delta_bps / 100.0
        fed_pct = base_fed_pct + delta_pct

        weighted_cost_pct = 0.0
        product_rates = []
        for product in products.values():
            scenario_rate = max(product.base_rate_pct + product.beta * delta_pct, 0.0)
            weighted_cost_pct += scenario_rate * (product.balance / total_ib_balance)
            product_rates.append(
                {
                    "code": product.code,
                    "balance_m": round(product.balance / 1e6, 1),
                    "base_rate_pct": round(product.base_rate_pct, 2),
                    "scenario_rate_pct": round(scenario_rate, 2),
                }
            )

        all_in_cost_pct = weighted_cost_pct * (total_ib_balance / total_deposit_balance)
        delta_cost_bps = (weighted_cost_pct - base_ib_cost_pct) * 100

        asset_yield_pct = base_asset_yield_pct + ASSET_BETA * delta_pct
        delta_asset_bps = (asset_yield_pct - base_asset_yield_pct) * 100

        scenario_nim_pct = base_nim_pct + (asset_yield_pct - base_asset_yield_pct) - (weighted_cost_pct - base_ib_cost_pct)
        nim_delta_bps = (scenario_nim_pct - base_nim_pct) * 100

        eps = round(eps_from_nim(scenario_nim_pct), 2)
        tbvps = round(tbv_from_eps(eps), 2)

        interest_expense_m = quarterly_interest_expense(total_ib_balance, weighted_cost_pct)
        delta_interest_expense_m = round(interest_expense_m - base_ib_expense_m, 2)

        scenarios.append(
            {
                "fed_change_bps": delta_bps,
                "fed_target_pct": round(fed_pct, 2),
                "deposit_cost_pct": round(weighted_cost_pct, 2),
                "deposit_cost_delta_bps": round(delta_cost_bps, 1),
                "all_in_deposit_cost_pct": round(all_in_cost_pct, 2),
                "asset_yield_pct": round(asset_yield_pct, 2),
                "asset_yield_delta_bps": round(delta_asset_bps, 1),
                "nim_pct": round(scenario_nim_pct, 2),
                "nim_delta_bps": round(nim_delta_bps, 1),
                "quarterly_eps": eps,
                "tbvps": tbvps,
                "interest_expense_delta_m": delta_interest_expense_m,
                "product_rates": product_rates,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base": {
            "fed_funds_pct": base_fed_pct,
            "interest_bearing_cost_pct": base_ib_cost_pct,
            "asset_yield_pct": base_asset_yield_pct,
            "nim_pct": base_nim_pct,
            "asset_beta": ASSET_BETA,
            "total_ib_balance_b": round(total_ib_balance / 1e9, 2),
            "dda_balance_b": round(dda_balance / 1e9, 2),
            "non_interest_eps": round(base_payload["non_interest_items_eps"], 3),
        },
        "scenarios": scenarios,
    }


def main() -> int:
    payload = build_scenarios()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUTPUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
