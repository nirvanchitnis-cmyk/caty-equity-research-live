#!/usr/bin/env python3
"""Combine rate-path and credit-loss scenarios into a probability-weighted outlook."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
RATE_PATH = ROOT / "analysis" / "deposit_rate_scenarios.json"
CREDIT_PATH = ROOT / "analysis" / "credit_stress_scenarios.json"
OUTPUT_PATH = ROOT / "analysis" / "probabilistic_outlook.json"
MARKET_DATA_PATH = ROOT / "data" / "market_data_current.json"

BASE_QUARTERLY_EPS = 1.13  # Q3'25 diluted EPS per 8-K Exhibit 99.1
BASE_TBV = 41.00  # Guardrail TBVPS per Module 18 sensitivity baseline

def load_current_price() -> float:
    if not MARKET_DATA_PATH.exists():
        raise FileNotFoundError(f"Missing market data file: {MARKET_DATA_PATH}")
    payload = json.loads(MARKET_DATA_PATH.read_text())
    price = payload.get("price")
    if price is None:
        raise ValueError("Market data payload missing 'price'")
    return float(price)


CURRENT_PRICE = load_current_price()
CURRENT_P_E = CURRENT_PRICE / (BASE_QUARTERLY_EPS * 4.0)
CURRENT_P_TBV = CURRENT_PRICE / BASE_TBV

# Probabilities anchored to CME FedWatch (22-Oct-2025 15:30 ET snapshot) and IRC credit review.
# FedWatch implies ~50% probability of ≤50 bps cuts by Sep-2026, ~25% hold, remainder skewed to hikes.
RATE_PROB = {
    -100: 0.08,
    -50: 0.22,
    -25: 0.20,
    0: 0.25,
    25: 0.15,
    50: 0.10,
}
# Credit distribution reflects elevated watchlist risk: 50% base, 30% guardrail, 15% stress, 5% severe migration.
CREDIT_PROB = {
    "Base LTM": 0.50,
    "Guardrail": 0.30,
    "Stress": 0.15,
    "Severe": 0.05,
}


@dataclass
class RateScenario:
    fed_change_bps: int
    probability: float
    eps: float  # quarterly EPS from deposit file
    tbvps: float


@dataclass
class CreditScenario:
    name: str
    probability: float
    eps_delta: float  # delta vs base
    tbv_delta: float


def load_rate_scenarios() -> Dict[int, RateScenario]:
    payload = json.loads(RATE_PATH.read_text())
    mapping: Dict[int, RateScenario] = {}
    for item in payload["scenarios"]:
        delta = item["fed_change_bps"]
        if delta not in RATE_PROB:
            continue
        mapping[delta] = RateScenario(
            fed_change_bps=delta,
            probability=RATE_PROB[delta],
            eps=item["quarterly_eps"],
            tbvps=item["tbvps"],
        )
    return mapping


def load_credit_scenarios() -> Dict[str, CreditScenario]:
    payload = json.loads(CREDIT_PATH.read_text())
    mapping: Dict[str, CreditScenario] = {}
    for item in payload["scenarios"]:
        name = item["scenario"]
        if name not in CREDIT_PROB:
            continue
        eps_delta = item["eps"] - BASE_QUARTERLY_EPS
        tbv_delta = item["tbvps"] - BASE_TBV
        mapping[name] = CreditScenario(
            name=name,
            probability=CREDIT_PROB[name],
            eps_delta=eps_delta,
            tbv_delta=tbv_delta,
        )
    return mapping


def annualize_eps(quarterly_eps: float) -> float:
    return quarterly_eps * 4.0


def scenario_price_from_pe(annual_eps: float) -> float:
    return round(annual_eps * CURRENT_P_E, 2)


def scenario_price_from_ptbv(tbvps: float) -> float:
    return round(tbvps * CURRENT_P_TBV, 2)


def combine_scenarios() -> Dict:
    rate_map = load_rate_scenarios()
    credit_map = load_credit_scenarios()

    combined: List[Dict] = []
    expected_price = 0.0
    expected_eps = 0.0
    expected_tbv = 0.0
    probability_sum = 0.0

    for rate in rate_map.values():
        for credit in credit_map.values():
            joint_prob = rate.probability * credit.probability
            adj_eps = rate.eps + credit.eps_delta
            adj_tbv = rate.tbvps + credit.tbv_delta
            annual_eps = annualize_eps(adj_eps)
            pe_price = scenario_price_from_pe(annual_eps)
            ptbv_price = scenario_price_from_ptbv(adj_tbv)
            implied_price = round((pe_price + ptbv_price) / 2.0, 2)
            combined.append(
                {
                    "rate_fed_change_bps": rate.fed_change_bps,
                    "credit_scenario": credit.name,
                    "probability": round(joint_prob, 4),
                    "quarterly_eps": round(adj_eps, 2),
                    "annual_eps": round(annual_eps, 2),
                    "tbvps": round(adj_tbv, 2),
                    "current_pe_at_price": round(CURRENT_PRICE / annual_eps if annual_eps else float('inf'), 2),
                    "current_ptbv_at_price": round(CURRENT_PRICE / adj_tbv if adj_tbv else float('inf'), 2),
                    "implied_price_pe": pe_price,
                    "implied_price_ptbv": ptbv_price,
                    "implied_price_avg": implied_price,
                }
            )
            expected_price += implied_price * joint_prob
            expected_eps += annual_eps * joint_prob
            expected_tbv += adj_tbv * joint_prob
            probability_sum += joint_prob

    expected_price = round(expected_price, 2)
    expected_eps = round(expected_eps, 2)
    expected_tbv = round(expected_tbv, 2)
    probability_sum = round(probability_sum, 4)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "current_price": CURRENT_PRICE,
        "current_forward_pe": round(CURRENT_P_E, 2),
        "current_ptbv": round(CURRENT_P_TBV, 3),
        "rate_probabilities": RATE_PROB,
        "credit_probabilities": CREDIT_PROB,
        "combined_scenarios": combined,
        "probability_sum": probability_sum,
        "expected": {
            "price": expected_price,
            "annual_eps": expected_eps,
            "tbvps": expected_tbv,
        },
    }


def main() -> int:
    payload = combine_scenarios()
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
