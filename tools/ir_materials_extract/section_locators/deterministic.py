"""Heuristic section locator for IR materials using deterministic regex patterns."""

from __future__ import annotations

import re
from typing import List, Tuple

from .models import SectionSpan

SECTION_PATTERNS = {
    "guidance": [
        r"(?i)outlook\s+(for\s+)?(?:fy|q\d+|\d{4})",
        r"(?i)guidance",
        r"(?i)forward[- ]looking",
        r"(?i)(fy|q\d+)\s+\d{4}\s+outlook",      # FY 2025 Outlook
        r"(?i)\d{4}\s+outlook\s+update",         # 2025 Outlook Update
    ],
    "financial_highlights": [
        r"(?i)financial\s+highlights",
        r"(?i)q\d+\s+\d{4}\s+results",
        r"(?i)quarterly\s+results",
        r"(?i)key\s+financial\s+metrics",        # NEW
        r"(?i)financial\s+summary",              # NEW
    ],
    "segment_results": [
        r"(?i)segment\s+results",
        r"(?i)business\s+segments",
        r"(?i)revenue\s+by\s+segment",
        r"(?i)segment\s+performance",            # NEW
        r"(?i)business\s+highlights",            # NEW
    ],
    "non_gaap": [
        r"(?i)non[- ]gaap\s+reconciliation",
        r"(?i)adjusted\s+.*\s+reconciliation",
        r"(?i)gaap\s+to\s+non[- ]gaap",
        r"(?i)reconciliation\s+of\s+gaap",       # NEW
    ],
}


def locate_sections(text: str, source_file: str) -> List[SectionSpan]:
    """Identify section spans in normalized IR text."""

    if not text:
        return []

    matches: List[Tuple[int, str, str, float]] = []
    for section_id, patterns in SECTION_PATTERNS.items():
        best_match: Tuple[int, str, str, float] | None = None
        for pattern in patterns:
            for re_match in re.finditer(pattern, text, flags=re.IGNORECASE):
                heading = _heading_for_offset(text, re_match.start())
                confidence = _confidence_from_match(pattern, heading)
                candidate = (re_match.start(), section_id, heading, confidence)
                if best_match is None or candidate[0] < best_match[0]:
                    best_match = candidate
        if best_match:
            matches.append(best_match)

    if not matches:
        return []

    matches.sort(key=lambda item: item[0])
    spans: List[SectionSpan] = []
    text_length = len(text)

    for index, (start_offset, section_id, heading_text, confidence) in enumerate(matches):
        if index + 1 < len(matches):
            end_offset = matches[index + 1][0]
        else:
            end_offset = text_length

        spans.append(
            SectionSpan(
                section_id=section_id,
                start_offset=start_offset,
                end_offset=end_offset,
                heading_text=heading_text,
                confidence=min(confidence, 1.0),
                source_file=source_file,
            )
        )

    return spans


def _heading_for_offset(text: str, offset: int) -> str:
    """Extract the logical heading line around a regex match."""
    start = text.rfind("\n", 0, offset)
    start = start + 1 if start != -1 else 0
    end = text.find("\n", offset)
    end = end if end != -1 else len(text)
    heading = text[start:end].strip()
    return heading or text[offset : min(offset + 120, len(text))].strip()


def _confidence_from_match(pattern: str, heading: str) -> float:
    """Derive a confidence score based on pattern specificity and heading richness."""
    base = 0.55
    lowered = pattern.lower()
    if "non-gaap" in lowered:
        base += 0.1
    if "segment" in lowered:
        base += 0.05
    if len(heading.split()) >= 4:
        base += 0.1
    if heading.isupper():
        base += 0.05
    return min(1.0, base)


__all__ = ["locate_sections", "SECTION_PATTERNS"]
