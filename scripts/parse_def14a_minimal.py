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

from bs4 import BeautifulSoup, NavigableString, XMLParsedAsHTMLWarning  # type: ignore
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

AUDIT_FEES_HEADINGS = re.compile(
    r"(principal accountant fees|audit(?: and)?(?:[^a-zA-Z]|&)*non-?audit fees|audit fees|independent registered public accounting firm fees|fees billed)",
    re.IGNORECASE,
)

PAY_RATIO_HEADINGS = re.compile(r"pay\s+ratio", re.IGNORECASE)
PAY_RATIO_REGEXES: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r"(\d[\d,\.]*)\s*:\s*1", re.IGNORECASE), "regex: (\\d+):1"),
    (re.compile(r"1\s*:\s*(\d[\d,\.]*)", re.IGNORECASE), "regex: 1:(\\d+)"),
    (re.compile(r"(\d[\d,\.]*)\s*(?:to|–|-|—)\s*1", re.IGNORECASE), "regex: (\\d+) to 1"),
    (re.compile(r"1\s*(?:to|–|-|—)\s*(\d[\d,\.]*)", re.IGNORECASE), "regex: 1 to (\\d+)"),
    (re.compile(r"(\d[\d,\.]*)\s+(?:times|x)\b", re.IGNORECASE), "regex: (\\d+) times"),
]
SAY_ON_PAY_HEADINGS = re.compile(
    r"(say-?on-?pay|advisory vote on executive compensation|executive compensation advisory vote)",
    re.IGNORECASE,
)
SAY_ON_PAY_REGEXES: List[Tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"(\d{1,3}(?:\.\d+)?)%\s+(?:of\s+)?(?:the\s+)?(?:[A-Za-z]+\s+){0,2}(?:votes?|vote|shares|ballots|votes cast|vote cast|shares present).{0,120}?(?:for|in favor|support|supported|approval|approved)",
            re.IGNORECASE,
        ),
        "regex: (\\d+)% ... votes/shares ... for",
    ),
    (
        re.compile(
            r"(?:received|garnered|with|approximately)\s+(\d{1,3}(?:\.\d+)?)%\s+(?:support|approval)",
            re.IGNORECASE,
        ),
        "regex: received (\\d+)% support",
    ),
    (
        re.compile(
            r"(\d{1,3}(?:\.\d+)?)%\s+(?:approval|support)",
            re.IGNORECASE,
        ),
        "regex: (\\d+)% approval/support",
    ),
    (
        re.compile(
            r"(?:support|approval)\s+of\s+(?:approximately\s+)?(\d{1,3}(?:\.\d+)?)%",
            re.IGNORECASE,
        ),
        "regex: support of (\\d+)% ",
    ),
    (
        re.compile(
            r"favorable\s+vote\s+from\s+(?:approximately\s+)?(\d{1,3}(?:\.\d+)?)%\s+(?:of\s+)?(?:the\s+)?(?:[A-Za-z]+\s+){0,2}(?:votes?|vote|shares|ballots|votes cast|vote cast|shares present)",
            re.IGNORECASE,
        ),
        "regex: favorable vote from (\\d+)% of shares/votes",
    ),
]
INDEPENDENT_COUNT_REGEXES: List[Tuple[re.Pattern[str], str, int]] = [
    (
        re.compile(
            r"(?P<count>[A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)*)\s+independent\s+directors?",
            re.IGNORECASE,
        ),
        "regex: {count} independent directors",
        95,
    ),
    (
        re.compile(
            r"following\s+(?P<count>[A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)*)\s+of\s+(?:its|our)\s+current\s+(?P<total>[A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)*)\s+(?:members|directors|nominees)[^.]{0,160}?\bare\b[^.]{0,40}?\bindependent",
            re.IGNORECASE,
        ),
        "regex: following {count} of current members are independent",
        95,
    ),
    (
        re.compile(
            r"(?P<count>[A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)*)\s+of\s+(?:our|the)\s+(?:board|directors|nominees)[^.]{0,80}?\b(?:are|is|were|will be)\b[^.]{0,40}?\bindependent",
            re.IGNORECASE,
        ),
        "regex: {count} of our directors ... independent",
        90,
    ),
    (
        re.compile(
            r"(?P<count>[A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)*)\s+independent\s+members?\s+of\s+the\s+board",
            re.IGNORECASE,
        ),
        "regex: {count} independent members of the board",
        90,
    ),
    (
        re.compile(
            r"(?P<count>[A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)*)\s+independent\s+nominees?",
            re.IGNORECASE,
        ),
        "regex: {count} independent nominees",
        85,
    ),
]
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

