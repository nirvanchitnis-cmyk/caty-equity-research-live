"""Beneficial ownership extraction."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

import pandas as pd

from ..models import (
    DocumentProfile,
    FactCandidate,
    SectionSpan,
    TableExtractionResult,
)
from .base import BaseFactExtractor
from .helpers import build_table_result_from_frame, iter_document_tables


class BeneficialOwnershipExtractor(BaseFactExtractor):
    fact_ids = ["beneficial_owners_over5pct"]

    def extract(
        self,
        section_spans: Iterable[SectionSpan],
        tables: Iterable[TableExtractionResult],
        documents: Iterable[DocumentProfile],
        registry: Mapping[str, object],
    ) -> Dict[str, FactCandidate]:
        section_index = {span.section_id: span for span in section_spans}
        target_span = section_index.get("beneficial_ownership")
        if not target_span:
            return {}

        documents_list = list(documents)
        tables_list = list(tables)
        located = self._locate_ownership_table(tables_list, target_span, documents_list)
        if not located:
            return {}
        table, owners = located
        filtered = [record for record in owners if record.get('percent') is not None and record['percent'] >= 5.0]
        if not filtered:
            return {}

        return {
            'beneficial_owners_over5pct': FactCandidate(
                fact_id='beneficial_owners_over5pct',
                value=filtered,
                value_type='table',
                unit=None,
                anchors=[target_span],
                extraction_path={
                    'table_id': table.table_id,
                    'source_url': table.source_url,
                    'sha256': table.sha256,
                    'snapshot_path': str(table.raw_snapshot_path),
                },
                method='table',
                confidence_components={
                    'source': 0.85,
                    'parser': 0.9,
                    'header': 0.85,
                    'validation': 0.95,
                    'provenance': 0.9,
                },
            )
        }

    def _locate_ownership_table(
        self,
        tables: Sequence[TableExtractionResult],
        span: SectionSpan,
        documents: Sequence[DocumentProfile],
    ) -> Optional[tuple[TableExtractionResult, List[Dict[str, object]]]]:
        section_tables = [table for table in tables if table.section_id == span.section_id]
        for table in section_tables:
            owners = self._extract_owners_from_frame(table.dataframe)
            if owners:
                return table, owners
        for document in documents:
            for idx, frame in iter_document_tables(document, max_tables=250):
                owners = self._extract_owners_from_frame(frame)
                if owners:
                    table = build_table_result_from_frame(
                        span.section_id,
                        frame,
                        document,
                        label=f'ownership_{idx}',
                        source_method='fallback_html',
                        quality_score=0.8,
                    )
                    return table, owners
        return None

    def _is_ownership_table(self, frame: pd.DataFrame) -> bool:
        if frame.empty:
            return False
        first_row = " ".join(str(value).lower() for value in frame.iloc[0].tolist())
        if "beneficial owner" in first_row or "beneficial ownership" in first_row:
            return True
        flattened = " ".join(str(value).lower() for value in frame.to_numpy().flatten())
        return "% of" in flattened or "percent" in flattened

    def _extract_owners_from_frame(self, frame: pd.DataFrame) -> List[Dict[str, object]]:
        working = frame.fillna("").astype(str)
        header_row = working.iloc[0].tolist()
        column_map = self._map_columns(header_row)
        owners: List[Dict[str, object]] = []
        for row in working.iloc[1:].itertuples(index=False, name=None):
            name_cell = self._clean_text(self._get_cell(row, column_map.get('name')))
            shares_cell = self._clean_text(self._get_cell(row, column_map.get('shares')))
            percent_cell = self._clean_text(self._get_cell(row, column_map.get('percent')))
            if not name_cell or not shares_cell:
                continue
            shares = self._parse_int(shares_cell)
            percent = self._parse_percent(percent_cell)
            if shares is None or percent is None:
                continue
            owners.append({
                'name': self._normalize_name(name_cell),
                'shares': shares,
                'percent': percent,
            })
        return owners

    def _map_columns(self, headers: Sequence[str]) -> Dict[str, int]:
        mapping = {"name": 0, "shares": 2, "percent": 4}
        for idx, header in enumerate(headers):
            lowered = header.lower()
            if "beneficial owner" in lowered or "name" in lowered:
                mapping["name"] = idx
            elif "amount" in lowered or "nature" in lowered or "ownership" in lowered:
                mapping["shares"] = idx
            elif "percent" in lowered or "%" in lowered:
                mapping["percent"] = idx
        return mapping

    @staticmethod
    def _clean_text(value: str) -> str:
        return value.replace(" ", " ").strip()

    @staticmethod
    def _normalize_name(value: str) -> str:
        cleaned = re.sub(r"\s+", " ", value).strip()
        return cleaned

    @staticmethod
    def _parse_int(value: str) -> Optional[int]:
        cleaned = re.sub(r"\s*\d+/.*$", "", value)
        cleaned = re.sub(r"[^0-9]", "", cleaned)
        if not cleaned:
            return None
        try:
            return int(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _get_cell(row: Sequence[str], index: Optional[int]) -> str:
        if index is None:
            return ""
        if index >= len(row):
            return ""
        return row[index]

    @staticmethod
    def _parse_percent(value: str) -> Optional[float]:
        cleaned = value.replace('%', '').strip()
        cleaned = re.sub(r"\s*\d+/.*$", "", cleaned)
        cleaned = cleaned.replace(',', '')
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
