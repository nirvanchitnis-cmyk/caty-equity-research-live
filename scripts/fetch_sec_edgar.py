#!/usr/bin/env python3
"""
Fetch the latest CATY 10-Q/10-K filing from SEC EDGAR and extract key XBRL facts.

Outputs a canonical JSON payload at data/sec_edgar_raw.json that captures the
raw fact values, metadata, and provenance needed by downstream merge scripts.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "sec_edgar_raw.json"
CIK = "0000861842"
SUBMISSIONS_URL = f"https://data.sec.gov/submissions/CIK{CIK}.json"
COMPANY_FACTS_URL = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json"
USER_AGENT = "Claude Code Research caty-equity@example.com"
RATE_LIMIT_SECONDS = 0.2
REQUEST_TIMEOUT = 30

TAG_MAP: Dict[str, str] = {
    # Income statement
    "InterestAndDividendIncomeOperating": "us-gaap:InterestAndDividendIncomeOperating",
    "InterestExpense": "us-gaap:InterestExpense",
    "InterestIncomeExpenseNet": "us-gaap:InterestIncomeExpenseNet",
    "ProvisionForLoanLossesExpensed": "us-gaap:ProvisionForLoanLossesExpensed",
    "NoninterestIncome": "us-gaap:NoninterestIncome",
    "NoninterestExpense": "us-gaap:NoninterestExpense",
    "IncomeTaxExpenseBenefit": "us-gaap:IncomeTaxExpenseBenefit",
    "NetIncomeLoss": "us-gaap:NetIncomeLoss",
    "EarningsPerShareDiluted": "us-gaap:EarningsPerShareDiluted",
    # Balance sheet
    "Assets": "us-gaap:Assets",
    "LoansAndLeasesReceivableNetOfDeferredIncome": "us-gaap:LoansAndLeasesReceivableNetOfDeferredIncome",
    "AllowanceForLoanAndLeaseLosses": "us-gaap:AllowanceForLoanAndLeaseLosses",
    "Deposits": "us-gaap:Deposits",
    "StockholdersEquity": "us-gaap:StockholdersEquity",
    "Goodwill": "us-gaap:Goodwill",
    "IntangibleAssetsNetExcludingGoodwill": "us-gaap:IntangibleAssetsNetExcludingGoodwill",
    "AccumulatedOtherComprehensiveIncomeLossNetOfTax": "us-gaap:AccumulatedOtherComprehensiveIncomeLossNetOfTax",
    "CommonStockSharesOutstanding": "us-gaap:CommonStockSharesOutstanding",
}


def _now_utc_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _http_get_json(url: str) -> Dict[str, Any]:
    logging.debug("GET %s", url)
    resp = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
        timeout=REQUEST_TIMEOUT,
    )
    time.sleep(RATE_LIMIT_SECONDS)
    resp.raise_for_status()
    return resp.json()


def find_recent_filings(limit: int = 2) -> list[Dict[str, Any]]:
    submissions = _http_get_json(SUBMISSIONS_URL)
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    primary_docs = recent.get("primaryDocument", [])

    filings: list[Dict[str, Any]] = []
    for form, accession, filing_date, report_date, primary_doc in zip(
        forms, accessions, filing_dates, report_dates, primary_docs
    ):
        if form not in {"10-Q", "10-K"}:
            continue
        filings.append(
            {
                "form_type": form,
                "accession": accession,
                "filing_date": filing_date,
                "period_end": report_date,
                "primary_document": primary_doc,
            }
        )
        if len(filings) >= limit:
            break

    if not filings:
        raise RuntimeError("No 10-Q or 10-K filings found in SEC submissions feed.")
    return filings


def load_company_facts() -> Dict[str, Any]:
    return _http_get_json(COMPANY_FACTS_URL)


def make_entry(unit: str, item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "unit": unit,
        "value": item.get("val"),
        "decimals": item.get("decimals"),
        "context_ref": item.get("contextRef"),
        "start": item.get("start"),
        "end": item.get("end"),
        "fy": item.get("fy"),
        "fp": item.get("fp"),
        "form": item.get("form"),
        "filed": item.get("filed"),
        "accn": item.get("accn"),
        "frame": item.get("frame"),
    }


def extract_fact(
    facts: Dict[str, Any],
    tag: str,
    accession: str,
    prior_accession: Optional[str],
    target_end: Optional[str],
    prefer_quarterly: bool = True,
) -> Optional[Dict[str, Any]]:
    try:
        namespace, fact_name = tag.split(":", 1)
    except ValueError:
        namespace, fact_name = "us-gaap", tag

    namespace_facts = facts.get(namespace, {})
    tag_facts = namespace_facts.get(fact_name)
    if not tag_facts:
        logging.warning("XBRL tag missing for %s", tag)
        return None

    current_entry: Optional[Dict[str, Any]] = None
    prior_entry: Optional[Dict[str, Any]] = None
    candidates: list[Dict[str, Any]] = []
    for unit, fact_items in tag_facts.get("units", {}).items():
        for item in fact_items:
            entry = make_entry(unit, item)
            if item.get("accn") == accession:
                candidates.append(entry)
            if prior_accession and item.get("accn") == prior_accession and prior_entry is None:
                prior_entry = entry

    if target_end:
        matching_end = [entry for entry in candidates if entry.get("end") == target_end]
        if matching_end:
            candidates = matching_end

    if not candidates:
        logging.warning("No fact entry for tag %s with accession %s", tag, accession)
        return None

    if prefer_quarterly:
        quarterly_candidates: list[Dict[str, Any]] = []
        for entry in candidates:
            start = entry.get("start")
            end = entry.get("end")
            if start and end:
                try:
                    start_dt = dt.datetime.fromisoformat(start)
                    end_dt = dt.datetime.fromisoformat(end)
                except ValueError:
                    continue
                days = (end_dt - start_dt).days
                if 80 <= days <= 100:
                    quarterly_candidates.append(entry)
        if quarterly_candidates:
            current_entry = quarterly_candidates[0]
        else:
            instant_candidates = [e for e in candidates if e.get("start") is None]
            if instant_candidates:
                current_entry = instant_candidates[0]
            else:
                candidates.sort(
                    key=lambda e: (
                        e.get("start") or "",
                        e.get("end") or "",
                    )
                )
                current_entry = candidates[0]
    else:
        current_entry = candidates[0]

    if current_entry is None:
        logging.warning("No suitable fact entry for tag %s with accession %s", tag, accession)
        return None

    if prior_entry:
        current_entry["prior"] = prior_entry

    return current_entry


def build_payload(
    latest_filing: Dict[str, Any],
    prior_filing: Optional[Dict[str, Any]],
    facts: Dict[str, Any],
) -> Dict[str, Any]:
    accession = latest_filing["accession"]
    prior_accession = prior_filing["accession"] if prior_filing else None
    data: Dict[str, Any] = {}
    missing_tags: list[str] = []
    for key, tag in TAG_MAP.items():
        fact = extract_fact(
            facts,
            tag,
            accession,
            prior_accession,
            latest_filing.get("period_end"),
            prefer_quarterly=True,
        )
        if fact is None:
            missing_tags.append(tag)
            continue
        data[key] = fact

    if missing_tags:
        logging.info("Missing %d tags: %s", len(missing_tags), ", ".join(sorted(missing_tags)))

    payload = {
        "source": "SEC EDGAR",
        "fetch_timestamp": _now_utc_iso(),
        "cik": CIK,
        "ticker": "CATY",
        "form_type": latest_filing["form_type"],
        "filing_date": latest_filing["filing_date"],
        "period_end": latest_filing["period_end"],
        "accession": accession,
        "primary_document": latest_filing.get("primary_document"),
        "data": data,
    }
    if prior_filing:
        payload["prior_accession"] = prior_filing["accession"]
        payload["prior_period_end"] = prior_filing.get("period_end")
    return payload


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
        filings = find_recent_filings(limit=2)
        latest_filing = filings[0]
        prior_filing = filings[1] if len(filings) > 1 else None
        logging.info(
            "Latest filing: %s accession=%s period_end=%s",
            latest_filing["form_type"],
            latest_filing["accession"],
            latest_filing["period_end"],
        )
        facts = load_company_facts()
        payload = build_payload(latest_filing, prior_filing, facts.get("facts", {}))
        write_json(OUTPUT_PATH, payload)
        logging.info("Wrote %s", OUTPUT_PATH.relative_to(ROOT))
        return 0
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to fetch SEC EDGAR data: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
