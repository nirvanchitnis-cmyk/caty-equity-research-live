#!/usr/bin/env python3
"""
Simple DEF 14A parser (Phase 1) extracting core governance facts.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning  # type: ignore
from jsonschema import Draft7Validator  # type: ignore

import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

AUDITOR_KEYWORDS = [
    "kpmg",
    "deloitte",
    "pricewaterhousecoopers",
    "pwc",
    "ernst & young",
    "ey",
    "grant thornton",
    "crowe",
    "rsm us",
    "bdo",
    "cliftonlarsonallen",
    "moss adams",
    "bkd",
    "forvis",
    "marcum",
]

BOARD_SIZE_PATTERNS = [
    re.compile(
        r"board(?: of directors)? (?:consists|currently consists|currently has|comprises|is composed of)\s+(?:of\s+)?(\d+)\s+director",
        re.IGNORECASE,
    ),
    re.compile(r"our board has\s+(\d+)\s+(?:members|directors)", re.IGNORECASE),
    re.compile(
        r"There (?:are|were)\s+(\d+)\s+directors? (?:serving|standing) (?:on|for)\s+the board",
        re.IGNORECASE,
    ),
]

INDEPENDENT_PATTERNS = [
    re.compile(r"(\d+)\s+independent directors?", re.IGNORECASE),
    re.compile(r"(\d+)\s+of whom are independent", re.IGNORECASE),
    re.compile(r"(\d+)\s+are independent directors?", re.IGNORECASE),
    re.compile(r"(\d+)\s+are independent", re.IGNORECASE),
]



NUMBER_WORDS = {
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
    'eleven': 11,
    'twelve': 12,
}


SAY_ON_PAY_REGEX = re.compile(
    r"(\d{1,3}(?:\.\d+)?)%\s+[^%]{0,120}?(?:vote|votes|voted)[^%]{0,60}?(?:for|in favor)",
    re.IGNORECASE,
)

CURRENCY_CLEAN_RE = re.compile(r"[^0-9().\-]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract core governance facts from a DEF14A HTML filing."
    )
    parser.add_argument("--ticker", required=True, help="Ticker symbol (e.g., CATY)")
    parser.add_argument(
        "--html",
        required=True,
        help="Path or glob to DEF14A HTML document",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Destination JSON output file",
    )
    parser.add_argument(
        "--schema",
        default="schemas/def14a.schema.json",
        help="Path to DEF14A JSON schema",
    )
    return parser.parse_args()


def resolve_html_path(pattern: str) -> Path:
    matches = sorted(glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No HTML files matched pattern: {pattern}")
    if len(matches) > 1:
        print(f"NOTE: multiple HTML matches, using {matches[0]}", file=sys.stderr)
    return Path(matches[0]).resolve()


def load_manifest(run_dir: Path) -> Dict[str, Any]:
    manifest_path = run_dir / "manifest_def14a.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def load_soup(html_path: Path) -> BeautifulSoup:
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    return BeautifulSoup(html, "lxml")


def find_ix_value(soup: BeautifulSoup, key: str) -> Optional[str]:
    tag = soup.find(attrs={"name": key})
    if tag:
        text = tag.get_text(" ", strip=True)
        return text or None
    return None


def parse_cik(def14a_url: str) -> Optional[str]:
    match = re.search(r"/data/(\d+)/", def14a_url)
    if not match:
        return None
    digits = match.group(1).lstrip("0")
    return match.group(1).zfill(10) if digits else "0000000000"


def build_company_info(
    soup: BeautifulSoup, ticker: str, manifest_entry: Dict[str, Any]
) -> Dict[str, Any]:
    name = find_ix_value(soup, "dei:EntityRegistrantName") or ticker.upper()
    cik = (
        find_ix_value(soup, "dei:EntityCentralIndexKey")
        or parse_cik(manifest_entry.get("def14a_url", ""))
        or ""
    )
    cik = cik.zfill(10) if cik else ""
    if not cik:
        raise ValueError("Unable to determine company CIK.")
    company: Dict[str, Any] = {
        "name": " ".join(name.split()),
        "ticker": ticker.upper(),
        "cik": cik,
    }
    fiscal_end = find_ix_value(soup, "dei:DocumentFiscalYearFocus")
    if fiscal_end and re.match(r"\d{4}", fiscal_end):
        company["fiscal_year_end"] = f"{fiscal_end[:4]}-12-31"
    return company


def build_filing_info(
    manifest_entry: Dict[str, Any], company: Dict[str, Any]
) -> Dict[str, Any]:
    accession = manifest_entry.get("accession_number")
    filing_date = manifest_entry.get("filing_date")
    def14a_url = manifest_entry.get("def14a_url")
    if not accession or not filing_date or not def14a_url:
        raise ValueError("Manifest entry missing filing metadata.")
    cik = int(company["cik"])
    accession_nodash = accession.replace("-", "")
    index_url = (
        f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_nodash}/{accession}-index.html"
    )
    return {
        "form": "DEF 14A",
        "accession_number": accession,
        "filing_date": filing_date,
        "edgar_urls": {
            "index": index_url,
            "primary_doc": def14a_url,
            "pdf_fallback": None,
        },
        "is_scanned_pdf": False,
        "meeting_date": None,
        "meeting_type": None,
        "period_of_report": None,
    }


def split_sentences(text: str) -> List[str]:
    bits = re.split(r"(?<=[\.\!\?])\s+", text)
    return [b.strip() for b in bits if b.strip()]


def make_snippet(text: str, start: int, end: int, radius: int = 120) -> str:
    return text[max(0, start - radius) : min(len(text), end + radius)].strip()


def extract_board_info(soup: BeautifulSoup, text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    board: Dict[str, Any] = {}
    provenance: List[Dict[str, Any]] = []
    sentences = split_sentences(text)

    for sentence in sentences:
        if "director" not in sentence.lower():
            continue
        for pattern in BOARD_SIZE_PATTERNS:
            match = pattern.search(sentence)
            if match:
                size = int(match.group(1))
                board["size"] = size
                confidence = (
                    90
                    if re.search(
                        r"board of directors|director nominees|corporate governance",
                        sentence,
                        re.IGNORECASE,
                    )
                    else 70
                )
                provenance.append(
                    {
                        "section": "board.size",
                        "method": "regex",
                        "locators": [f"regex: {pattern.pattern}"],
                        "page_range": None,
                        "text_snippet": sentence.strip(),
                        "confidence_pct": confidence,
                    }
                )
                break
        if "independent" in sentence.lower() and "board" in sentence.lower():
            for pattern in INDEPENDENT_PATTERNS:
                match = pattern.search(sentence)
                if match:
                    independent = int(match.group(1))
                    board["independent_count"] = independent
                    confidence = (
                        90
                        if "independent directors" in sentence.lower()
                        else 70
                    )
                    provenance.append(
                        {
                            "section": "board.independent_count",
                            "method": "regex",
                            "locators": [f"regex: {pattern.pattern}"],
                            "page_range": None,
                            "text_snippet": sentence.strip(),
                            "confidence_pct": confidence,
                        }
                    )
                    break
        if "size" in board and "independent_count" in board:
            break

    if "size" not in board:
        match = re.search(r"elect\s+(\d+)\s+directors\s+to serve", text, re.IGNORECASE)
        if match:
            board["size"] = int(match.group(1))
            snippet = make_snippet(text, match.start(), match.end())
            provenance.append(
                {
                    "section": "board.size",
                    "method": "regex",
                    "locators": ["regex: elect N directors to serve"],
                    "page_range": None,
                    "text_snippet": snippet,
                    "confidence_pct": 60,
                }
            )
    if "size" not in board:
        matrix_cell = soup.find(string=re.compile("Total Number of Directors", re.IGNORECASE))
        if matrix_cell:
            row = matrix_cell.find_parent("tr")
            if row:
                numbers = re.findall(r"\d+", row.get_text(" ", strip=True))
                if numbers:
                    board["size"] = int(numbers[-1])
                    provenance.append(
                        {
                            "section": "board.size",
                            "method": "html_parse",
                            "locators": ["table: Board Diversity Matrix"],
                            "page_range": None,
                            "text_snippet": row.get_text(" ", strip=True),
                            "confidence_pct": 70,
                        }
                    )
    if "independent_count" not in board:
        mix_match = re.search(
            r"((?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve))\s+of the\s+((?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve))\s+directors[^.]{0,160}independent",
            text,
            re.IGNORECASE,
        )
        if mix_match:
            first = mix_match.group(1).lower()
            second = mix_match.group(2).lower()
            independent = int(first) if first.isdigit() else NUMBER_WORDS.get(first)
            total = int(second) if second.isdigit() else NUMBER_WORDS.get(second)
            if independent is not None:
                board["independent_count"] = independent
                if "size" not in board and total is not None:
                    board["size"] = total
                snippet = make_snippet(text, mix_match.start(), mix_match.end())
                provenance.append(
                    {
                        "section": "board.independent_count",
                        "method": "regex",
                        "locators": ["regex: mixed-count independent directors"],
                        "page_range": None,
                        "text_snippet": snippet,
                        "confidence_pct": 75,
                    }
                )
    if "size" not in board:
        raise ValueError("Board size not found.")
    if "independent_count" not in board:
        count = 0
        for p in soup.find_all("p"):
            label = p.get_text(" ", strip=True).lower()
            if label.startswith("independent director") or label.startswith("lead independent director"):
                count += 1
        if count:
            board["independent_count"] = count
            provenance.append(
                {
                    "section": "board.independent_count",
                    "method": "html_parse",
                    "locators": ["bios: Independent Director labels"],
                    "page_range": None,
                    "text_snippet": f"Independent director labels counted: {count}",
                    "confidence_pct": 65,
                }
            )
    if "independent_count" not in board:
        raise ValueError("Independent director count not found.")
    return board, provenance


def extract_leadership(text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    leadership = {
        "ceo_is_chair": False,
        "chair_is_independent": False,
    }
    provenance: List[Dict[str, Any]] = []
    lower = text.lower()
    ceo_match = re.search(
        r"(chief executive officer).{0,120}(chair(?:man|woman)?(?: of the board)?)",
        lower,
    )
    if ceo_match:
        snippet = make_snippet(text, ceo_match.start(), ceo_match.end())
        tokens = ["separat", "executive chair", "was the", "former", "from "]
        leadership["ceo_is_chair"] = not any(token in snippet.lower() for token in tokens)
        provenance.append(
            {
                "section": "board.leadership.ceo_is_chair",
                "method": "regex",
                "locators": ["regex: CEO/Chair proximity"],
                "page_range": None,
                "text_snippet": snippet,
                "confidence_pct": 70,
            }
        )

    independent_match = re.search(
        r"independent (?:chair(?:man|woman)?|board chair)", lower
    )
    if independent_match:
        leadership["chair_is_independent"] = True
        snippet = make_snippet(text, independent_match.start(), independent_match.end())
        provenance.append(
            {
                "section": "board.leadership.chair_is_independent",
                "method": "regex",
                "locators": ["regex: independent chair"],
                "page_range": None,
                "text_snippet": snippet,
                "confidence_pct": 75,
            }
        )
    else:
        exec_match = re.search(r"executive chair(?:man|woman)?", lower)
        if exec_match:
            leadership["chair_is_independent"] = False
            snippet = make_snippet(text, exec_match.start(), exec_match.end())
            provenance.append(
                {
                    "section": "board.leadership.chair_is_independent",
                    "method": "regex",
                    "locators": ["regex: executive chair"],
                    "page_range": None,
                    "text_snippet": snippet,
                    "confidence_pct": 65,
                }
            )
    return leadership, provenance


def parse_currency(value: str) -> Optional[float]:
    if not value:
        return None
    cleaned = CURRENCY_CLEAN_RE.sub("", value)
    cleaned = cleaned.replace("\u2014", "").strip()
    if not cleaned:
        return None
    if cleaned.lower() in {"n/a", "na"}:
        return None
    if cleaned in {"--", "-"}:
        return 0.0
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()")
    try:
        number = float(cleaned)
        return -number if negative else number
    except ValueError:
        return None


def split_name_and_role(text: str) -> Tuple[str, str]:
    text = " ".join(text.split())
    if not text:
        return "", ""
    match = re.search(
        r"(President|Chief|Executive|Chair|Vice|Treasurer|Secretary|Officer)", text
    )
    if match:
        idx = match.start()
        name = text[:idx].strip(", ")
        role = text[idx:].strip()
        return (name or text, role)
    parts = text.split(",", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return text, ""


def extract_ceo_comp(soup: BeautifulSoup) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    heading_node = None
    for node in soup.find_all(string=True):
        if not isinstance(node, str):
            continue
        text = node.strip()
        if text and "summary compensation table" in text.lower():
            if heading_node is None or len(text) < len(heading_node.strip()):
                heading_node = node
    if heading_node is None:
        raise ValueError("Summary Compensation Table heading not found.")
    table = heading_node.parent.find_next("table")
    if table is None:
        raise ValueError("Summary Compensation Table not found.")
    rows = table.find_all("tr")
    first_data = None
    for row in rows:
        cells = row.find_all("td")
        if not cells:
            continue
        texts = [c.get_text(" ", strip=True) for c in cells]
        if not texts[0]:
            continue
        first_cell_norm = texts[0].lower().replace(' ', ' ')
        if 'name and principal position' in first_cell_norm:
            continue
        if len(texts) < 3:
            continue
        first_data = texts
        break
    if first_data is None:
        raise ValueError("Unable to locate first NEO row.")

    name_raw = first_data[0]
    name, role = split_name_and_role(name_raw)
    total = None
    for cell in reversed(first_data):
        num = parse_currency(cell)
        if num is not None:
            total = num
            break
    neo = {
        "name": name or name_raw,
        "role": role or "CEO",
        "total_comp_usd": total,
        "pay_mix_pct": None,
    }
    provenance = {
        "section": "compensation.neos[0]",
        "method": "html_parse",
        "locators": ["heading: Summary Compensation Table", "table:first_row"],
        "page_range": None,
        "text_snippet": " | ".join(first_data[: min(4, len(first_data))]),
        "confidence_pct": 95,
    }
    return neo, provenance


def extract_say_on_pay(text: str) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
    match = SAY_ON_PAY_REGEX.search(text)
    if not match:
        return None, None
    pct = float(match.group(1))
    snippet = make_snippet(text, match.start(), match.end())
    provenance = {
        "section": "compensation.say_on_pay_pct",
        "method": "regex",
        "locators": ["regex: say-on-pay support"],
        "page_range": None,
        "text_snippet": snippet,
        "confidence_pct": 85,
    }
    return pct, provenance


def extract_auditor_and_fees(
    soup: BeautifulSoup, text: str
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    lower = text.lower()
    auditor_name = None
    auditor_snippet = None
    for keyword in AUDITOR_KEYWORDS:
        idx = lower.find(keyword)
        if idx != -1:
            start = max(0, idx - 80)
            end = min(len(text), idx + len(keyword) + 80)
            snippet = text[start:end].strip()
            match = re.search(
                r"([A-Z][A-Za-z&\. ]{1,60}?(?:LLP|LLC|LP|P\.C\.|PC|LLP\.))",
                snippet,
            )
            if match:
                auditor_name = match.group(1).strip(" ,.")
            else:
                auditor_name = keyword.upper()
                if auditor_name == "PWC":
                    auditor_name = "PwC"
                elif auditor_name == "EY":
                    auditor_name = "Ernst & Young LLP"
            auditor_snippet = snippet
            break
    if auditor_name is None:
        raise ValueError("Auditor name not identified.")

    table = None
    cell = soup.find(string=re.compile(r"Audit Fees", re.IGNORECASE))
    if cell:
        table = cell.find_parent("table")
        if table is None and cell.parent:
            table = cell.parent.find_next("table")
    if table is None:
        heading = soup.find(string=re.compile(r"Principal (?:Accountant|Accounting) Fees", re.IGNORECASE))
        if heading:
            parent = heading.parent if hasattr(heading, "parent") else None
            if parent is not None:
                table = parent.find_next("table")
    if table is None:
        raise ValueError("Auditor fee table not found.")

    fees: Dict[str, Optional[float]] = {
        "audit": None,
        "audit_related": None,
        "tax": None,
        "all_other": None,
    }
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        label = re.sub(r"\s+", " ", cells[0].get_text(" ", strip=True).lower())
        values = []
        for cell in cells[1:]:
            text_val = cell.get_text(" ", strip=True)
            num = parse_currency(text_val)
            if num is not None:
                values.append(num)
        if not values:
            continue
        value = values[0]
        if "audit-related" in label or "audit related" in label:
            fees["audit_related"] = value
        elif "tax fees" in label:
            fees["tax"] = value
        elif "all other" in label:
            fees["all_other"] = value
        elif "audit fees" in label:
            fees["audit"] = value
    if fees["audit"] is None:
        raise ValueError("Audit fee amount missing.")

    total = sum((fees["audit"] or 0.0, fees["audit_related"] or 0.0, fees["tax"] or 0.0, fees["all_other"] or 0.0))
    non_audit = (fees["audit_related"] or 0.0) + (fees["tax"] or 0.0) + (fees["all_other"] or 0.0)
    non_audit_pct = round(non_audit / total * 100, 2) if total else None

    audit_info = {
        "auditor": auditor_name,
        "fees": {
            "audit": fees["audit"],
            "audit_related": fees["audit_related"],
            "tax": fees["tax"],
            "all_other": fees["all_other"],
            "non_audit_pct": non_audit_pct,
        },
    }
    provenance = [
        {
            "section": "audit.auditor",
            "method": "regex",
            "locators": ["regex: auditor keyword"],
            "page_range": None,
            "text_snippet": auditor_snippet,
            "confidence_pct": 90,
        },
        {
            "section": "audit.fees",
            "method": "html_parse",
            "locators": ["table: audit fees"],
            "page_range": None,
            "text_snippet": " ".join(
                filter(
                    None,
                    [
                        f"Audit {fees['audit']}",
                        f"Audit-Related {fees['audit_related']}",
                        f"Tax {fees['tax']}",
                        f"All Other {fees['all_other']}",
                    ],
                )
            ),
            "confidence_pct": 90,
        },
    ]
    return audit_info, provenance


def apply_provenance_urls(
    provenance_entries: List[Dict[str, Any]], manifest_entry: Dict[str, Any]
) -> None:
    source_url = manifest_entry.get("def14a_url")
    sha256 = manifest_entry.get("sha256")
    for entry in provenance_entries:
        entry["source_url"] = source_url
        entry["sha256"] = sha256


def validate_record(record: Dict[str, Any], schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(record))
    if errors:
        lines = ["Schema validation errors:"]
        for err in errors:
            lines.append(f"- {'/'.join(str(x) for x in err.path)}: {err.message}")
        raise ValueError("\n".join(lines))


def enforce_business_rules(record: Dict[str, Any]) -> None:
    board = record.get("board", {})
    size = board.get("size")
    independent = board.get("independent_count")
    if size and independent is not None and size > 0:
        ratio = independent / size
        if ratio < 0.5:
            raise ValueError(
                f"Business rule failed: independent_count/size = {ratio:.2f} (< 0.5)"
            )
    say = record.get("compensation", {}).get("say_on_pay_pct")
    if say is not None and say < 50:
        raise ValueError(
            f"Business rule failed: say_on_pay_pct = {say:.2f} (< 50)"
        )


def main() -> int:
    args = parse_args()
    html_path = resolve_html_path(args.html)
    run_dir = html_path.parent
    manifest = load_manifest(run_dir)
    ticker = args.ticker.upper()
    manifest_entry = (manifest.get("http_provenance") or {}).get(ticker)
    if manifest_entry is None:
        raise ValueError(f"Ticker {ticker} missing from manifest http_provenance.")

    soup = load_soup(html_path)
    text = soup.get_text(" ", strip=True)

    company = build_company_info(soup, ticker, manifest_entry)
    filing = build_filing_info(manifest_entry, company)
    board, board_prov = extract_board_info(soup, text)
    leadership, leadership_prov = extract_leadership(text)
    neo, neo_prov = extract_ceo_comp(soup)
    say_on_pay, sop_prov = extract_say_on_pay(text)
    audit_info, audit_prov = extract_auditor_and_fees(soup, text)

    record = {
        "version": "1.0.0",
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "company": company,
        "filing": filing,
        "board": {**board, "leadership": leadership},
        "ownership": {
            "top5_pct": 0.0,
            "insider_pct": 0.0,
            "policies": {},
            "top_holders": [],
        },
        "compensation": {
            "pay_mix_pct": {},
            "neos": [neo],
            "annual_incentive": {"metrics": [], "payout_ratio_pct": None},
            "ltip": {"metrics": [], "vehicles": []},
            "pvp": {"table": []},
            "say_on_pay_pct": say_on_pay,
        },
        "equity_plan": {
            "overhang_pct": None,
            "burn_rate_pct": None,
            "plan_name": None,
            "shares_available": None,
            "shares_outstanding_awards": None,
        },
        "audit": audit_info,
        "peer_group": {"members": []},
        "severance_cic": {},
        "proposals": [],
        "related_party": [],
        "policies": {},
        "metrics_derived": {},
        "footnotes": [],
        "provenance": [],
    }

    provenance_entries: List[Dict[str, Any]] = []
    provenance_entries.extend(board_prov)
    provenance_entries.extend(leadership_prov)
    provenance_entries.append(neo_prov)
    if sop_prov:
        provenance_entries.append(sop_prov)
    provenance_entries.extend(audit_prov)
    apply_provenance_urls(provenance_entries, manifest_entry)
    record["provenance"] = provenance_entries

    validate_record(record, Path(args.schema))
    enforce_business_rules(record)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")
    print(
        f"Board size={board['size']} independent={board['independent_count']} | "
        f"CEO={neo['name']} total_comp={neo['total_comp_usd']} | "
        f"Say-on-pay={say_on_pay} | Auditor={audit_info['auditor']}"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
