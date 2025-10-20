#!/usr/bin/env python3
"""
Transform peer_data_raw.json into the peer_snapshot_2025Q2.csv evidence file.

The CSV output mirrors the manually curated structure historically used for peer
regression analysis, but is now generated entirely from API-derived metrics.
"""

from __future__ import annotations

import csv
import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
PEER_DATA_PATH = ROOT / "data" / "peer_data_raw.json"
PRICE_DATA_PATH = ROOT / "data" / "peer_market_prices.json"
OUTPUT_PATH = ROOT / "evidence" / "peer_snapshot_2025Q2.csv"
BACKUP_PATH = OUTPUT_PATH.with_suffix(".csv.backup")

# Keep ticker ordering consistent with historical reporting.
PEER_ORDER = [
    "CATY",
    "EWBC",
    "CVBF",
    "HAFC",
    "HOPE",
    "COLB",
    "WAFD",
    "PPBI",
    "BANC",
]

CSV_FIELDS = [
    "Ticker",
    "Company",
    "Price_10_18_25",
    "TBVPS",
    "P_TBV",
    "ROTE_Pct",
    "CRE_Pct",
    "Mkt_Cap_M",
    "Source",
    "TBVPS_Citation",
    "ROTE_Citation",
    "CRE_Citation",
    "Notes",
]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _fmt(value: Any, decimals: int) -> str:
    if value is None:
        return ""
    return f"{value:.{decimals}f}"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not PEER_DATA_PATH.exists():
        logging.error("Peer dataset missing: %s", PEER_DATA_PATH)
        return 1

    peer_payload = _load_json(PEER_DATA_PATH)
    price_payload = _load_json(PRICE_DATA_PATH) if PRICE_DATA_PATH.exists() else {"prices": {}}

    period = peer_payload.get("period", "Unknown Period")
    banks: Dict[str, Dict[str, Any]] = peer_payload.get("banks", {})
    prices: Dict[str, float] = price_payload.get("prices", {})
    price_source = price_payload.get("source", "Manual input")
    price_date = price_payload.get("date", "Unknown")

    rows: List[Dict[str, str]] = []

    for ticker in PEER_ORDER:
        bank = banks.get(ticker)
        if not bank:
            logging.warning("Missing bank payload for %s; skipping", ticker)
            continue

        company = bank.get("company", ticker)
        price = prices.get(ticker)
        tbvps = bank.get("tbvps")
        rote = bank.get("rote_pct")
        cre_pct = bank.get("cre_pct")
        shares = bank.get("shares_outstanding_millions")

        p_tbv = price / tbvps if price is not None and tbvps else None
        market_cap = price * shares if price is not None and shares is not None else None

        source = f"{period} {bank.get('accession', 'SEC filing')}"
        tbvps_citation = "us-gaap:StockholdersEquity; Goodwill; IntangibleAssetsNetExcludingGoodwill; CommonStockSharesOutstanding"
        rote_citation = "us-gaap:NetIncomeLoss; Tangible equity derived from companyfacts"
        cre_citation = "Fallback ratio from prior peer snapshot (2025Q2) pending XBRL tagging"

        notes = ""
        if bank.get("cre_source") == "fallback_ratio":
            notes = "CRE% uses verified manual ratio until standardized tag adopted."

        rows.append(
            {
                "Ticker": ticker,
                "Company": company,
                "Price_10_18_25": _fmt(price, 2),
                "TBVPS": _fmt(tbvps, 2),
                "P_TBV": _fmt(p_tbv, 3),
                "ROTE_Pct": _fmt(rote, 2),
                "CRE_Pct": _fmt(cre_pct, 1),
                "Mkt_Cap_M": _fmt(market_cap, 1),
                "Source": source,
                "TBVPS_Citation": tbvps_citation,
                "ROTE_Citation": rote_citation,
                "CRE_Citation": cre_citation,
                "Notes": notes,
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT_PATH.exists():
        shutil.copyfile(OUTPUT_PATH, BACKUP_PATH)
        logging.info("Backed up existing snapshot to %s", BACKUP_PATH)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    logging.info(
        "Wrote %s rows to %s (prices as of %s, source: %s)",
        len(rows),
        OUTPUT_PATH,
        price_date,
        price_source,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
