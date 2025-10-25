"""PDF table extraction utilities leveraging Camelot and Tabula."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd

from .models import TableExtractionResult

logger = logging.getLogger(__name__)

try:  # pragma: no cover - dependency may be absent in some environments
    import camelot  # type: ignore
except ImportError:  # pragma: no cover - handled via graceful degradation
    camelot = None  # type: ignore

try:  # pragma: no cover
    import tabula  # type: ignore
except ImportError:  # pragma: no cover
    tabula = None  # type: ignore


def extract_pdf_tables(pdf_path: Path, flavor: str = "lattice") -> List[TableExtractionResult]:
    """Extract tables from a PDF with optional Camelot/Tabula fallbacks."""

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF path not found: {pdf_path}")

    results: List[TableExtractionResult] = []

    camelot_flavors: List[str] = [flavor]
    if flavor == "lattice":
        camelot_flavors.append("stream")

    if camelot is not None:
        for camelot_flavor in camelot_flavors:
            try:
                tables = camelot.read_pdf(
                    str(pdf_path),
                    pages="all",
                    flavor=camelot_flavor,
                    strip_text="\n",
                )
            except Exception as exc:  # pragma: no cover - Camelot-specific errors
                logger.debug("Camelot %s extraction failed: %s", camelot_flavor, exc)
                continue

            for index, table in enumerate(tables):
                df = table.df if hasattr(table, "df") else pd.DataFrame(table)
                df = _cleanup_dataframe(df)
                confidence = _compute_confidence(df)
                page_number = _safe_int(getattr(table, "page", None))
                table_id = _hash_table(
                    pdf_path,
                    method=f"camelot_{camelot_flavor}",
                    index=index,
                    dataframe=df,
                )
                results.append(
                    TableExtractionResult(
                        table_id=table_id,
                        source_file=str(pdf_path),
                        method=f"camelot_{camelot_flavor}",
                        dataframe=df,
                        confidence=confidence,
                        page_number=page_number,
                    )
                )

            if results:
                return results

    if tabula is not None:
        try:
            tabula_tables = tabula.read_pdf(
                str(pdf_path),
                pages="all",
                multiple_tables=True,
                pandas_options={"dtype": str},
            )
        except Exception as exc:  # pragma: no cover - Java/Tabula errors
            logger.debug("Tabula extraction failed: %s", exc)
            tabula_tables = []

        for index, df in enumerate(tabula_tables or []):
            df = _cleanup_dataframe(df)
            confidence = _compute_confidence(df)
            table_id = _hash_table(
                pdf_path,
                method="tabula_stream",
                index=index,
                dataframe=df,
            )
            results.append(
                TableExtractionResult(
                    table_id=table_id,
                    source_file=str(pdf_path),
                    method="tabula_stream",
                    dataframe=df,
                    confidence=confidence,
                )
            )

    return results


def _cleanup_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dataframe by stripping whitespace and replacing NaNs."""
    cleaned = df.copy()
    cleaned = cleaned.fillna("")
    cleaned = cleaned.apply(
        lambda col: col.map(lambda value: value.strip() if isinstance(value, str) else value)
    )
    return cleaned


def _compute_confidence(df: pd.DataFrame) -> float:
    """Calculate confidence using coverage and whitespace metrics."""
    rows, cols = df.shape
    if rows == 0 or cols == 0:
        return 0.0

    total_cells = rows * cols
    normalized = df.astype(str).apply(
        lambda col: col.map(lambda value: value.strip())
    )
    non_empty_cells = (normalized != "").to_numpy().sum()
    empty_cells = total_cells - non_empty_cells

    fill_ratio = non_empty_cells / total_cells if total_cells else 0.0
    whitespace_penalty = max(0.3, 1 - (empty_cells / total_cells) if total_cells else 0.0)

    confidence = max(0.0, min(1.0, fill_ratio * whitespace_penalty))
    return confidence


def _hash_table(pdf_path: Path, method: str, index: int, dataframe: pd.DataFrame) -> str:
    csv_payload = dataframe.to_csv(index=False, header=True)
    digest = hashlib.sha1(csv_payload.encode("utf-8")).hexdigest()
    return f"{pdf_path.name}:{method}:{index}:{digest}"


def _safe_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


__all__ = ["extract_pdf_tables"]
