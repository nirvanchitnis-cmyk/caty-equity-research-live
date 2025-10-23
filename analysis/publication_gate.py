#!/usr/bin/env python3
"""
Publication Gate: Enforce NOT RATED status until controlling inputs are final.

Checks:
 1) Deposit betas present and not flagged TBD/Pending in market_data_current.json
 2) Peer regression universe >= 8 and coefficients present in caty11_peers_normalized.json
 3) COE triangulation present in data/caty16_coe_triangulation.json (if available)

Exit codes:
 0 -> Gates clear (safe to publish rating)
 1 -> Gates not clear (NOT RATED)

Prints a short summary for CI logs.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def is_number(x: Any) -> bool:
    try:
        float(x)
        return True
    except Exception:
        return False


def main() -> int:
    reasons: list[str] = []

    market = load_json(ROOT / "data" / "market_data_current.json")
    metrics = market.get("calculated_metrics", {}) if isinstance(market, dict) else {}

    # Gate 1: Deposit betas present (both all-in and IB) and numeric
    beta_ib = metrics.get("deposit_beta_interest_bearing")
    beta_all = metrics.get("deposit_beta_all_in")
    if not (is_number(beta_ib) and is_number(beta_all)):
        reasons.append("Deposit betas pending (product-level required post-10-Q)")

    # Gate 2: Peer regression sample actually used must be >= 8 (not just total universe)
    peers = load_json(ROOT / "data" / "caty11_peers_normalized.json")
    uni = (peers.get("regression_universe") or {}) if isinstance(peers, dict) else {}
    stats = peers.get("regression_stats") or {}
    sample_size = stats.get("sample_size")
    slope = stats.get("slope")
    intercept = stats.get("intercept")
    if not (is_number(sample_size) and int(sample_size) >= 8 and is_number(slope) and is_number(intercept)):
        reasons.append("Peer regression incomplete (sample < 8 or coefficients missing)")

    # Gate 3: COE triangulation available (required)
    coe = load_json(ROOT / "data" / "caty16_coe_triangulation.json")
    if not coe:
        reasons.append("COE triangulation not finalized")

    # Gate 4: Deposit beta history with >= 3 quarters present in NIM module tables
    deposit_history = load_json(ROOT / "data" / "deposit_beta_history.json")
    quarters = deposit_history.get("quarters") if isinstance(deposit_history, dict) else None
    if not quarters or len(quarters) < 3:
        reasons.append("Deposit beta product-level history < 3 quarters")

    if reasons:
        print("Publication Gate: NOT RATED")
        for r in reasons:
            print(f" - {r}")
        return 1

    print("Publication Gate: CLEAR — safe to publish rating")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
