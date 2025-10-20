#!/usr/bin/env python3
"""
Fetch CATY Call Report data from the FDIC BankFind Suite API.

Outputs a normalized JSON payload at data/fdic_raw.json containing the latest
quarter of financial metrics used by downstream templates.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "fdic_raw.json"
FDIC_CERT = 23417
BANK_NAME = "CATHAY BANK"
USER_AGENT = "Claude Code Research caty-equity@example.com"
RATE_LIMIT_SECONDS = 0.2
REQUEST_TIMEOUT = 30

INSTITUTIONS_URL = "https://banks.data.fdic.gov/api/institutions"
FINANCIALS_URL = "https://banks.data.fdic.gov/api/financials"

FINANCIAL_FIELDS = [
    "ASSET",
    "DEP",
    "NTLNLSCOQR",
    "RIAD4074",
    "RIAD4230",
    "ROA",
    "EQTOT",
]


def _now_utc_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _get(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    logging.debug("GET %s params=%s", url, params)
    resp = requests.get(
        url,
        params=params,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
        timeout=REQUEST_TIMEOUT,
    )
    time.sleep(RATE_LIMIT_SECONDS)
    resp.raise_for_status()
    return resp.json()


def _parse_institution_record(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "cert": int(record["CERT"]),
        "name": record.get("NAME"),
        "city": record.get("CITY"),
        "state": record.get("STALP"),
    }


def fetch_institution() -> Dict[str, Any]:
    params = {
        "filters": f"CERT:{FDIC_CERT}",
        "fields": "CERT,NAME,CITY,STALP",
        "limit": 1,
        "format": "json",
        "download": "false",
        "filename": "data_file",
    }
    payload = _get(INSTITUTIONS_URL, params)
    records = payload.get("data", [])
    if records:
        record = records[0].get("data", records[0])
        return _parse_institution_record(record)

    logging.warning("CERT %s not found, falling back to name lookup", FDIC_CERT)
    params = {
        "filters": f"NAME:\"{BANK_NAME}\"",
        "fields": "CERT,NAME,CITY,STALP",
        "limit": 1,
        "format": "json",
        "download": "false",
        "filename": "data_file",
    }
    payload = _get(INSTITUTIONS_URL, params)
    records = payload.get("data", [])
    if not records:
        raise RuntimeError("FDIC institution lookup returned no results.")
    record = records[0].get("data", records[0])
    return _parse_institution_record(record)


def fetch_financials(cert: int, period: str | None) -> List[Dict[str, Any]]:
    filters = [f"CERT:{cert}"]
    if period:
        filters.append(f"REPDTE:{period}")
    params = {
        "filters": " AND ".join(filters),
        "fields": ",".join(["CERT", "REPDTE"] + FINANCIAL_FIELDS),
        "sort_by": "REPDTE",
        "sort_order": "DESC",
        "limit": 10,
        "offset": 0,
        "format": "json",
        "download": "false",
        "filename": "data_file",
    }
    payload = _get(FINANCIALS_URL, params)
    records = []
    for item in payload.get("data", []):
        data = item.get("data", item)
        records.append(data)
    return records


def normalize_quarters(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    quarters: List[Dict[str, Any]] = []
    for record in records:
        quarter: Dict[str, Any] = {
            "period": record.get("REPDTE"),
        }
        for field in FINANCIAL_FIELDS:
            if field in record:
                quarter[field] = record[field]
        quarters.append(quarter)
    return quarters


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        institution = fetch_institution()
        logging.info("FDIC CERT %s (%s)", institution["cert"], institution["name"])
        today = dt.date.today()
        target_period = today.strftime("%Y%m%d")
        financials = fetch_financials(institution["cert"], target_period)
        if not financials:
            logging.info("No financials for %s, falling back to latest available", target_period)
            financials = fetch_financials(institution["cert"], None)
        quarters = normalize_quarters(financials)
        payload = {
            "source": "FDIC Call Reports",
            "fetch_timestamp": _now_utc_iso(),
            "cert": institution["cert"],
            "name": institution["name"],
            "quarters": quarters,
        }
        write_json(OUTPUT_PATH, payload)
        logging.info("Wrote %s", OUTPUT_PATH.relative_to(ROOT))
        return 0
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to fetch FDIC data: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
