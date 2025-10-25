"""Utility helpers for IR fact extraction logic."""

from __future__ import annotations

from typing import Iterable, Optional

import pandas as pd
from rapidfuzz import fuzz


def find_column_fuzzy(
    df: pd.DataFrame,
    target_headers: list[str],
    threshold: int = 70,
    exclude: Iterable[str] | None = None,
) -> Optional[str]:
    """Return the first column whose name fuzzily matches a target header."""
    excluded = {str(col).lower() for col in (exclude or [])}
    for column in df.columns:
        column_normalized_raw = str(column)
        column_normalized = column_normalized_raw.strip().lower()
        if column_normalized in excluded:
            continue
        for target in target_headers:
            target_normalized = target.strip().lower()
            score = max(
                fuzz.ratio(column_normalized, target_normalized),
                fuzz.partial_ratio(column_normalized, target_normalized),
                fuzz.token_sort_ratio(column_normalized, target_normalized),
            )
            if score >= threshold:
                return column_normalized_raw
    return None


def normalize_numeric_value(value: object) -> Optional[float]:
    """Normalize a table cell into a float when possible."""
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    is_negative = text.startswith("(") and text.endswith(")")
    if is_negative:
        text = text[1:-1]

    cleaned = (
        text.replace(",", "")
        .replace("$", "")
        .replace("–", "-")
        .replace("—", "-")
    )

    if cleaned.lower() in {"na", "n/a", "nm", "--", "-"}:
        return None

    try:
        value_float = float(cleaned)
    except ValueError:
        return None

    return -value_float if is_negative else value_float


def detect_unit_multiplier(header_text: str) -> float:
    """Infer the numeric multiplier encoded in a column header."""
    header = header_text.lower()
    if any(token in header for token in ["billion", "$b", "\\$b"]):
        return 1_000_000_000
    if any(token in header for token in ["million", "$m", "\\$m"]):
        return 1_000_000
    if any(token in header for token in ["thousand", "$k", "\\$k"]):
        return 1_000
    return 1.0


__all__ = [
    "detect_unit_multiplier",
    "find_column_fuzzy",
    "normalize_numeric_value",
]
