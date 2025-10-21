#!/usr/bin/env python3
"""
Valuation orchestrator that recalculates target prices and expected returns.

Reads the merged market data JSON, executes valuation logic, and writes both
the detailed valuation outputs as well as summary metrics embedded in
market_data_current.json.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.probability_weighted_valuation import calculate_wilson_weighted
from analysis.valuation_bridge_final import (
    calculate_normalized_target,
    calculate_regression_target,
    load_market_data,
    load_peer_context,
)

DATA_DIR = ROOT / "data"

MARKET_DATA_PATH = DATA_DIR / "market_data_current.json"
VALUATION_OUTPUTS_PATH = DATA_DIR / "valuation_outputs.json"
PEER_DATA_PATH = DATA_DIR / "caty11_peers_normalized.json"

# IRC blended uses Residual Income (RIM) and Dividend Discount Model (DDM) anchors
RIM_TARGET_PRICE = 50.08
DDM_TARGET_PRICE = 45.12
IRC_WEIGHTS = {"rim": 0.60, "ddm": 0.10, "regression": 0.30}


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")


def compute_return(target_price: float, current_price: float) -> float:
    return round(((target_price - current_price) / current_price) * 100, 1)


def main() -> int:
    market_data = load_market_data(MARKET_DATA_PATH)
    metrics = market_data.setdefault("calculated_metrics", {})
    peer_context = load_peer_context(PEER_DATA_PATH)

    current_price = market_data.get("price")
    tbvps = metrics.get("tbvps")
    roae = metrics.get("rote_ltm_pct")
    normalized_rote = metrics.get("normalized_rote_pct", roae)
    coe = metrics.get("implied_coe_pct", 9.587)
    coe_decimal = coe / 100 if coe and coe > 1 else coe

    if current_price is None or tbvps is None or roae is None:
        raise ValueError("market_data_current.json missing price, tbvps, or rote_ltm_pct")

    timestamp_dt = datetime.now(timezone.utc)
    timestamp = timestamp_dt.isoformat()
    timestamp_display = timestamp_dt.strftime("%B %d, %Y %H:%M UTC")

    regression = calculate_regression_target(roae, tbvps)
    normalized = calculate_normalized_target(normalized_rote, tbvps, coe=coe_decimal)
    wilson = calculate_wilson_weighted(regression["target_price"], normalized["target_price"])

    # IRC blended target uses the fresh regression output
    irc_target_price = round(
        IRC_WEIGHTS["rim"] * RIM_TARGET_PRICE
        + IRC_WEIGHTS["ddm"] * DDM_TARGET_PRICE
        + IRC_WEIGHTS["regression"] * regression["target_price"],
        2,
    )

    methods: Dict[str, Dict[str, Any]] = {}

    regression_entry = deepcopy(regression)
    regression_entry["return_pct"] = compute_return(regression_entry["target_price"], current_price)
    regression_entry["last_calculated"] = timestamp
    regression_entry["inputs"] = {
        **regression.get("inputs", {}),
        "price": current_price,
        "peer_sample": peer_context.get("regression_universe", {}).get("regression_peers"),
        "coefficients": {"slope": 0.058, "intercept": 0.82},
    }
    methods["regression"] = regression_entry

    normalized_entry = deepcopy(normalized)
    normalized_entry["return_pct"] = compute_return(normalized_entry["target_price"], current_price)
    normalized_entry["last_calculated"] = timestamp
    normalized_entry["inputs"] = {
        **normalized.get("inputs", {}),
        "price": current_price,
        "through_cycle_nco_bps": metrics.get("through_cycle_nco_bps"),
    }
    methods["normalized"] = normalized_entry

    wilson_entry = deepcopy(wilson)
    wilson_entry["return_pct"] = compute_return(wilson_entry["target_price"], current_price)
    wilson_entry["last_calculated"] = timestamp
    wilson_entry["inputs"] = {
        **wilson.get("inputs", {}),
        "price": current_price,
        "probabilities": wilson.get("probabilities"),
    }
    methods["wilson_95"] = wilson_entry

    irc_entry = {
        "target_price": irc_target_price,
        "target_ptbv": round(irc_target_price / tbvps, 3),
        "method": "IRC Blended (60% RIM / 10% DDM / 30% Regression)",
        "weights": IRC_WEIGHTS,
        "inputs": {
            "rim_target": RIM_TARGET_PRICE,
            "ddm_target": DDM_TARGET_PRICE,
            "regression_target": regression_entry["target_price"],
        },
        "return_pct": compute_return(irc_target_price, current_price),
        "last_calculated": timestamp,
    }
    methods["irc_blended"] = irc_entry

    existing_outputs = {}
    if VALUATION_OUTPUTS_PATH.exists():
        existing_outputs = load_json(VALUATION_OUTPUTS_PATH)

    valuation_outputs: Dict[str, Any] = {
        "metadata": {
            "calculation_run": timestamp,
            "price_used": round(current_price, 2),
        },
        "methods": methods,
    }

    if existing_outputs.get("scenarios"):
        valuation_outputs["scenarios"] = existing_outputs["scenarios"]

    frameworks = existing_outputs.get("frameworks", {})
    frameworks.update(
        {
            "wilson_95": {
                "target_price": wilson_entry["target_price"],
                "composition": "60.9% Regression + 39.1% Normalized",
                "return_pct": wilson_entry["return_pct"],
                "last_calculated": timestamp,
            },
            "irc_blended": {
                "target_price": irc_entry["target_price"],
                "composition": "60% RIM + 10% DDM + 30% Regression",
                "return_pct": irc_entry["return_pct"],
                "last_calculated": timestamp,
            },
        }
    )
    valuation_outputs["frameworks"] = frameworks

    if existing_outputs.get("assumptions"):
        valuation_outputs["assumptions"] = existing_outputs["assumptions"]

    valuation_outputs["last_updated"] = timestamp

    save_json(VALUATION_OUTPUTS_PATH, valuation_outputs)

    # Update market data calculated metrics
    metrics["target_regression"] = regression_entry["target_price"]
    metrics["return_regression_pct"] = regression_entry["return_pct"]
    metrics["target_normalized"] = normalized_entry["target_price"]
    metrics["return_normalized_pct"] = normalized_entry["return_pct"]
    metrics["target_wilson_95"] = wilson_entry["target_price"]
    metrics["return_wilson_95_pct"] = wilson_entry["return_pct"]
    metrics["target_irc_blended"] = irc_entry["target_price"]
    metrics["return_irc_blended_pct"] = irc_entry["return_pct"]
    metrics["current_ptbv"] = round(current_price / tbvps, 3)
    metrics["normalized_ptbv"] = normalized_entry["target_ptbv"]

    market_data["report_generated"] = timestamp
    report_metadata = market_data.setdefault("report_metadata", {})
    report_metadata["last_updated_utc"] = timestamp
    report_metadata["generated_at_display"] = timestamp_display

    price_date_iso = market_data.get("price_date")
    if price_date_iso:
        try:
            price_date_display = datetime.strptime(price_date_iso, "%Y-%m-%d").strftime("%B %d, %Y")
        except ValueError:
            price_date_display = price_date_iso
    else:
        price_date_iso = timestamp_dt.date().isoformat()
        price_date_display = timestamp_dt.strftime("%B %d, %Y")

    report_metadata["report_date_iso"] = price_date_iso
    report_metadata["report_date"] = price_date_display

    save_json(MARKET_DATA_PATH, market_data)

    print("Valuation metrics recalculated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
