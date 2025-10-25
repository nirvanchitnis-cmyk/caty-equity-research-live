from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional


@dataclass
class FactCandidate:
    """Structured representation of an extracted IR fact."""

    fact_id: str
    value: Any
    value_type: str
    unit: Optional[str]
    currency: Optional[str]

    period_start: Optional[date] = None
    period_end: Optional[date] = None
    quarter: Optional[str] = None
    fiscal_year: Optional[int] = None

    source_url: str = ""
    file_sha256: str = ""
    doc_type: str = ""
    page_numbers: list[int] = field(default_factory=list)
    dom_path: Optional[str] = None
    table_id: Optional[str] = None
    slide_no: Optional[int] = None

    method: str = "regex"
    confidence: float = 0.0

    validation: dict = field(
        default_factory=lambda: {"cross_checks": [], "warnings": []}
    )

    anchor_text: Optional[str] = None
