"""
DUAL VALUATION BRIDGE - Regression vs Gordon Growth Reconciliation
Now exposes callable helpers so automation pipelines can depend on the logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "market_data_current.json"
PEER_PATH = Path(__file__).resolve().parents[1] / "data" / "caty11_peers_normalized.json"


def _to_decimal(value: float) -> float:
    """Convert a percentage expressed as 10.5 -> 0.105."""
    if value is None:
        raise ValueError("Cannot convert None to decimal")
    return value / 100 if value > 1 else value


def calculate_regression_target(roae: float, tbvps: float) -> Dict[str, Any]:
    """Calculate regression-based target price."""
    if roae is None or tbvps is None:
        raise ValueError("ROAE and TBVPS are required for regression target")

    ptbv_multiple = 0.058 * roae + 0.82
    target_price = ptbv_multiple * tbvps

    return {
        "target_price": round(target_price, 2),
        "target_ptbv": round(ptbv_multiple, 3),
        "method": "Regression",
        "equation": "P/TBV = 0.058 × ROAE + 0.82",
        "r_squared": 0.68,
        "inputs": {"roae": roae, "tbvps": tbvps},
    }


def calculate_normalized_target(
    rote: float,
    tbvps: float,
    coe: float = 0.09587,
    g: float = 0.025,
) -> Dict[str, Any]:
    """Calculate Gordon Growth normalized target."""
    if rote is None or tbvps is None:
        raise ValueError("ROTE and TBVPS are required for normalized target")

    rote_decimal = _to_decimal(rote)
    ptbv_multiple = (rote_decimal - g) / (coe - g)
    target_price = ptbv_multiple * tbvps

    return {
        "target_price": round(target_price, 2),
        "target_ptbv": round(ptbv_multiple, 3),
        "method": "Normalized (Gordon Growth)",
        "inputs": {"rote": rote, "tbvps": tbvps, "coe": coe, "g": g},
    }


def load_market_data(path: Path = DATA_PATH) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_peer_context(path: Path = PEER_PATH) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    market_data = load_market_data()
    metrics = market_data.get("calculated_metrics", {})
    price = market_data.get("price")
    price_date = market_data.get("price_date")

    tbvps = metrics.get("tbvps")
    roae = metrics.get("rote_ltm_pct")
    normalized_rote = metrics.get("normalized_rote_pct", roae)
    coe = _to_decimal(metrics.get("implied_coe_pct", 9.587))

    if tbvps is None or roae is None or price is None:
        raise ValueError("Missing required inputs in market_data_current.json")

    peer_context = load_peer_context()
    regression = calculate_regression_target(roae, tbvps)
    normalized = calculate_normalized_target(normalized_rote, tbvps, coe=coe)

    regression_return = ((regression["target_price"] - price) / price) * 100
    normalized_return = ((normalized["target_price"] - price) / price) * 100

    print(f"PATH A (Regression): ${regression['target_price']:.2f} ({regression_return:+.1f}%)")
    print(f"PATH B (Normalized): ${normalized['target_price']:.2f} ({normalized_return:+.1f}%)")
    print(f"\nMarket Data: ${price:.2f} as of {price_date}")
    print(f"Peer cohort: {peer_context.get('regression_universe', {}).get('regression_peers', [])}")

    target_gap = regression["target_price"] - normalized["target_price"]
    print(f"Gap: ${target_gap:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