SMALL_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
TENS_NUMBER_WORDS = {
    "twenty": 20,
    "thirty": 30,
}


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


def _collect_section_text(tag: Any, max_chars: int = 4000) -> str:
    pieces: List[str] = []
    initial = tag.get_text(" ", strip=True)
    if initial:
        pieces.append(initial)
    consumed = sum(len(part) for part in pieces)
    for sibling in tag.next_siblings:
        if consumed >= max_chars:
            break
        if isinstance(sibling, NavigableString):
            text_value = str(sibling).strip()
            if not text_value:
                continue
            pieces.append(text_value)
            consumed += len(text_value)
            continue
        name = getattr(sibling, "name", "")
        if name and name.lower() in HEADING_TAGS:
            break
        text_value = sibling.get_text(" ", strip=True)
        if text_value:
            pieces.append(text_value)
            consumed += len(text_value)
    return " ".join(pieces)


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


def _parse_numeric_token(raw: str) -> Optional[int]:
    if not raw:
        return None
    digit_match = re.search(r"\d+", raw)
    if digit_match:
        return int(digit_match.group(0))
    cleaned = re.sub(r"[^a-zA-Z\\s-]", " ", raw.lower())
    cleaned = cleaned.replace("-", " ")
    parts = [part for part in cleaned.split() if part and part != "and"]
    if not parts:
        return None
    total = 0
    for part in parts:
        if part in SMALL_NUMBER_WORDS:
            total += SMALL_NUMBER_WORDS[part]
        elif part in TENS_NUMBER_WORDS:
            total += TENS_NUMBER_WORDS[part]
        else:
            return None
    if total == 0 and parts[0] != "zero":
        return None
    return total


