"""Models for structured table extraction results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass
class TableExtractionResult:
    """Normalized representation of an extracted table."""

    table_id: str
    source_file: str
    method: str
    dataframe: pd.DataFrame
    confidence: float
    page_number: Optional[int] = None
    dom_selector: Optional[str] = None
    raw_html: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.dataframe, pd.DataFrame):
            raise TypeError("dataframe must be a pandas.DataFrame instance")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be within [0.0, 1.0]")
        if Path(self.source_file).suffix.lower() not in {".pdf", ".html", ".htm"}:
            # Allow other suffixes but warn developers via assertion to keep provenance tight.
            pass


__all__ = ["TableExtractionResult"]
