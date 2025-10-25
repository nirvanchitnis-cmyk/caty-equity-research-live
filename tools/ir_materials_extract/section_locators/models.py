"""Data structures for section span identification within IR documents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SectionSpan:
    """Represents the location of a semantic section within a document."""

    section_id: str
    start_offset: int
    end_offset: int
    heading_text: str
    confidence: float
    source_file: str
    page_number: Optional[int] = None


__all__ = ["SectionSpan"]
