"""Table-driven extraction for quarterly financial results."""

from __future__ import annotations

from typing import Dict, Sequence, Tuple

from ..section_locators.models import SectionSpan
from ..table_extraction.models import TableExtractionResult
from .base import BaseFactExtractor
from .helpers import detect_unit_multiplier, find_column_fuzzy, normalize_numeric_value
from .models import FactCandidate


class ResultsFactExtractor(BaseFactExtractor):
    """Extract revenue and EPS metrics from financial highlights tables."""

    _REVENUE_HEADERS = [
        "revenue",
        "total revenue",
        "net revenue",
        "total revenues",
        "net revenues",
    ]
    _EPS_NON_GAAP_HEADERS = [
        "non-gaap eps",
        "adjusted eps",
        "eps (non-gaap)",
        "diluted eps - adjusted",
        "diluted eps (non-gaap)",
    ]
    _EPS_GAAP_HEADERS = [
        "gaap eps",
        "diluted eps",
        "eps (gaap)",
        "basic eps",
    ]

    def extract(
        self,
        sections: Sequence[SectionSpan],
        tables: Sequence[TableExtractionResult],
        normalized_text: str,
        artifact_metadata: dict,
    ) -> Dict[str, FactCandidate]:
        results: Dict[str, FactCandidate] = {}

        fin_sections = [s for s in sections if s.section_id == "financial_highlights"]
        if not fin_sections:
            return results

        section = fin_sections[0]
        candidate_tables = self._tables_in_section(section, tables)
        if not candidate_tables:
            return results

        table = candidate_tables[0]
        dataframe = table.dataframe
        if dataframe.empty:
            return results

        metadata = {
            "source_url": artifact_metadata.get("url", ""),
            "file_sha256": artifact_metadata.get("sha256", ""),
            "doc_type": artifact_metadata.get("doc_type", ""),
            "page_numbers": [table.page_number] if table.page_number is not None else [],
            "table_id": table.table_id,
            "method": "table",
        }

        used_columns: set[str] = set()

        revenue_result = self._extract_currency_metric(
            dataframe, self._REVENUE_HEADERS, "revenue_total", metadata, table.confidence * 0.9, None, used_columns
        )
        if revenue_result:
            fact, column = revenue_result
            results["revenue_total"] = fact
            used_columns.add(column)

        non_gaap_result = self._extract_currency_metric(
            dataframe,
            self._EPS_NON_GAAP_HEADERS,
            "eps_non_gaap",
            metadata,
            table.confidence * 0.9,
            1.0,
            used_columns,
        )
        if non_gaap_result:
            fact, column = non_gaap_result
            results["eps_non_gaap"] = fact
            used_columns.add(column)

        gaap_result = self._extract_currency_metric(
            dataframe,
            self._EPS_GAAP_HEADERS,
            "eps_gaap",
            metadata,
            table.confidence * 0.9,
            1.0,
            used_columns,
        )
        if gaap_result:
            fact, column = gaap_result
            results["eps_gaap"] = fact
            used_columns.add(column)

        return results

    @staticmethod
    def _tables_in_section(
        section: SectionSpan, tables: Sequence[TableExtractionResult]
    ) -> list[TableExtractionResult]:
        if section.page_number is None:
            return list(tables)
        return [table for table in tables if table.page_number == section.page_number]

    def _extract_currency_metric(
        self,
        dataframe,
        header_candidates: list[str],
        fact_id: str,
        metadata: dict,
        confidence: float,
        multiplier_override: float | None,
        exclude_columns: set[str],
    ) -> Tuple[FactCandidate, str] | None:
        column = find_column_fuzzy(
            dataframe, header_candidates, exclude=exclude_columns
        )
        if column is None:
            return None

        multiplier = (
            multiplier_override
            if multiplier_override is not None
            else detect_unit_multiplier(str(column))
        )

        if len(dataframe) == 0:
            return None

        raw_value = dataframe.iloc[0][column]
        numeric_value = normalize_numeric_value(raw_value)
        if numeric_value is None:
            return None

        value = numeric_value * multiplier
        fact = FactCandidate(
            fact_id=fact_id,
            value=value,
            value_type="currency",
            unit="USD",
            currency="USD",
            confidence=confidence,
            anchor_text=f"column={column}",
            **metadata,
        )
        return fact, str(column)


__all__ = ["ResultsFactExtractor"]
