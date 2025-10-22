#!/usr/bin/env python3
"""Derive peer valuation comparables for the HOLD corridor analysis."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
PEER_DATA_PATH = ROOT / "data" / "peer_data_raw.json"
PEER_PRICE_PATH = ROOT / "data" / "peer_market_prices.json"
OUTPUT_PATH = ROOT / "data" / "peer_comparables.json"

ASSUMED_COE = 0.10  # 10% hurdle for excess return comparison


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def percentile_rank(population: List[float], value: float) -> float:
    if not population:
        return float("nan")
    sorted_vals = sorted(population)
    below = sum(1 for v in sorted_vals if v < value)
    equal = sum(1 for v in sorted_vals if v == value)
    rank = below + 0.5 * equal
    return round(100.0 * rank / len(sorted_vals), 1)


def build_metrics() -> Dict[str, Any]:
    peer_payload = load_json(PEER_DATA_PATH)
    price_payload = load_json(PEER_PRICE_PATH)

    banks: Dict[str, Dict[str, Any]] = peer_payload.get("banks", {})
    prices: Dict[str, float] = price_payload.get("prices", {})
    price_date = price_payload.get("date")

    metrics: List[Dict[str, Any]] = []

    for ticker, bank in banks.items():
        price = prices.get(ticker)
        tbvps = bank.get("tbvps")
        rote = bank.get("rote_pct")
        net_income = bank.get("net_income_millions")
        annual_factor = bank.get("net_income_annualisation_factor", 4.0)
        shares = bank.get("shares_outstanding_millions")
        cre_pct = bank.get("cre_pct")

        annual_net_income = net_income * annual_factor if net_income is not None else None
        annual_eps = (annual_net_income / shares) if annual_net_income and shares else None

        p_tbv = (price / tbvps) if price and tbvps else None
        p_e = (price / annual_eps) if price and annual_eps else None
        excess_return = (rote / 100.0 - ASSUMED_COE) if rote is not None else None

        metrics.append(
            {
                "ticker": ticker,
                "price": price,
                "price_date": price_date,
                "tbvps": tbvps,
                "p_tbv": round(p_tbv, 3) if p_tbv else None,
                "annual_eps": round(annual_eps, 2) if annual_eps else None,
                "p_e": round(p_e, 1) if p_e else None,
                "rote_pct": rote,
                "roe_minus_10pct_bp": round((excess_return or 0.0) * 10000, 0) if excess_return is not None else None,
                "cre_pct": cre_pct,
            }
        )

    p_tbv_values = [m["p_tbv"] for m in metrics if m["p_tbv"] is not None]
    p_e_values = [m["p_e"] for m in metrics if m["p_e"] is not None]

    caty_metrics = next((m for m in metrics if m["ticker"] == "CATY"), None)
    summary = {
        "peer_count": len(metrics),
        "price_date": price_date,
        "median_p_tbv": round(median(p_tbv_values), 3) if p_tbv_values else None,
        "median_p_e": round(median(p_e_values), 1) if p_e_values else None,
        "caty_percentile": {
            "p_tbv": percentile_rank(p_tbv_values, caty_metrics["p_tbv"]) if caty_metrics and caty_metrics.get("p_tbv") else None,
            "p_e": percentile_rank(p_e_values, caty_metrics["p_e"]) if caty_metrics and caty_metrics.get("p_e") else None,
        },
    }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "price_date": price_date,
        "assumptions": {"assumed_coe_pct": ASSUMED_COE * 100},
        "metrics": metrics,
        "summary": summary,
        "sources": {
            "peer_data": str(PEER_DATA_PATH.relative_to(ROOT)),
            "peer_prices": str(PEER_PRICE_PATH.relative_to(ROOT)),
        },
    }
    return payload


def main() -> int:
    payload = build_metrics()
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
