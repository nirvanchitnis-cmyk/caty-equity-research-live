#!/usr/bin/env python3
"""
Minimal DEF 14A parser extracting board size, CEO name, and auditor.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning  # type: ignore
from jsonschema import Draft7Validator  # type: ignore

import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BOARD_SIZE_REGEXES: List[Tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"board(?: of directors)?(?: currently)? (?:consists?|comprises|is composed of)\s+(?:of\s+)?(\d+)\s+directors?",
            re.IGNORECASE,
        ),
        "regex: board ... consists of (\\d+) directors",
    ),
    (
        re.compile(
            r"(\d+)\s+directors?\s+(?:serve|serving|stand|served).{0,40}?board",
            re.IGNORECASE,
        ),
        "regex: (\\d+) directors ... board",
    ),
    (
        re.compile(
            r"our board has\s+(\d+)\s+(?:members|directors)",
            re.IGNORECASE,
        ),
        "regex: our board has (\\d+)",
    ),
    (
        re.compile(
            r"board has nominated\s+(\d+)\s+individuals",
            re.IGNORECASE,
        ),
        "regex: board has nominated (\\d+) individuals",
    ),
    (
        re.compile(
            r"elect\s+[a-z\s]*\((\d+)\)\s+directors",
            re.IGNORECASE,
        ),
        "regex: elect (\\d+) directors (parenthetical)",
    ),
    (
        re.compile(
            r"elect\s+(\d+)\s+directors",
            re.IGNORECASE,
        ),
        "regex: elect (\\d+) directors",
    ),
    (
        re.compile(
            r"elect\s+[a-z\s]*\((\d+)\)\s+persons?\s+to\s+the\s+board",
            re.IGNORECASE,
        ),
        "regex: elect (\\d+) persons to the board",
    ),
]

AUDITOR_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r"kpmg(?:\s+llp)?", re.IGNORECASE), "KPMG LLP"),
    (re.compile(r"deloitte(?:\s+&\s+touche)?(?:\s+llp)?", re.IGNORECASE), "Deloitte & Touche LLP"),
    (re.compile(r"pricewaterhousecoopers(?:\s+llp)?", re.IGNORECASE), "PricewaterhouseCoopers LLP"),
    (re.compile(r"\bpwc\b", re.IGNORECASE), "PwC"),
    (re.compile(r"ernst\s*&\s*young(?:\s+llp)?", re.IGNORECASE), "Ernst & Young LLP"),
    (re.compile(r"\bey\b", re.IGNORECASE), "EY"),
    (re.compile(r"crowe(?:\s+llp)?", re.IGNORECASE), "Crowe LLP"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract minimal governance facts from a DEF 14A HTML filing."
    )
    parser.add_argument("--ticker", required=True, help="Ticker symbol (e.g., CATY)")
    parser.add_argument(
        "--html",
        required=True,
        help="Path or glob to DEF 14A HTML document",
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to manifest_def14a.json",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Destination JSON output file",
    )
    parser.add_argument(
        "--schema",
        default="schemas/def14a.schema.json",
        help="Path to DEF14A JSON schema file",
    )
    return parser.parse_args()


def resolve_html_path(pattern: str) -> Path:
    matches = sorted(glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No HTML files matched pattern: {pattern}")
    if len(matches) > 1:
        print(f"NOTE: multiple HTML matches, using {matches[0]}", file=sys.stderr)
    return Path(matches[0]).resolve()


def load_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def get_manifest_entry(manifest: Dict[str, Any], ticker: str) -> Dict[str, Any]:
    http_prov = manifest.get("http_provenance", {})
    entry = http_prov.get(ticker.upper())
    if not entry:
        raise KeyError(f"Ticker {ticker} not present in manifest http_provenance.")
    return entry


def load_soup(html_path: Path) -> BeautifulSoup:
    html_text = html_path.read_text(encoding="utf-8", errors="ignore")
    return BeautifulSoup(html_text, "lxml")


def find_ix_value(soup: BeautifulSoup, key: str) -> Optional[str]:
    tag = soup.find(attrs={"name": key})
    if tag:
        text = tag.get_text(" ", strip=True)
        return text or None
    return None


def parse_cik_from_url(url: str) -> Optional[str]:
    match = re.search(r"/data/(\d+)/", url)
    if not match:
        return None
    digits = match.group(1)
    if not digits:
        return None
    return digits.zfill(10)


def make_snippet(text: str, start: int, end: int, radius: int = 120) -> str:
    lo = max(0, start - radius)
    hi = min(len(text), end + radius)
    snippet = text[lo:hi].strip()
    snippet = re.sub(r"\s+", " ", snippet)
    return snippet[:500]


def extract_board_size(text: str, soup: BeautifulSoup) -> Tuple[int, int, str, List[str], str]:
    for pattern, locator in BOARD_SIZE_REGEXES:
        match = pattern.search(text)
        if match:
            size = int(match.group(1))
            snippet = make_snippet(text, match.start(), match.end())
            return size, 90, "regex", [locator], snippet

    independent_hits: List[str] = []
    for paragraph in soup.find_all("p"):
        if paragraph.find("b", string=re.compile("Independent Director", re.IGNORECASE)):
            independent_hits.append(paragraph.get_text(" ", strip=True))
    count = len(independent_hits)
    if count > 0:
        snippet = independent_hits[0][:500]
        return count, 70, "html_parse", ["count: <p><b>Independent Director</b>"], snippet

    raise ValueError("Board size not found via regex or fallback heuristics.")


def extract_ceo_name(soup: BeautifulSoup) -> Tuple[str, int, str, List[str], str]:
    summary_table = None
    for table in soup.find_all("table"):
        header_rows = table.find_all("tr", limit=8)
        header_text = " ".join(
            cell.get_text(" ", strip=True).lower()
            for row in header_rows
            for cell in row.find_all(["td", "th"])
        )
        if "name and principal" in header_text and "salary" in header_text:
            summary_table = table
            break

    if summary_table is None:
        raise ValueError("Summary Compensation Table not located.")

    for require_bold in (True, False):
        for row in summary_table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            first_cell_tag = cells[0]
            first_cell_text = first_cell_tag.get_text(" ", strip=True)
            if not first_cell_text:
                continue
            if first_cell_text.strip().lower().startswith("name"):
                continue
            bold = first_cell_tag.find("b")
            if require_bold and (not bold or not bold.get_text(" ", strip=True)):
                continue
            if bold and bold.get_text(" ", strip=True):
                ceo_name = " ".join(bold.get_text(" ", strip=True).split())
            else:
                first_item = next(first_cell_tag.stripped_strings, "")
                ceo_name = " ".join(first_item.split())
            if not ceo_name:
                continue
            normalized = ceo_name.strip().lower()
            if normalized.startswith("(") or normalized in {"position", "year"}:
                continue
            snippet = row.get_text(" ", strip=True)[:500]
            return (
                ceo_name,
                95,
                "html_parse",
                ["table header: Name and Principal Position"],
                snippet,
            )

    raise ValueError("Unable to extract CEO name from Summary Compensation Table.")


def extract_auditor(text: str) -> Tuple[str, int, str, List[str], str]:
    lower_text = text.lower()
    for pattern, canonical in AUDITOR_PATTERNS:
        for match in pattern.finditer(lower_text):
            start, end = match.span()
            snippet = make_snippet(text, start, end)
            context = lower_text[max(0, start - 120) : min(len(lower_text), end + 120)]
            if "independent registered public accounting firm" in context or "independent auditor" in context or "independent auditors" in context:
                return canonical, 90, "regex", [f"text contains: {pattern.pattern}"], snippet
    raise ValueError("Auditor not identified in filing text.")


def build_company_info(
    soup: BeautifulSoup, ticker: str, manifest_entry: Dict[str, Any]
) -> Dict[str, Any]:
    name = find_ix_value(soup, "dei:EntityRegistrantName")
    cik = find_ix_value(soup, "dei:EntityCentralIndexKey")
    if not cik:
        cik = parse_cik_from_url(manifest_entry.get("def14a_url", "")) or ""
    cik = cik.zfill(10) if cik else ""
    if not cik:
        raise ValueError("Unable to determine company CIK.")
    company_name = " ".join((name or ticker.upper()).split())
    return {
        "name": company_name,
        "ticker": ticker.upper(),
        "cik": cik,
    }


def build_filing_info(manifest_entry: Dict[str, Any], cik: str) -> Dict[str, Any]:
    accession = manifest_entry.get("accession_number", "")
    filing_date = manifest_entry.get("filing_date")
    primary_doc_url = manifest_entry.get("def14a_url")
    if not accession or not filing_date or not primary_doc_url:
        raise ValueError("Manifest entry missing required filing metadata.")
    accession_clean = accession.replace("-", "")
    cik_numeric = str(int(cik)) if cik else ""
    index_url = (
        f"https://www.sec.gov/Archives/edgar/data/{cik_numeric}/{accession_clean}/{accession}-index.htm"
        if cik_numeric and accession_clean
        else primary_doc_url
    )
    return {
        "form": "DEF 14A",
        "accession_number": accession,
        "filing_date": filing_date,
        "edgar_urls": {
            "index": index_url,
            "primary_doc": primary_doc_url,
        },
    }


def build_output_skeleton() -> Dict[str, Any]:
    return {
        "version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "company": {},
        "filing": {},
        "board": {},
        "ownership": {
            "top_holders": [],
            "top5_pct": 0.0,
            "insider_pct": 0.0,
            "policies": {},
        },
        "compensation": {
            "pay_mix_pct": {},
            "neos": [],
            "annual_incentive": {},
            "ltip": {},
            "say_on_pay_pct": None,
        },
        "equity_plan": {
            "overhang_pct": None,
            "burn_rate_pct": None,
            "shares_available": None,
            "shares_outstanding_awards": None,
            "plan_name": None,
        },
        "audit": {
            "auditor": "",
            "fees": {},
        },
        "provenance": [],
    }


def validate_output(schema_path: Path, payload: Dict[str, Any]) -> None:
    with schema_path.open("r", encoding="utf-8") as fh:
        schema = json.load(fh)
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    if errors:
        for err in errors:
            location = ".".join(str(p) for p in err.path)
            print(f"Validation error at {location or '<root>'}: {err.message}", file=sys.stderr)
        raise ValueError("JSON schema validation failed.")


def main() -> None:
    args = parse_args()
    try:
        html_path = resolve_html_path(args.html)
        manifest_path = Path(args.manifest).resolve()
        output_path = Path(args.output).resolve()
        schema_path = Path(args.schema).resolve()

        manifest = load_manifest(manifest_path)
        manifest_entry = get_manifest_entry(manifest, args.ticker)
        soup = load_soup(html_path)
        text = soup.get_text(" ", strip=True)

        board_size, board_conf, board_method, board_locators, board_snippet = extract_board_size(text, soup)
        ceo_name, ceo_conf, ceo_method, ceo_locators, ceo_snippet = extract_ceo_name(soup)
        auditor_name, auditor_conf, auditor_method, auditor_locators, auditor_snippet = extract_auditor(text)

        company_info = build_company_info(soup, args.ticker, manifest_entry)
        filing_info = build_filing_info(manifest_entry, company_info["cik"])

        payload = build_output_skeleton()
        payload["company"] = company_info
        payload["filing"] = filing_info
        payload["board"] = {
            "size": board_size,
            "independent_count": board_size,
            "leadership": {
                "chair_is_independent": False,
                "ceo_is_chair": False,
            },
        }
        payload["compensation"]["neos"] = [
            {"role": "CEO", "name": ceo_name, "total_comp_usd": None}
        ]
        payload["audit"]["auditor"] = auditor_name
        payload["provenance"] = [
            {
                "section": "board.size",
                "method": board_method,
                "locators": board_locators,
                "page_range": None,
                "text_snippet": board_snippet,
                "confidence_pct": board_conf,
                "source_url": manifest_entry.get("def14a_url"),
                "sha256": manifest_entry.get("sha256"),
            },
            {
                "section": "compensation.neos[0].name",
                "method": ceo_method,
                "locators": ceo_locators,
                "page_range": None,
                "text_snippet": ceo_snippet,
                "confidence_pct": ceo_conf,
                "source_url": manifest_entry.get("def14a_url"),
                "sha256": manifest_entry.get("sha256"),
            },
            {
                "section": "audit.auditor",
                "method": auditor_method,
                "locators": auditor_locators,
                "page_range": None,
                "text_snippet": auditor_snippet,
                "confidence_pct": auditor_conf,
                "source_url": manifest_entry.get("def14a_url"),
                "sha256": manifest_entry.get("sha256"),
            },
        ]

        validate_output(schema_path, payload)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

    except Exception as exc:  # pylint: disable=broad-except
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
