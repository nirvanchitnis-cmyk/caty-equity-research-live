"""HTML table extraction helpers built on pandas + BeautifulSoup."""

from __future__ import annotations

import hashlib
from io import StringIO
from pathlib import Path
from typing import List

import pandas as pd
from bs4 import BeautifulSoup

from .models import TableExtractionResult


def extract_html_tables(html_path: Path) -> List[TableExtractionResult]:
    """Extract and normalize tables from an HTML artifact."""

    if not html_path.exists():
        raise FileNotFoundError(f"HTML path not found: {html_path}")

    html_text = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html_text, "lxml")
    tables = soup.find_all("table")

    if not tables:
        return []

    df_list = pd.read_html(StringIO(html_text), flavor="lxml")

    results: List[TableExtractionResult] = []
    for idx, (table_tag, df) in enumerate(zip(tables, df_list)):
        df = df.fillna("")
        df = df.apply(
            lambda col: col.map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
        )

        dom_selector = f"table:nth-of-type({idx + 1})"
        table_id = _hash_table(html_path, idx, df)

        confidence = _compute_confidence(table_tag, df)

        results.append(
            TableExtractionResult(
                table_id=table_id,
                source_file=str(html_path),
                method="pandas_html",
                dataframe=df,
                confidence=confidence,
                dom_selector=dom_selector,
                raw_html=str(table_tag),
            )
        )

    return results


def _compute_confidence(table_tag, df: pd.DataFrame) -> float:
    rows, cols = df.shape
    if rows == 0 or cols == 0:
        return 0.0

    total_cells = rows * cols
    normalized = df.astype(str).apply(
        lambda col: col.map(lambda value: value.strip())
    )
    non_empty_cells = (normalized != "").to_numpy().sum()
    fill_ratio = non_empty_cells / total_cells

    header_quality = 0.3
    if table_tag.find("th"):
        header_quality += 0.4
    if table_tag.find("caption"):
        header_quality += 0.2
    if any("Total" in str(cell) for cell in normalized.iloc[-1]):
        header_quality += 0.05

    header_quality = min(header_quality, 1.0)
    confidence = max(0.0, min(1.0, fill_ratio * header_quality))
    return confidence


def _hash_table(html_path: Path, index: int, df: pd.DataFrame) -> str:
    csv_payload = df.to_csv(index=False, header=True)
    digest = hashlib.sha1(csv_payload.encode("utf-8")).hexdigest()
    return f"{html_path.name}:table:{index}:{digest}"


__all__ = ["extract_html_tables"]
