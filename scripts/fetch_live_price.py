#!/usr/bin/env python3
"""Fetch the latest CATY close price from Yahoo Finance and update market data."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "market_data_current.json"


def fetch_latest_price() -> tuple[float, str]:
    """Return the most recent close price and corresponding date string."""
    ticker = yf.Ticker("CATY")
    data = ticker.history(period="1d")
    if data.empty:
        raise RuntimeError("No price data returned from Yahoo Finance")
    close_price = float(data["Close"].iloc[-1])
    price_date = data.index[-1].strftime("%Y-%m-%d")
    return close_price, price_date


def update_market_data(price: float, price_date: str) -> None:
    """Update market_data_current.json with the latest price information."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Market data file missing: {DATA_PATH}")

    with DATA_PATH.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    payload["price"] = round(price, 2)
    payload["price_date"] = price_date
    now_utc = datetime.now(tz=timezone.utc).replace(microsecond=0)
    payload["report_generated"] = now_utc.isoformat().replace("+00:00", "Z")

    price_dt = datetime.strptime(price_date, "%Y-%m-%d").date()
    payload["data_source"] = f"NASDAQ closing price ({price_dt.strftime('%A, %b %d, %Y')})"

    metadata = payload.setdefault("metadata", {})
    metadata["update_method"] = "yfinance API"
    metadata["last_trading_day"] = price_date
    metadata["market_status"] = "closed"

    next_trading_day = price_dt + timedelta(days=1)
    while next_trading_day.weekday() >= 5:
        next_trading_day += timedelta(days=1)
    metadata["next_trading_day"] = next_trading_day.isoformat()

    metrics = payload.setdefault("calculated_metrics", {})
    tbvps = metrics.get("tbvps")
    if tbvps in (None, 0):
        raise RuntimeError("TBVPS value missing; cannot compute current_ptbv")
    metrics["current_ptbv"] = round(price / tbvps, 3)

    target_return_fields = {
        "target_regression": "return_regression_pct",
        "target_normalized": "return_normalized_pct",
        "target_wilson_95": "return_wilson_95_pct",
        "target_irc_blended": "return_irc_blended_pct",
    }
    for target_key, return_key in target_return_fields.items():
        target_value = metrics.get(target_key)
        if target_value is None:
            continue
        return_pct = (target_value - price) / price * 100
        metrics[return_key] = round(return_pct, 1)

    report_meta = payload.setdefault("report_metadata", {})
    report_meta["last_updated_utc"] = now_utc.isoformat().replace("+00:00", "Z")
    report_meta["generated_at_display"] = now_utc.strftime("%B %d, %Y %H:%M UTC")

    with DATA_PATH.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")


def main() -> int:
    try:
        price, price_date = fetch_latest_price()
        update_market_data(price, price_date)
        print(f"✅ Updated CATY price: ${price:.2f} ({price_date})")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Failed to update CATY price: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
