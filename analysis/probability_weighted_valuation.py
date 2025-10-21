"""
Probability-Weighted Valuation Analysis
Provides callable helpers for Wilson score blending of valuation targets.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.valuation_bridge_final import (  # noqa: E402
    calculate_normalized_target,
    calculate_regression_target,
    load_market_data,
)


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "market_data_current.json"


def calculate_wilson_weighted(
    regression_target: float,
    normalized_target: float,
    prob_regression: float = 0.609,
) -> Dict[str, Any]:
    """Calculate Wilson probability-weighted target."""
    prob_normalized = 1 - prob_regression
    wilson_target = (prob_regression * regression_target) + (prob_normalized * normalized_target)

    return {
        "target_price": round(wilson_target, 2),
        "method": "Wilson 95% Probability-Weighted",
        "probabilities": {
            "regression": round(prob_regression, 3),
            "normalized": round(prob_normalized, 3),
        },
        "inputs": {
            "regression_target": regression_target,
            "normalized_target": normalized_target,
        },
    }


def main() -> int:
    market_data = load_market_data(DATA_PATH)
    metrics = market_data.get("calculated_metrics", {})
    price = market_data.get("price")
    tbvps = metrics.get("tbvps")
    roae = metrics.get("rote_ltm_pct")
    normalized_rote = metrics.get("normalized_rote_pct", roae)

    if price is None or tbvps is None or roae is None:
        raise ValueError("Missing required inputs in market_data_current.json")

    regression = calculate_regression_target(roae, tbvps)
    normalized = calculate_normalized_target(normalized_rote, tbvps)
    wilson = calculate_wilson_weighted(regression["target_price"], normalized["target_price"])

    expected_return = ((wilson["target_price"] - price) / price) * 100

    print(
        "Wilson Weighted Target: "
        f"${wilson['target_price']:.2f} ({expected_return:+.1f}%) "
        f"[{wilson['probabilities']['regression']*100:.1f}% regression / "
        f"{wilson['probabilities']['normalized']*100:.1f}% normalized]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
