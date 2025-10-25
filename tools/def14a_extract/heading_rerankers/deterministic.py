"""Deterministic heading scoring heuristics."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

try:  # pragma: no cover - optional dependency guard
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover
    import difflib

    class _FallbackFuzz:
        @staticmethod
        def partial_ratio(a: str, b: str) -> float:
            return difflib.SequenceMatcher(None, a, b).ratio() * 100

    fuzz = _FallbackFuzz()  # type: ignore

SECTION_SYNONYMS: Dict[str, Sequence[str]] = {
    "meeting_overview": [
        "notice of annual meeting",
        "annual meeting of shareholders",
        "proxy summary",
    ],
    "beneficial_ownership": [
        "security ownership of certain beneficial owners",
        "beneficial ownership",
        "principal shareholders",
    ],
    "executive_compensation": [
        "executive compensation",
        "summary compensation table",
        "compensation discussion and analysis",
    ],
    "audit_fees": [
        "principal accounting fees",
        "audit fees",
        "fees billed by",
    ],
    "election_of_directors": [
        "proposal one",
        "election of directors",
        "director nominees",
        "board of directors and corporate governance",
    ],
}


@dataclass
class HeadingCandidate:
    section_id: str
    heading_text: str
    score: float
    start_offset: int
    end_offset: int
    dom_path: Optional[str] = None


def score_heading(section_id: str, heading: str) -> float:
    heading_lower = heading.lower()
    best = 0.0
    synonyms = SECTION_SYNONYMS.get(section_id, [])
    for synonym in synonyms:
        token_score = fuzz.partial_ratio(heading_lower, synonym)
        best = max(best, token_score / 100.0)
    if re.search(section_id.replace("_", " "), heading_lower):
        best = max(best, 0.6)
    return best


def find_heading_candidates(
    section_id: str,
    headings: Iterable[tuple[str, int, int, Optional[str]]],
) -> List[HeadingCandidate]:
    candidates: List[HeadingCandidate] = []
    for heading_text, start, end, dom_path in headings:
        score = score_heading(section_id, heading_text)
        if score >= 0.5:
            candidates.append(
                HeadingCandidate(
                    section_id=section_id,
                    heading_text=heading_text,
                    score=score,
                    start_offset=start,
                    end_offset=end,
                    dom_path=dom_path,
                )
            )
    return sorted(candidates, key=lambda c: c.score, reverse=True)
