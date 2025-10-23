#!/usr/bin/env python3
"""Fetch latest closing prices for the CATY peer set via yfinance."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "peer_market_prices.json"

PEER_TICKERS = [
    "CATY",
    "EWBC",
    "CVBF",
    "HAFC",
    "HOPE",
    "COLB",
    "WAFD",
    "PPBI",
    "BANC",
    "OPBK",
]


def load_existing_prices() -> Dict[str, any]:
    if not OUTPUT_PATH.exists():
        return {}
    with OUTPUT_PATH.open("r", encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError:
            return {}


def fetch_close(ticker: str, fallback: Dict[str, any]) -> Tuple[float, str, bool]:
    history = yf.Ticker(ticker).history(period="5d")
    history = history.dropna(subset=["Close"])
    if history.empty:
        fallback_prices = fallback.get("prices", {}) if fallback else {}
        if ticker in fallback_prices:
            return float(fallback_prices[ticker]), fallback.get("date", ""), True
        raise RuntimeError(f"No pricing data returned for {ticker}")
    close_price = float(history["Close"].iloc[-1])
    price_date = history.index[-1].strftime("%Y-%m-%d")
    return close_price, price_date, False


def main() -> int:
    fallback_payload = load_existing_prices()
    closes: Dict[str, float] = {}
    price_dates: List[str] = []
    fallbacks_used: List[str] = []

    for ticker in PEER_TICKERS:
        price, date_str, used_fallback = fetch_close(ticker, fallback_payload)
        closes[ticker] = round(price, 2)
        price_dates.append(date_str)
        if used_fallback:
            fallbacks_used.append(ticker)

    price_date = max(price_dates)
    payload = {
        "date": price_date,
        "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "yfinance daily close (adjusted)",
        "tickers": PEER_TICKERS,
        "prices": closes,
    }
    if fallbacks_used:
        payload["fallback_prices"] = {
            "tickers": fallbacks_used,
            "note": "Retained last verified close where yfinance returned no recent data.",
            "previous_snapshot": fallback_payload.get("captured_at"),
        }

    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")

    print(f"Wrote peer prices for {len(PEER_TICKERS)} tickers to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