def extract_independent_director_count(
    text: str,
    soup: BeautifulSoup,
    board_size: int,
) -> Tuple[int, int, str, List[str], str]:
    search_text = text.replace("“", '"').replace("”", '"').replace("\u00a0", " ")
    for pattern, locator, confidence in INDEPENDENT_COUNT_REGEXES:
        match = pattern.search(search_text)
        if not match:
            continue
        raw_value = match.group("count")
        count = _parse_numeric_token(raw_value)
        if count is None:
            continue
        if board_size and count > board_size:
            count = board_size
        snippet = make_snippet(text, match.start(), match.end())
        locator_formatted = locator.format(count=raw_value.strip())
        return count, confidence, "regex", [locator_formatted], snippet

    hits: List[str] = []
    seen_norm: set[str] = set()
    for tag in soup.find_all(["p", "li", "td"]):
        tag_text = tag.get_text(" ", strip=True)
        if not tag_text:
            continue
        if "independent director" not in tag_text.lower():
            continue
        norm = re.sub(r"\s+", " ", tag_text.lower())
        if norm in seen_norm:
            continue
        seen_norm.add(norm)
        hits.append(tag_text)
    count = len(hits)
    if count > 0:
        if board_size and count > board_size:
            count = board_size
        has_numeric = any(re.search(r"\d", entry) for entry in hits)
        if board_size and (
            (board_size >= 4 and count < max(board_size // 2, 1))
            or not has_numeric
        ):
            assumed = max(board_size - 2, 0)
            snippet = (
                f"Independent markers detected ({count}) lacked explicit counts; assuming {assumed} independent directors from board size {board_size}."
            )
            return assumed, 65, "html_parse", ["assumption: board.size - 2 (insufficient explicit indicators)"], snippet
        snippet = hits[0][:500]
        return count, 80, "html_parse", ["count: Independent Director mentions"], snippet

    assumed = max(board_size - 2, 0) if board_size else 0
    snippet = (
        f"Assumed independent directors = board size ({board_size}) - 2 (management members)."
        if board_size
        else "Assumed independent directors due to missing disclosure."
    )
    return assumed, 70, "html_parse", ["assumption: board.size - 2"], snippet


def extract_ceo_name(soup: BeautifulSoup) -> Tuple[str, int, str, List[str], str]:
    summary_table = None
    for table in soup.find_all("table"):
        header_rows = table.find_all("tr", limit=8)
        header_text_raw = " ".join(
            cell.get_text(" ", strip=True)
            for row in header_rows
            for cell in row.find_all(["td", "th"])
        )
        header_text = re.sub(r"\s+", " ", header_text_raw.replace(" ", " ")).lower()
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




def _normalize_fee_label(label: str) -> str:
    cleaned = re.sub(r"\s+", " ", label).strip().lower()
    cleaned = re.sub(r"\(\d+\)", "", cleaned)
    cleaned = cleaned.replace("/", " ")
    cleaned = cleaned.replace("-", " ")
    cleaned = re.sub(r"[^a-z\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()



def _map_fee_label(normalized: str) -> Optional[str]:
    normalized = normalized.strip()
    if not normalized or "fee" not in normalized:
        return None
    if "committee" in normalized or "report" in normalized:
        return None
    if "audit and non audit" in normalized:
        return None
    if "audit related" in normalized:
        return "audit_related"
    if "audit fee" in normalized:
        return "audit"
    if "tax fee" in normalized or normalized.startswith("tax services"):
        return "tax"
    if "all other fee" in normalized or normalized.startswith("other fees") or normalized.endswith("other fees"):
        return "all_other"
    if "non audit fee" in normalized:
        return "all_other"
    return None


def _parse_currency_value(raw: str) -> Optional[int]:
    if not raw:
        return None
    value = raw.strip().replace(" ", " ")
    if not value:
        return None
    lowered = value.lower()
    if lowered in {"n/a", "na", "not applicable"}:
        return 0
    if re.fullmatch(r"[-–—]+", value):
        return 0
    value = value.replace("$", "")
    value = value.replace(",", "")
    value = value.replace(" ", "")
    value = value.replace("−", "-")
    if value.startswith("(") and value.endswith(")"):
        value = "-" + value[1:-1]
    value = re.sub(r"[^0-9.\-]", "", value)
    if not value:
        return None
    if value in {"-", "--", "---"}:
        return 0
    try:
        amount = float(value)
    except ValueError:
        return None
    digits_only = re.sub(r"[^0-9]", "", raw)
    if amount != 0 and len(digits_only) == 1 and "$" not in raw and "," not in raw and "." not in raw:
        return None
    return int(round(amount))


def _first_currency_from_cells(cells: List[Tag]) -> Optional[int]:
    for cell in cells:
        text_value = cell.get_text(" ", strip=True)
        if not text_value:
            continue
        amount = _parse_currency_value(text_value)
        if amount is None:
            continue
        return amount
    return None


def _find_following_table(heading: Tag) -> Optional[Tag]:
    for element in heading.next_elements:
        if isinstance(element, Tag):
            if element is heading:
                continue
            name = (element.name or "").lower()
            if name in HEADING_TAGS and element is not heading:
                break
            if name == "table":
                return element
    return None


def _parse_audit_fee_table(table: Tag) -> Tuple[Dict[str, int], List[str]]:
    fees: Dict[str, int] = {}
    locators: List[str] = []
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        label_raw = cells[0].get_text(" ", strip=True)
        if not label_raw:
            continue
        normalized = _normalize_fee_label(label_raw)
        key = _map_fee_label(normalized)
        if not key:
            continue
        amount = _first_currency_from_cells(cells[1:])
        if amount is None:
            continue
        fees[key] = amount
        locators.append(f"table row: {label_raw.strip()}")
    if "audit" not in fees:
        return {}, []
    for fallback_key in ("audit_related", "tax", "all_other"):
        fees.setdefault(fallback_key, 0)
    return fees, locators


def _augment_with_non_audit_pct(fees: Dict[str, int]) -> Dict[str, Any]:
    audit_total = fees.get("audit", 0) or 0
    audit_related = fees.get("audit_related", 0) or 0
    tax = fees.get("tax", 0) or 0
    all_other = fees.get("all_other", 0) or 0
    total = audit_total + audit_related + tax + all_other
    non_audit = audit_related + tax + all_other
    result: Dict[str, Any] = dict(fees)
    result["non_audit_pct"] = round((non_audit / total) * 100, 1) if total else 0.0
    return result


def extract_audit_fees(text: str, soup: BeautifulSoup) -> Tuple[Dict[str, Any], int, str, List[str], str]:
    for heading in soup.find_all(HEADING_TAGS):
        heading_text = heading.get_text(" ", strip=True)
        if not heading_text or not AUDIT_FEES_HEADINGS.search(heading_text):
            continue
        table = _find_following_table(heading)
        if table is None:
            continue
        fees, row_locators = _parse_audit_fee_table(table)
        if not fees:
            continue
        enriched = _augment_with_non_audit_pct(fees)
        snippet = table.get_text(" ", strip=True)[:500]
        locators = [f"{heading.name}: {heading_text}", *row_locators]
        return enriched, 90, "table_detect", locators, snippet

    for table in soup.find_all("table"):
        fees, row_locators = _parse_audit_fee_table(table)
        if not fees:
            continue
        enriched = _augment_with_non_audit_pct(fees)
        snippet = table.get_text(" ", strip=True)[:500]
        locators = ["table search: Audit Fees", *row_locators]
        return enriched, 90, "table_detect", locators, snippet

    raise ValueError("Audit fee table not found.")


def extract_ceo_pay_ratio(text: str, soup: BeautifulSoup) -> Tuple[int, int, str, List[str], str]:
    text_lower = text.lower()

    def parse_ratio(raw: str) -> int:
        clean = raw.replace(",", "")
        try:
            value = float(clean)
        except ValueError as exc:
            raise ValueError(f"Unable to parse CEO pay ratio value: {raw}") from exc
        return int(round(value))

    def snippet_for_match(match_text: str, start: int, end: int) -> str:
        return make_snippet(text, start, end)

    for heading in soup.find_all(HEADING_TAGS):
        heading_text = heading.get_text(" ", strip=True)
        if not heading_text or not PAY_RATIO_HEADINGS.search(heading_text):
            continue
        section_text = _collect_section_text(heading)
        if not section_text:
            continue
        section_lower = section_text.lower()
        for pattern, locator in PAY_RATIO_REGEXES:
            match = pattern.search(section_text)
            if not match:
                continue
            context_ok = "pay ratio" in section_lower or (
                "median" in section_lower
                and ("employee" in section_lower or "associates" in section_lower)
                and ("ceo" in section_lower or "chief executive" in section_lower)
            )
            if not context_ok:
                continue
            ratio = parse_ratio(match.group(1))
            match_text = match.group(0)
            locate = text_lower.find(match_text.lower())
            if locate != -1:
                snippet = snippet_for_match(match_text, locate, locate + len(match_text))
            else:
                snippet = section_text[:500]
            locators = [f"{heading.name}: {heading_text}", locator]
            return ratio, 85, "regex", locators, snippet

    for pattern, locator in PAY_RATIO_REGEXES:
        for match in pattern.finditer(text):
            context = text_lower[max(0, match.start() - 200) : min(len(text_lower), match.end() + 200)]
            if "median" in context and ("employee" in context or "associates" in context) and (
                "ceo" in context or "chief executive" in context or "pay ratio" in context or "ratio" in context
            ):
                ratio = parse_ratio(match.group(1))
                snippet = snippet_for_match(match.group(0), match.start(), match.end())
                locators = ["regex context search", locator]
                confidence = 85
                return ratio, confidence, "regex", locators, snippet

    raise ValueError("CEO pay ratio disclosure not found.")


def extract_say_on_pay_pct(text: str, soup: BeautifulSoup) -> Tuple[float, int, str, List[str], str]:
    text_lower = text.lower()

    def parse_pct(raw: str) -> float:
        clean = raw.replace(",", "")
        try:
            value = float(clean)
        except ValueError as exc:
            raise ValueError(f"Unable to parse Say-on-Pay percentage: {raw}") from exc
        return value

    for heading in soup.find_all(HEADING_TAGS):
        heading_text = heading.get_text(" ", strip=True)
        if not heading_text or not SAY_ON_PAY_HEADINGS.search(heading_text):
            continue
        section_text = _collect_section_text(heading)
        if not section_text:
            continue
        section_lower = section_text.lower()
        if "say" not in section_lower and "advisory" not in section_lower and "executive compensation" not in section_lower:
            continue
        for pattern, locator in SAY_ON_PAY_REGEXES:
            match = pattern.search(section_text)
            if not match:
                continue
            pct_value = parse_pct(match.group(1))
            match_text = match.group(0)
            locate = text_lower.find(match_text.lower())
            if locate != -1:
                snippet = make_snippet(text, locate, locate + len(match_text))
            else:
                snippet = section_text[:500]
            locators = [f"{heading.name}: {heading_text}", locator]
            return pct_value, 85, "regex", locators, snippet

    for pattern, locator in SAY_ON_PAY_REGEXES:
        for match in pattern.finditer(text):
            context_start = max(0, match.start() - 160)
            context_end = min(len(text_lower), match.end() + 160)
            context = text_lower[context_start:context_end]
            if not (
                "say-on-pay" in context
                or "say on pay" in context
                or "advisory vote on executive compensation" in context
                or "advisory vote" in context
                or "executive compensation" in context
            ):
                continue
            pct_value = parse_pct(match.group(1))
            snippet = make_snippet(text, match.start(), match.end())
            locators = ["regex context search", locator]
            return pct_value, 80, "regex", locators, snippet

    raise ValueError("Say-on-Pay voting result not found.")


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
            "ceo_pay_ratio_to_median": None,
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
        raw_text = soup.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", raw_text)

        board_size, board_conf, board_method, board_locators, board_snippet = extract_board_size(text, soup)
        independent_count, indep_conf, indep_method, indep_locators, indep_snippet = extract_independent_director_count(
            text, soup, board_size
        )
        independence_pct = round((independent_count / board_size) * 100, 1) if board_size else None
        say_on_pay_pct, say_conf, say_method, say_locators, say_snippet = extract_say_on_pay_pct(text, soup)
        ceo_name, ceo_conf, ceo_method, ceo_locators, ceo_snippet = extract_ceo_name(soup)
        ceo_pay_ratio, pay_ratio_conf, pay_ratio_method, pay_ratio_locators, pay_ratio_snippet = extract_ceo_pay_ratio(
            text, soup
        )
        auditor_name, auditor_conf, auditor_method, auditor_locators, auditor_snippet = extract_auditor(text)
        audit_fees, audit_fees_conf, audit_fees_method, audit_fees_locators, audit_fees_snippet = extract_audit_fees(text, soup)

        company_info = build_company_info(soup, args.ticker, manifest_entry)
        filing_info = build_filing_info(manifest_entry, company_info["cik"])

        payload = build_output_skeleton()
        payload["company"] = company_info
        payload["filing"] = filing_info
        payload["board"] = {
            "size": board_size,
            "independent_count": independent_count,
            "independence_pct": independence_pct,
            "leadership": {
                "chair_is_independent": False,
                "ceo_is_chair": False,
            },
        }
        payload["compensation"]["neos"] = [
            {"role": "CEO", "name": ceo_name, "total_comp_usd": None}
        ]
        payload["compensation"]["ceo_pay_ratio_to_median"] = ceo_pay_ratio
        payload["compensation"]["say_on_pay_pct"] = say_on_pay_pct
        payload["audit"]["auditor"] = auditor_name
        payload["audit"]["fees"] = audit_fees
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
                "section": "board.independent_count",
                "method": indep_method,
                "locators": indep_locators,
                "page_range": None,
                "text_snippet": indep_snippet,
                "confidence_pct": indep_conf,
                "source_url": manifest_entry.get("def14a_url"),
                "sha256": manifest_entry.get("sha256"),
            },
            {
                "section": "board.independence_pct",
                "method": indep_method,
                "locators": ["derived from board.independent_count / board.size"],
                "page_range": None,
                "text_snippet": f"independent_count={independent_count}, board_size={board_size}, independence_pct={independence_pct}",
                "confidence_pct": indep_conf if independence_pct is not None else 0,
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
                "section": "compensation.say_on_pay_pct",
                "method": say_method,
                "locators": say_locators,
                "page_range": None,
                "text_snippet": say_snippet,
                "confidence_pct": say_conf,
                "source_url": manifest_entry.get("def14a_url"),
                "sha256": manifest_entry.get("sha256"),
            },
            {
                "section": "compensation.ceo_pay_ratio_to_median",
                "method": pay_ratio_method,
                "locators": pay_ratio_locators,
                "page_range": None,
                "text_snippet": pay_ratio_snippet,
                "confidence_pct": pay_ratio_conf,
                "source_url": manifest_entry.get("def14a_url"),
                "sha256": manifest_entry.get("sha256"),
            },
            {
                "section": "audit.fees",
                "method": audit_fees_method,
                "locators": audit_fees_locators,
                "page_range": None,
                "text_snippet": audit_fees_snippet,
                "confidence_pct": audit_fees_conf,
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
