#!/usr/bin/env python3
"""
fetch_peer_filings.py

Utility to monitor peer filings (EWBC, COLB, etc.) for earnings releases.
Queries SEC submissions API and prints the most recent 8-K (Item 2.02) and 10-Q filings
filed on/after a specified date. Designed to support the Oct 17, 2025 peer monitoring workflow.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from typing import Iterable, List, Tuple

import urllib.request

USER_AGENT = "CATYResearchBot/1.0 (nirvan@example.com)"


def fetch_submissions(cik: str) -> dict:
    """Fetch the submissions JSON for a given numeric CIK."""
    cik_numeric = cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_numeric}.json"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def extract_recent_filings(data: dict, forms: Iterable[str]) -> List[Tuple[str, str, str, str]]:
    """Return list of (accession, form, filing_date, report_date) for given forms."""
    recent = data["filings"]["recent"]
    output = []
    for acc, form, filing_date, report_date in zip(
        recent["accessionNumber"],
        recent["form"],
        recent["filingDate"],
        recent.get("reportDate", [""] * len(recent["accessionNumber"])),
    ):
        if form in forms:
            output.append((acc, form, filing_date, report_date))
    return output


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor peer SEC filings for earnings updates.")
    parser.add_argument(
        "--cutoff",
        type=lambda s: dt.datetime.strptime(s, "%Y-%m-%d").date(),
        default=dt.date(2025, 10, 1),
        help="Earliest filing date to report (default: 2025-10-01).",
    )
    parser.add_argument(
        "peers",
        nargs="+",
        help="Ticker or numeric CIK (default peer aliases available: EWBC, COLB).",
    )
    return parser.parse_args(argv)


ALIASES = {
    "EWBC": "1069157",  # East West Bancorp
    "COLB": "0887343",  # Columbia Banking System
}


def resolve_cik(identifier: str) -> str:
    """Accept either ticker alias or numeric CIK and return numeric string."""
    identifier = identifier.upper().strip()
    if identifier.isdigit():
        return identifier
    if identifier in ALIASES:
        return ALIASES[identifier]
    raise SystemExit(f"Unknown identifier '{identifier}'. Add to ALIASES in fetch_peer_filings.py.")


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    print("Peer Filing Monitor")
    print("===================")
    print(f"Cutoff date: {args.cutoff.isoformat()}")
    print()

    for peer in args.peers:
        cik = resolve_cik(peer)
        try:
            data = fetch_submissions(cik)
        except Exception as err:  # pragma: no cover - network errors bubble up
            print(f"[{peer}] ERROR fetching submissions: {err}")
            continue

        filings = extract_recent_filings(data, forms={"8-K", "10-Q"})
        print(f"[{peer}] Latest filings (>= {args.cutoff.isoformat()}):")
        any_printed = False
        for acc, form, filing_date, report_date in filings:
            filing_date_obj = dt.datetime.strptime(filing_date, "%Y-%m-%d").date()
            if filing_date_obj < args.cutoff:
                continue
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik):010d}/{acc.replace('-', '')}/{acc}-index.html"
            tags = []
            if form == "8-K":
                tags.append("earnings?")
            if report_date:
                tags.append(f"report date {report_date}")
            tag_str = f" ({', '.join(tags)})" if tags else ""
            print(f"  - {filing_date} | {form}{tag_str}")
            print(f"    {doc_url}")
            any_printed = True
        if not any_printed:
            print("  (no filings on/after cutoff)")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
