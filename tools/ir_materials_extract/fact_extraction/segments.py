"""Segment-level revenue extraction from structured tables."""

from __future__ import annotations

from typing import Dict, Sequence

from ..section_locators.models import SectionSpan
from ..table_extraction.models import TableExtractionResult
from .base import BaseFactExtractor
from .helpers import detect_unit_multiplier, find_column_fuzzy, normalize_numeric_value
from .models import FactCandidate


class SegmentFactExtractor(BaseFactExtractor):
    """Extract revenue by segment and validate totals."""

    _REVENUE_HEADERS = [
        "revenue",
        "segment revenue",
        "net revenue",
        "net sales",
    ]

    def extract(
        self,
        sections: Sequence[SectionSpan],
        tables: Sequence[TableExtractionResult],
        normalized_text: str,
        artifact_metadata: dict,
    ) -> Dict[str, FactCandidate]:
        results: Dict[str, FactCandidate] = {}

        segment_sections = [s for s in sections if s.section_id == "segment_results"]
        if not segment_sections:
            return results

        candidate_tables = self._candidate_tables(segment_sections[0], tables)
        target_table = self._select_segment_table(candidate_tables)
        if target_table is None:
            return results

        dataframe = target_table.dataframe
        metadata = {
            "source_url": artifact_metadata.get("url", ""),
            "file_sha256": artifact_metadata.get("sha256", ""),
            "doc_type": artifact_metadata.get("doc_type", ""),
            "page_numbers": [target_table.page_number]
            if target_table.page_number is not None
            else [],
            "table_id": target_table.table_id,
            "method": "table",
        }

        segment_column = dataframe.columns[0]
        revenue_column = find_column_fuzzy(
            dataframe,
            self._REVENUE_HEADERS,
            exclude={segment_column},
        )
        if revenue_column is None:
            return results

        multiplier = detect_unit_multiplier(str(revenue_column))

        segment_values: list[float] = []
        total_value: float | None = None

        for _, row in dataframe.iterrows():
            segment_name = str(row[segment_column]).strip()
            if not segment_name or segment_name.lower() in {"segment", "metric"}:
                continue

            raw_value = row[revenue_column]
            numeric_value = normalize_numeric_value(raw_value)
            if numeric_value is None:
                continue

            value = numeric_value * multiplier

            if "total" in segment_name.lower():
                total_value = value
                continue

            fact_id = (
                "segment_revenue_"
                + segment_name.lower().replace(" ", "_").replace("&", "and")
            )
            results[fact_id] = FactCandidate(
                fact_id=fact_id,
                value=value,
                value_type="currency",
                unit="USD",
                currency="USD",
                confidence=target_table.confidence * 0.85,
                anchor_text=f"segment={segment_name}",
                **metadata,
            )
            segment_values.append(value)

        if total_value is not None and segment_values:
            calculated_total = sum(segment_values)
            delta = abs(calculated_total - total_value)
            tolerance = max(total_value * 0.01, 1.0)
            if delta > tolerance:
                warnings = [
                    f"Segment sum {calculated_total:,.0f} != total {total_value:,.0f} (Δ={delta:,.0f})"
                ]
                confidence = target_table.confidence * 0.6
            else:
                warnings = []
                confidence = target_table.confidence * 0.9

            results["segment_revenue_total"] = FactCandidate(
                fact_id="segment_revenue_total",
                value=total_value,
                value_type="currency",
                unit="USD",
                currency="USD",
                confidence=confidence,
                validation={
                    "cross_checks": [f"sum(segments)={calculated_total:,.0f}"],
                    "warnings": warnings,
                },
                anchor_text="total-row",
                **metadata,
            )

        return results

    @staticmethod
    def _candidate_tables(
        section: SectionSpan,
        tables: Sequence[TableExtractionResult],
    ) -> list[TableExtractionResult]:
        if section.page_number is None:
            return list(tables)
        return [table for table in tables if table.page_number == section.page_number]

    @staticmethod
    def _select_segment_table(
        tables: Sequence[TableExtractionResult],
    ) -> TableExtractionResult | None:
        for table in tables:
            if table.dataframe.empty:
                continue
            first_col = str(table.dataframe.columns[0]).lower()
            if "segment" in first_col or "division" in first_col:
                return table
        return tables[0] if tables else None


__all__ = ["SegmentFactExtractor"]
