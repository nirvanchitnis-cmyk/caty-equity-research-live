#!/usr/bin/env python3
"""Combine rate-path and credit-loss scenarios into a probability-weighted outlook."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
RATE_PATH = ROOT / "analysis" / "deposit_rate_scenarios.json"
CREDIT_PATH = ROOT / "analysis" / "credit_stress_scenarios.json"
OUTPUT_PATH = ROOT / "analysis" / "probabilistic_outlook.json"
MARKET_DATA_PATH = ROOT / "data" / "market_data_current.json"
FEDWATCH_PATH = ROOT / "analysis" / "fedwatch_snapshot.json"

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


@dataclass
class RateScenario:
    fed_change_bps: int
    probability: float
    eps: float  # quarterly EPS from deposit file
    tbvps: float
    metadata: Dict[str, float]


@dataclass
class CreditScenario:
    name: str
    probability: float
    eps_delta: float  # delta vs base
    tbv_delta: float
    nco_bps: float
    incremental_bps: float
    incremental_provision_m: float


def load_rate_probabilities() -> Tuple[Dict[int, float], Dict]:
    payload = json.loads(FEDWATCH_PATH.read_text())
    raw_probs = payload.get("probabilities", {})
    probabilities = {int(k): float(v) for k, v in raw_probs.items()}
    metadata = {
        "source": payload.get("source"),
        "captured_at": payload.get("captured_at"),
        "contracts": payload.get("contracts"),
        "notes": payload.get("notes"),
    }
    return probabilities, metadata


def load_credit_probabilities() -> Tuple[Dict[str, float], Dict[str, str]]:
    # Distribution reflects watchlist review and prior cycle default/severity mix.
    probabilities = {
        "Base LTM": 0.50,
        "Guardrail": 0.30,
        "Stress": 0.15,
        "Severe": 0.05,
    }
    rationale = {
        "Base LTM": "Q3 2025 run-rate (18 bps NCO) with stable watchlist",
        "Guardrail": "Through-cycle mean 42.8 bps derived from FDIC NTLNLSCOQR",
        "Stress": "Emerge of two large movie theatre loans; doubles guardrail (85 bps)",
        "Severe": "GFC analogue; 3× LTM (120 bps) reflecting tail liquidity run",
    }
    return probabilities, rationale


def load_rate_scenarios(rate_prob: Dict[int, float]) -> Dict[int, RateScenario]:
    payload = json.loads(RATE_PATH.read_text())
    mapping: Dict[int, RateScenario] = {}
    for item in payload["scenarios"]:
        delta = item["fed_change_bps"]
        if delta not in rate_prob:
            continue
        mapping[delta] = RateScenario(
            fed_change_bps=delta,
            probability=rate_prob[delta],
            eps=item["quarterly_eps"],
            tbvps=item["tbvps"],
            metadata={
                "deposit_cost_delta_bps": item.get("deposit_cost_delta_bps"),
                "nim_delta_bps": item.get("nim_delta_bps"),
                "nii_delta_m": item.get("nii_delta_m"),
            },
        )
    return mapping


def load_credit_scenarios(credit_prob: Dict[str, float]) -> Dict[str, CreditScenario]:
    payload = json.loads(CREDIT_PATH.read_text())
    mapping: Dict[str, CreditScenario] = {}
    for item in payload["scenarios"]:
        name = item["scenario"]
        if name not in credit_prob:
            continue
        eps_delta = item["eps"] - BASE_QUARTERLY_EPS
        tbv_delta = item["tbvps"] - BASE_TBV
        mapping[name] = CreditScenario(
            name=name,
            probability=credit_prob[name],
            eps_delta=eps_delta,
            tbv_delta=tbv_delta,
            nco_bps=float(item["nco_bps"]),
            incremental_bps=float(item.get("incremental_bps", 0.0)),
            incremental_provision_m=float(item.get("incremental_provision_m", 0.0)),
        )
    return mapping


def annualize_eps(quarterly_eps: float) -> float:
    return quarterly_eps * 4.0


def combine_scenarios() -> Dict:
    current_price = load_current_price()
    current_p_e = current_price / (BASE_QUARTERLY_EPS * 4.0)
    current_p_tbv = current_price / BASE_TBV

    rate_prob, rate_meta = load_rate_probabilities()
    credit_prob, credit_notes = load_credit_probabilities()

    rate_map = load_rate_scenarios(rate_prob)
    credit_map = load_credit_scenarios(credit_prob)

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
            pe_price = round(annual_eps * current_p_e, 2)
            ptbv_price = round(adj_tbv * current_p_tbv, 2)
            implied_price = round((pe_price + ptbv_price) / 2.0, 2)
            combined.append(
                {
                    "rate_fed_change_bps": rate.fed_change_bps,
                    "credit_scenario": credit.name,
                    "probability": round(joint_prob, 4),
                    "quarterly_eps": round(adj_eps, 2),
                    "annual_eps": round(annual_eps, 2),
                    "tbvps": round(adj_tbv, 2),
                    "current_pe_at_price": round(current_price / annual_eps if annual_eps else float("inf"), 2),
                    "current_ptbv_at_price": round(current_price / adj_tbv if adj_tbv else float("inf"), 2),
                    "implied_price_pe": pe_price,
                    "implied_price_ptbv": ptbv_price,
                    "implied_price_avg": implied_price,
                    "rate_detail": rate.metadata,
                    "credit_detail": {
                        "nco_bps": credit.nco_bps,
                        "incremental_bps": credit.incremental_bps,
                        "incremental_provision_m": credit.incremental_provision_m,
                    },
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
        "current_price": current_price,
        "current_forward_pe": round(current_p_e, 2),
        "current_ptbv": round(current_p_tbv, 3),
        "rate_probabilities": rate_prob,
        "credit_probabilities": credit_prob,
        "combined_scenarios": combined,
        "probability_sum": probability_sum,
        "expected": {
            "price": expected_price,
            "annual_eps": expected_eps,
            "tbvps": expected_tbv,
        },
        "metadata": {
            "rate_path": rate_meta,
            "credit_mix_notes": credit_notes,
            "credit_scenarios_source": str(CREDIT_PATH.relative_to(ROOT)),
            "rate_scenarios_source": str(RATE_PATH.relative_to(ROOT)),
        },
    }


def main() -> int:
    payload = combine_scenarios()
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
