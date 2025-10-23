#!/usr/bin/env python3
"""
Extract product-level deposit metrics from CATY 10-Q filings.

The script downloads inline XBRL HTML, locates the "Interest-Earning Assets
and Interest-Bearing Liabilities" table, and captures average balances,
interest expense, and average rates for each deposit bucket. Results feed the
NIM bridge and deposit beta workflow so the deck can flip within hours of the
10-Q posting.

Usage:
    python3 scripts/extract_deposit_betas_q10.py --quarters 2025Q2 2025Q1 2024Q3

If --quarters is omitted the script defaults to the latest three 10-Q filings.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd
import requests
from io import BytesIO, StringIO

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "deposit_beta_history.json"

CIK_STR = "0000861842"
SEC_SUBMISSIONS_URL = f"https://data.sec.gov/submissions/CIK{CIK_STR}.json"
SEC_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"
USER_AGENT = "CATY Research Team (research@analysis.com)"
REQUEST_TIMEOUT = 45
SEC_RATE_LIMIT_SECONDS = 0.4  # < 10 requests per second as required


@dataclass
class FilingRef:
    quarter: str
    accession: str
    report_date: str
    filing_date: str
    primary_doc: str


class DepositExtractionError(RuntimeError):
    """Domain-specific exception for extraction failures."""


def load_sec_submissions() -> Dict[str, any]:
    resp = requests.get(
        SEC_SUBMISSIONS_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    time.sleep(SEC_RATE_LIMIT_SECONDS)
    return resp.json()


def derive_quarter_label(report_date: str) -> str:
    try:
        dt = datetime.strptime(report_date, "%Y-%m-%d")
    except ValueError as exc:
        raise DepositExtractionError(f"Unexpected report date format: {report_date}") from exc
    quarter = (dt.month - 1) // 3 + 1
    return f"{dt.year}Q{quarter}"


def build_filing_index(submissions: Dict[str, any]) -> Dict[str, FilingRef]:
    recent = submissions.get("filings", {}).get("recent")
    if not recent:
        raise DepositExtractionError("SEC submissions payload missing 'recent' section")

    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    report_dates = recent.get("reportDate", [])
    filing_dates = recent.get("filingDate", [])
    primary_docs = recent.get("primaryDocument", [])

    filing_index: Dict[str, FilingRef] = {}
    for form, acc, report, filed, doc in zip(
        forms, accessions, report_dates, filing_dates, primary_docs
    ):
        if form != "10-Q":
            continue
        quarter = derive_quarter_label(report)
        filing_index[quarter] = FilingRef(
            quarter=quarter,
            accession=acc,
            report_date=report,
            filing_date=filed,
            primary_doc=doc,
        )
    return filing_index


def default_quarters(filing_index: Dict[str, FilingRef], count: int = 3) -> List[str]:
    return [
        ref.quarter
        for ref in sorted(
            filing_index.values(),
            key=lambda ref: ref.report_date,
            reverse=True,
        )[:count]
    ]


def download_filing(ref: FilingRef) -> str:
    cik_numeric = str(int(CIK_STR))  # drop leading zeros
    accession_slug = ref.accession.replace("-", "")
    url = f"{SEC_ARCHIVES_BASE}/{cik_numeric}/{accession_slug}/{ref.primary_doc}"
    resp = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    time.sleep(SEC_RATE_LIMIT_SECONDS)
    return resp.text


TARGET_MATCH = "Interest-Earning Assets and Interest-Bearing Liabilities"


def locate_deposit_table(html: str) -> pd.DataFrame:
    try:
        tables = pd.read_html(StringIO(html), match=TARGET_MATCH)
    except ValueError as exc:
        raise DepositExtractionError("Deposit table not found (read_html failed)") from exc
    for df in tables:
        first_col = df.iloc[:, 0].astype(str)
        if first_col.str.contains("Interest-bearing demand", case=False).any():
            return df
    raise DepositExtractionError("Deposit table not found in filing")


def parse_float(value) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return float("nan")
    if isinstance(value, (int, float)):
        return float(value)
    cell_str = str(value).strip()
    if not cell_str or cell_str in {"-", "--"}:
        return float("nan")
    cleaned = (
        cell_str.replace("$", "")
        .replace(",", "")
        .replace("%", "")
        .replace("(", "-")
        .replace(")", "")
    )
    try:
        return float(cleaned)
    except ValueError:
        return float("nan")


def extract_deposit_metrics(table: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    metrics: Dict[str, Dict[str, float]] = {}

    def grab(label: str) -> Dict[str, float]:
        target_rows = table[table.iloc[:, 0].astype(str).str.strip() == label]
        if target_rows.empty:
            raise DepositExtractionError(f"Row '{label}' missing from deposit table")
        row = target_rows.iloc[0]
        current_balance = parse_float(row[3])
        current_interest = parse_float(row[7])
        current_rate = parse_float(row[11])
        dda_balance = parse_float(row[15])
        dda_interest = parse_float(row[19])
        dda_rate = parse_float(row[23])
        result = {
            "avg_balance_thousands": current_balance,
            "interest_expense_thousands": current_interest,
            "avg_rate_pct": current_rate,
            "prior_avg_balance_thousands": dda_balance,
            "prior_interest_expense_thousands": dda_interest,
            "prior_avg_rate_pct": dda_rate,
        }
        return result

    label_map = {
        "interest_bearing_demand": ["Interest-bearing demand accounts", "Interest-bearing demand deposits"],
        "money_market": ["Money market accounts", "Money market deposits"],
        "savings": ["Savings accounts", "Savings deposits"],
        "time_deposits": ["Time deposits"],
        "total_interest_bearing": ["Total interest-bearing deposits"],
    }

    for key, options in label_map.items():
        found = None
        for label in options:
            try:
                found = grab(label)
                break
            except DepositExtractionError:
                continue
        if found is None:
            raise DepositExtractionError(f"Could not find a row for {key} (tried {options})")
        metrics[key] = found

    demand_row = table[table.iloc[:, 0].astype(str).str.strip() == "Demand deposits"]
    if demand_row.empty:
        raise DepositExtractionError("Demand deposits row missing for DDA balances")
    metrics["noninterest_demand"] = {
        "avg_balance_thousands": parse_float(demand_row.iloc[0][3])
    }

    return metrics


def compute_all_in_metrics(metrics: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    total_ib_balance = metrics["total_interest_bearing"]["avg_balance_thousands"]
    total_ib_expense = metrics["total_interest_bearing"]["interest_expense_thousands"]
    ib_rate = metrics["total_interest_bearing"]["avg_rate_pct"]
    dda_balance = metrics["noninterest_demand"]["avg_balance_thousands"]

    all_in_balance = total_ib_balance + dda_balance
    if all_in_balance > 0:
        all_in_rate = (total_ib_expense / all_in_balance) * 100.0
        dda_mix_pct = (dda_balance / all_in_balance) * 100.0
    else:
        all_in_rate = 0.0
        dda_mix_pct = 0.0

    return {
        "interest_bearing_rate_pct": round(ib_rate, 3),
        "all_in_rate_pct": round(all_in_rate, 3),
        "dda_mix_pct": round(dda_mix_pct, 2),
    }


def build_history(
    quarters: List[str],
    filing_index: Dict[str, FilingRef],
) -> Dict[str, any]:
    history: List[Dict[str, any]] = []
    for quarter in quarters:
        if quarter not in filing_index:
            raise DepositExtractionError(f"No 10-Q filing located for {quarter}")
        ref = filing_index[quarter]
        html = download_filing(ref)
        deposit_table = locate_deposit_table(html)
        metrics = extract_deposit_metrics(deposit_table)
        derived = compute_all_in_metrics(metrics)

        history.append(
            {
                "quarter": ref.quarter,
                "report_date": ref.report_date,
                "filing_date": ref.filing_date,
                "accession": ref.accession,
                "primary_document": ref.primary_doc,
                "metrics": metrics,
                "derived": derived,
            }
        )

    history.sort(key=lambda entry: entry["report_date"])
    return {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "SEC inline XBRL 10-Q filings (auto-extracted)",
        "cik": CIK_STR,
        "quarters": history,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract deposit metrics from CATY 10-Q filings")
    parser.add_argument(
        "--quarters",
        nargs="+",
        help="Quarter labels (e.g., 2025Q2 2025Q1 2024Q3). Defaults to most recent three filings.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="Destination JSON path (default: data/deposit_beta_history.json)",
    )
    args = parser.parse_args()

    submissions = load_sec_submissions()
    filing_index = build_filing_index(submissions)

    if args.quarters:
        target_quarters = args.quarters
    else:
        target_quarters = default_quarters(filing_index, count=3)

    missing = [q for q in target_quarters if q not in filing_index]
    if missing:
        raise DepositExtractionError(f"Missing accessions for: {', '.join(missing)}")

    payload = build_history(target_quarters, filing_index)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2))
    print(f"Wrote deposit beta history to {args.output} ({len(payload['quarters'])} quarters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
