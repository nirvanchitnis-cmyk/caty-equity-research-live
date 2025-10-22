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
from io import BytesIO

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


def locate_deposit_table(tables: Iterable[pd.DataFrame]) -> pd.DataFrame:
    for df in tables:
        try:
            first_col = df.iloc[:, 0].astype(str)
        except Exception:
            continue
        if (
            "Interest-earning assets:" in first_col.values
            and "Interest-bearing demand accounts" in first_col.values
            and "Total interest-bearing deposits" in first_col.values
        ):
            return df
    raise DepositExtractionError("Deposit table not found in filing")


def parse_numeric_sequence(row: pd.Series) -> List[float]:
    numbers: List[float] = []
    for cell in row[2:]:
        if cell is None or (isinstance(cell, float) and pd.isna(cell)):
            continue
        if isinstance(cell, (int, float)):
            numbers.append(float(cell))
            continue
        cell_str = str(cell).strip()
        if not cell_str or cell_str in {"-", "--"}:
            continue
        cleaned = (
            cell_str.replace("$", "")
            .replace(",", "")
            .replace("%", "")
            .replace("(", "-")
            .replace(")", "")
        )
        try:
            numbers.append(float(cleaned))
        except ValueError:
            continue
    return numbers


def extract_deposit_metrics(table: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    metrics: Dict[str, Dict[str, float]] = {}

    def grab(label: str, expect_interest: bool = True) -> Dict[str, float]:
        target_rows = table[table.iloc[:, 0] == label]
        if target_rows.empty:
            raise DepositExtractionError(f"Row '{label}' missing from deposit table")
        row = target_rows.iloc[0]
        values = parse_numeric_sequence(row)
        if expect_interest:
            if len(values) < 3:
                raise DepositExtractionError(f"Row '{label}' missing numeric triplet: {values}")
            avg_balance, interest_expense, avg_rate = values[:3]
            return {
                "avg_balance_thousands": avg_balance,
                "interest_expense_thousands": interest_expense,
                "avg_rate_pct": avg_rate,
            }
        if not values:
            raise DepositExtractionError(f"Row '{label}' missing numeric balance")
        return {"avg_balance_thousands": values[0]}

    metrics["interest_bearing_demand"] = grab("Interest-bearing demand accounts")
    metrics["money_market"] = grab("Money market accounts")
    metrics["savings"] = grab("Savings accounts")
    metrics["time_deposits"] = grab("Time deposits")
    metrics["total_interest_bearing"] = grab("Total interest-bearing deposits")
    metrics["noninterest_demand"] = grab("Demand deposits", expect_interest=False)

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
        tables = pd.read_html(BytesIO(html.encode("utf-8")), flavor="lxml")
        deposit_table = locate_deposit_table(tables)
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
