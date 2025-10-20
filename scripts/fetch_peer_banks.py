#!/usr/bin/env python3
"""
Fetch key financial metrics for CATY peer banks from the SEC EDGAR companyfacts API.

Outputs a consolidated payload at data/peer_data_raw.json that captures the latest
10-Q metrics required for peer regression analysis (TBVPS, ROTE, CRE exposure, etc.).

The script mirrors the CATY single-bank fetcher but iterates across the full peer set,
normalises amounts to millions, applies annualisation logic for ROTE, and falls back
to historical CRE ratios when the XBRL payload does not disclose a granular breakdown.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import requests

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "peer_data_raw.json"

USER_AGENT = "Claude Peer Analytics peer-fetcher@example.com"
RATE_LIMIT_SECONDS = 0.21
REQUEST_TIMEOUT = 30

# Canonical peer universe. Ticker ordering aligns with peer_snapshot CSV.
PEER_BANKS: Dict[str, Dict[str, str]] = {
    "CATY": {"cik": "0000861842", "name": "Cathay General Bancorp"},
    "EWBC": {"cik": "0001069157", "name": "East West Bancorp"},
    "CVBF": {"cik": "0000354647", "name": "CVB Financial Corp"},
    "HAFC": {"cik": "0001109242", "name": "Hanmi Financial Corp"},
    "HOPE": {"cik": "0001128361", "name": "Hope Bancorp"},
    "COLB": {"cik": "0000887343", "name": "Columbia Banking System"},
    "WAFD": {"cik": "0000936528", "name": "Washington Federal"},
    "PPBI": {"cik": "0001028918", "name": "Pacific Premier Bancorp"},
    "BANC": {"cik": "0001169770", "name": "Banc of California"},
}

# CRE disclosure is not consistently tagged across peers. Until a robust parser exists,
# fall back to the ratios previously verified in evidence/peer_snapshot_2025Q2.csv.
FALLBACK_CRE_RATIOS: Dict[str, float] = {
    "CATY": 52.4,
    "EWBC": 37.6,
    "CVBF": 78.9,
    "HAFC": 17.7,
    "HOPE": 58.1,
    "COLB": 52.1,
    "WAFD": 17.5,
    "PPBI": 17.5,
    "BANC": 18.0,
}


class PeerDataError(RuntimeError):
    """Domain-specific exception for peer fetching issues."""


def _now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _http_get_json(session: requests.Session, url: str) -> Dict[str, Any]:
    logging.debug("GET %s", url)
    resp = session.get(
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


def _clean_cik(cik: str) -> str:
    return str(cik).zfill(10)


@dataclass
class FilingInfo:
    accession: str
    period_end: str
    form_type: str


def _most_recent_10q(session: requests.Session, cik: str) -> FilingInfo:
    url = f"https://data.sec.gov/submissions/CIK{_clean_cik(cik)}.json"
    data = _http_get_json(session, url)
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    report_dates = recent.get("reportDate", [])

    for form, accession, report_date in zip(forms, accessions, report_dates):
        if form != "10-Q":
            continue
        if not accession:
            continue
        if not report_date:
            continue
        return FilingInfo(accession=accession, period_end=report_date, form_type=form)

    raise PeerDataError(f"No 10-Q filing found in SEC submissions feed for CIK {cik}")


def _load_company_facts(session: requests.Session, cik: str) -> Dict[str, Any]:
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{_clean_cik(cik)}.json"
    payload = _http_get_json(session, url)
    return payload.get("facts", {})


def _parse_number(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    try:
        return float(str(raw))
    except (TypeError, ValueError):
        return None


def _duration_days(start: Optional[str], end: Optional[str]) -> Optional[int]:
    if not start or not end:
        return None
    try:
        start_dt = dt.datetime.fromisoformat(start)
        end_dt = dt.datetime.fromisoformat(end)
    except ValueError:
        return None
    return (end_dt - start_dt).days


def _convert_amount(value: Optional[float], unit: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    unit_norm = (unit or "").lower()
    if unit_norm in {"usd", "usdollars"}:
        return value / 1_000_000
    if unit_norm in {"usdm", "usdmm", "usd-millions"}:
        return value
    if unit_norm in {"usdthousands", "usd-thousands"}:
        return value / 1_000
    if unit_norm in {"shares"}:
        return value / 1_000_000
    if unit_norm in {"sharesmillions", "sharesm"}:
        return value
    if abs(value) > 1_000_000_000:
        return value / 1_000_000
    return value


def _select_fact_entry(
    facts: Dict[str, Any],
    tag: str,
    accession: str,
    period_end: str,
    prefer_quarterly: bool = True,
) -> Optional[Dict[str, Any]]:
    namespace, fact_name = tag.split(":", 1) if ":" in tag else ("us-gaap", tag)
    tag_data = facts.get(namespace, {}).get(fact_name)
    if not tag_data:
        return None

    entries: list[Dict[str, Any]] = []
    for unit, items in tag_data.get("units", {}).items():
        for item in items:
            entry = {
                "value": _parse_number(item.get("val")),
                "start": item.get("start"),
                "end": item.get("end"),
                "accn": item.get("accn"),
                "form": item.get("form"),
                "fy": item.get("fy"),
                "fp": item.get("fp"),
                "unit": unit,
            }
            entries.append(entry)

    if not entries:
        return None

    def matches(entry: Dict[str, Any]) -> bool:
        if accession and entry.get("accn") != accession:
            return False
        if period_end and entry.get("end") != period_end:
            return False
        return True

    exact_entries = [e for e in entries if matches(e)]
    if not exact_entries and accession:
        exact_entries = [e for e in entries if e.get("accn") == accession]
    if not exact_entries and period_end:
        exact_entries = [e for e in entries if e.get("end") == period_end]
    if not exact_entries:
        exact_entries = [e for e in entries if e.get("form") in {"10-Q", "10-K"}]
    if not exact_entries:
        exact_entries = entries

    def sort_key(entry: Dict[str, Any]) -> tuple[int, int]:
        duration = _duration_days(entry.get("start"), entry.get("end"))
        if duration is None:
            duration = 365
        penalty = abs(duration - 90) if prefer_quarterly else 0
        end = entry.get("end")
        try:
            end_ord = dt.date.fromisoformat(end).toordinal() if end else 0
        except ValueError:
            end_ord = 0
        return (penalty, -end_ord)

    sorted_entries = sorted(exact_entries, key=sort_key)
    return sorted_entries[0] if sorted_entries else None


def _annualisation_factor(entry: Optional[Dict[str, Any]]) -> float:
    if not entry:
        return 4.0
    duration = _duration_days(entry.get("start"), entry.get("end"))
    if duration is None:
        return 4.0
    if 80 <= duration <= 100:
        return 4.0
    if 350 <= duration <= 370:
        return 1.0
    return max(1.0, round(360.0 / max(duration, 1)))


def _infer_period_label(period_end: str) -> str:
    try:
        end_dt = dt.date.fromisoformat(period_end)
    except ValueError:
        return period_end
    quarter = ((end_dt.month - 1) // 3) + 1
    return f"Q{quarter} {end_dt.year}"


def _compute_peer_metrics(
    facts: Dict[str, Any],
    filing: FilingInfo,
    ticker: str,
) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {
        "accession": filing.accession,
        "period_end": filing.period_end,
    }

    def grab(tag: str, prefer_quarterly: bool = True):
        entry = _select_fact_entry(facts, tag, filing.accession, filing.period_end, prefer_quarterly)
        if not entry:
            logging.warning("Tag %s missing for %s (%s)", tag, ticker, filing.accession)
            return None, None, None
        value = _convert_amount(entry.get("value"), entry.get("unit"))
        return value, entry.get("unit"), entry
    def grab_any(tags: list[str], prefer_quarterly: bool = True):
        for tag in tags:
            value, unit, entry = grab(tag, prefer_quarterly)
            if value is not None:
                return value, unit, entry
        return None, None, None



    equity, _, _ = grab_any(
        [
            "us-gaap:StockholdersEquity",
            "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            "us-gaap:StockholdersEquityIncludingPortionAttributableToParent",
        ],
        prefer_quarterly=False,
    )
    goodwill, _, _ = grab_any(
        [
            "us-gaap:Goodwill",
            "us-gaap:GoodwillAndIntangibleAssetsNet",
        ],
        prefer_quarterly=False,
    )
    intangibles, _, _ = grab_any(
        [
            "us-gaap:IntangibleAssetsNetExcludingGoodwill",
            "us-gaap:IntangibleAssetsNet",
            "us-gaap:FiniteLivedIntangibleAssetsNet",
        ],
        prefer_quarterly=False,
    )
    shares, shares_unit, _ = grab_any(
        [
            "us-gaap:CommonStockSharesOutstanding",
            "us-gaap:CommonStockSharesIssued",
        ],
        prefer_quarterly=False,
    )
    net_income, _, net_income_entry = grab_any(
        [
            "us-gaap:NetIncomeLoss",
            "us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic",
            "us-gaap:NetIncomeLossAvailableToCommonStockholdersDiluted",
        ],
    )
    total_loans, _, _ = grab_any(
        [
            "us-gaap:LoansAndLeasesReceivableNetOfDeferredIncome",
            "us-gaap:FinancingReceivableExcludingAccruedInterestBeforeAllowanceForCreditLossFeeAndLoanInProcess",
            "us-gaap:LoansAndLeasesReceivableNetReportedAmount",
            "us-gaap:LoansReceivableNet",
            "us-gaap:LoansAndLeasesReceivableGrossCarryingAmount",
            "us-gaap:NotesAndLoansReceivableGrossCurrent",
            "us-gaap:NotesAndLoansReceivableGrossNoncurrent",
            "us-gaap:DisposalGroupIncludingDiscontinuedOperationAccountsNotesAndLoansReceivableNet",
        ],
        prefer_quarterly=False,
    )

    if equity is None or shares is None or net_income is None or total_loans is None:
        raise PeerDataError(f"Missing core metrics for {ticker} ({filing.accession})")

    goodwill = goodwill or 0.0
    intangibles = intangibles or 0.0

    tangible_equity = max(equity - goodwill - intangibles, 0.0)
    tbvps = tangible_equity / shares if shares else None

    annualisation_factor = _annualisation_factor(net_income_entry)
    rote_pct = (net_income * annualisation_factor) / tangible_equity * 100 if tangible_equity else None

    fallback_cre_pct = FALLBACK_CRE_RATIOS.get(ticker)
    cre_pct = fallback_cre_pct
    cre_loans = total_loans * cre_pct / 100 if (cre_pct is not None and total_loans is not None) else None

    metrics.update(
        {
            "equity_millions": round(equity, 2) if equity is not None else None,
            "goodwill_millions": round(goodwill, 2) if goodwill is not None else 0.0,
            "intangibles_millions": round(intangibles, 2) if intangibles is not None else 0.0,
            "shares_outstanding_millions": round(shares, 3) if shares is not None else None,
            "net_income_millions": round(net_income, 2) if net_income is not None else None,
            "tangible_equity_millions": round(tangible_equity, 2) if tangible_equity is not None else None,
            "tbvps": round(tbvps, 2) if tbvps is not None else None,
            "rote_pct": round(rote_pct, 2) if rote_pct is not None else None,
            "total_loans_millions": round(total_loans, 2) if total_loans is not None else None,
            "cre_loans_millions": round(cre_loans, 2) if cre_loans is not None else None,
            "cre_pct": round(cre_pct, 1) if cre_pct is not None else None,
            "shares_unit": shares_unit,
            "net_income_annualisation_factor": annualisation_factor,
            "cre_source": "fallback_ratio" if fallback_cre_pct is not None else "missing",
        }
    )

    return metrics


def fetch_all_peers() -> Dict[str, Any]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
    )

    results: Dict[str, Any] = {}
    period_label: Optional[str] = None

    for ticker, meta in PEER_BANKS.items():
        cik = meta["cik"]
        logging.info("Fetching peer %s (%s)", ticker, cik)
        try:
            filing = _most_recent_10q(session, cik)
            facts = _load_company_facts(session, cik)
            metrics = _compute_peer_metrics(facts, filing, ticker)
        except Exception as exc:
            logging.exception("Failed to process %s (%s): %s", ticker, cik, exc)
            raise

        metrics["cik"] = _clean_cik(cik)
        metrics["company"] = meta["name"]
        results[ticker] = metrics

        if not period_label:
            period_label = _infer_period_label(filing.period_end)

    return {
        "fetch_timestamp": _now_iso(),
        "period": period_label or "Unknown",
        "banks": results,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        payload = fetch_all_peers()
    except Exception as exc:
        logging.error("Peer fetch failed: %s", exc)
        return 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")

    logging.info("Wrote peer dataset to %s (%s banks)", OUTPUT_PATH, len(payload["banks"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
