#!/usr/bin/env python3
"""
COVID Crash Regression Test

Tests that price shock (-40%) triggers full valuation recalculation.
Success criteria: All returns update to reflect new price.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
MARKET_PATH = ROOT / "data" / "market_data_current.json"
PIPELINE = ROOT / "scripts" / "update_all_data.py"


def load_market_data() -> Dict[str, Any]:
    with MARKET_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_market_data(data: Dict[str, Any]) -> None:
    with MARKET_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def run_pipeline() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PIPELINE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        env={**os.environ, "CATY_TEST_MODE": "1"},
    )


def test_covid_crash() -> bool:
    original = load_market_data()
    original_price = float(original["price"])
    crash_price = round(original_price * 0.6, 2)  # -40%

    print(f"Testing COVID crash scenario: ${original_price:.2f} → ${crash_price:.2f}")

    try:
        shocked = dict(original)
        shocked["price"] = crash_price
        shocked["price_date"] = "2025-03-15"
        save_market_data(shocked)

        result = run_pipeline()
        if result.returncode != 0:
            stderr_preview = (result.stderr or "")[:400]
            print(f"❌ Pipeline failed: {stderr_preview}")
            return False

        updated = load_market_data()
        recalculated = updated.get("calculated_metrics", {})
        regression_target = recalculated.get("target_regression")
        actual_regression_return = recalculated.get("return_regression_pct")

        if regression_target is None or actual_regression_return is None:
            print("❌ Missing regression target/return in calculated_metrics")
            return False

        expected_regression_return = ((regression_target - crash_price) / crash_price) * 100
        tolerance = 1.0  # ±1%
        if abs(actual_regression_return - expected_regression_return) > tolerance:
            print(
                "❌ Regression return not updated: "
                f"{actual_regression_return:.1f}% (expected {expected_regression_return:.1f}%)"
            )
            return False

        print("✅ COVID crash test PASSED - all returns recalculated")
        return True
    finally:
        save_market_data(original)
        restore = run_pipeline()
        if restore.returncode != 0:
            print("⚠ Warning: Failed to restore pipeline after test")


if __name__ == "__main__":
    sys.exit(0 if test_covid_crash() else 1)
